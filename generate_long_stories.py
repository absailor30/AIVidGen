"""
generate_long_stories.py — fills the `long` lane of the Supabase story queue.

Long-form is a 10-minute, 16:9, YouTube-only video with a deliberate retention
structure (see LONG_BRIEF). It is generated in FIVE Groq calls rather than one:

  1. plan  — title, dna, keywords, publishing kit, and a brief per beat
  2-12.    — one call per narrative beat, in order

Why one call per beat: the first version asked for section-sized chunks (~718
words covering four beats) and the model overshot every single time — 881,
1177, 1103 words against a 632-804 band. Length compliance collapses as the
target grows. A single beat at 62-325 words is something a 27B model can
actually hit, a bad beat is retried on its own, and a retry that overshot is
told by how much so the next attempt corrects rather than re-rolling.

Shares the model fallback chain, theme rotation and Groq plumbing with
generate_stories_cloud.py. Run with the same env as that script:
  SUPABASE_URL, SUPABASE_SERVICE_KEY, GROQ_API_KEY
  GROQ_MODEL / GROQ_MAX_TOKENS optional.

DRY_RUN=1 prints the story and skips every Supabase write — use it to check
prompt changes without touching the queue.
"""

import json
import os
import sys
import time

from supabase import create_client

from generate_stories_cloud import (
    BEAT_ORDER,
    LOGICAL_BEATS,
    LONG_BEATS,
    LONG_MIN_KEYWORD_TERMS,
    LONG_TOTAL_MAX,
    LONG_TOTAL_MIN,
    QUEUE_TARGETS,
    THEMES,
    call_groq,
    pick_theme,
    validate_story,
)

VARIANT = "long"
TARGET_DURATION_SECONDS = 600

# One story per run. Five calls plus retries is already a few minutes against
# Groq's free-tier rate limiting; batching would spend the whole job on
# generation and leave nothing for the render.
STORIES_PER_RUN = 1
MAX_BEAT_ATTEMPTS = 4       # per beat, with corrective feedback between tries
MAX_STORY_ATTEMPTS = 2      # whole-story restarts

LONG_BRIEF = """You are the head writer for "Twisty! StoryVault", a faceless
first-person storytelling channel. Brand promise: "Every story has another
side." Your stories are emotional, grounded, realistic family/relationship
dramas that hook instantly and end with a satisfying, karmic vindication where
the narrator comes out on top.

This is a LONG-FORM YouTube video (about 10 minutes narrated), not a Short. It
is a single continuous first-person account with room to breathe: real scenes,
specific detail, dialogue rendered as reported speech, and a slow tightening of
pressure. It is NOT a Short padded out with repetition."""

STRUCTURE = """The video runs in four movements, in this exact order:

MOVEMENT 1 — the first 7 minutes, in this beat order:
  HOOK        open mid-consequence on the sharpest image in the story. No
              throat-clearing, no scene-setting preamble.
  LOCK-IN     immediately promise the specific question the video answers
              ("what I found in that drawer changed everything") and establish
              the stakes, so the viewer commits to staying.
  BODY 1      the setup: who these people are, what was normal before.
  REHOOK 1    a forward-reference that re-buys attention ("I didn't know it
              yet, but the worst part hadn't happened").
  BODY 2      the betrayal begins to surface; escalate the pressure.
  REHOOK 2    another forward-reference, sharper than the first.
  BODY 3      the confrontation or the discovery that forces the narrator's hand.
  REHOOK 3    the final tease, pointing straight at the reveal.

MOVEMENT 2 — the next 1 minute: THE TRUTH. The reveal lands. The thing the
  rehooks kept promising is delivered plainly and completely. No new mysteries.

MOVEMENT 3 — the next 1.5 minutes: THE CLOSE. Consequences and vindication.
  The narrator comes out on top in a way that feels earned, not lucky. Loose
  ends tied.

MOVEMENT 4 — the last 30 seconds: THE CTA. Step out of the story and speak to
  the viewer directly. Ask the binary question the story raises, then an
  explicit, natural call to SUBSCRIBE (the literal word "subscribe" must
  appear). Warm and direct, not desperate or salesy.

Hard rules for every section:
- First person, past tense. No quotation marks anywhere (they break the
  narration). Render speech as reported speech.
- Self-contained. Never write "part 1", "part 2" or "to be continued".
- Plain spoken English. This is read aloud by a text-to-speech voice, so avoid
  parentheses, bullet points, headings, emoji, and any markup.
- Do NOT write the beat names into the prose. The structure is invisible to
  the viewer.
- Never state a running time or refer to the video itself, except in the CTA."""

PLAN_SCHEMA = """Respond with ONLY a single JSON object (no markdown fences, no
commentary before or after), matching exactly:

{
  "theme": "...", "title": "... the story's internal title ...",
  "keywords": "... 12 to 18 COMMA-SEPARATED stock-footage search terms, each 2-4 plain words, ordered to follow the story ...",
  "dna": {"hook": "...", "relationship": "...", "conflict": "...", "emotion": "...", "payoff": "... the satisfying/karmic resolution ...", "fingerprint": "..."},
  "curve": "... describe the hook -> lock-in -> body/rehook escalation -> truth -> close arc ...",
  "variables_changed": ["...", "..."],
  "score": 88,
  "cooldown_flag": "...",
  "tracking_tag": "[[TWISTY: theme=...; hook=...; fingerprint=...; ending=...]]",
  "beats": {
    "hook": "2-3 sentences briefing what happens in this beat",
    "lock_in": "...", "body_1": "...", "rehook_1": "...",
    "body_2": "...", "rehook_2": "...", "body_3": "...", "rehook_3": "...",
    "truth": "...", "closing": "...", "cta": "..."
  },
  "publishing_kit": {
    "youtube_title": "... under 100 characters, curiosity-driven, no clickbait lies ...",
    "youtube_description": "... teaser paragraph + tracking_tag on its own line + hashtags + 'Subscribe for the next one.' ...",
    "youtube_tags": ["...", "..."]
  }
}

The "keywords" field is critical and is NOT prose: it is fed directly to a stock
footage search, split on commas. Each term must be a literal, filmable subject
that stock libraries actually have — "empty family kitchen", "rain on window",
"woman reading letter", "hospital corridor night". Never abstract nouns like
"betrayal" or "regret". Give at least 12 distinct terms; a video that reuses the
same three clips for ten minutes is a failure.

variables_changed must list at least 6 items. score must be 85 or higher.
Output valid JSON only."""

BEAT_SCHEMA = """Respond with ONLY a single JSON object (no markdown fences,
no commentary), matching exactly:

{"beat": "<BEAT_NAME>", "text": "... the prose for this beat only ..."}

Output valid JSON only."""

# Human-readable role for each beat, so the prose call knows its job without
# re-reading the whole structure brief.
BEAT_ROLE = {
    "hook": "Open mid-consequence on the sharpest image in the story. No preamble.",
    "lock_in": "Promise the specific question this video answers, and set the stakes.",
    "body_1": "The setup: who these people are and what normal looked like before.",
    "rehook_1": "A short forward-reference that re-buys attention.",
    "body_2": "The betrayal surfaces. Escalate the pressure.",
    "rehook_2": "Another forward-reference, sharper than the first.",
    "body_3": "The confrontation or discovery that forces the narrator's hand.",
    "rehook_3": "The final tease, pointing straight at the reveal.",
    "truth": "The reveal lands, plainly and completely. No new mysteries.",
    "closing": "Consequences and vindication, earned rather than lucky. Tie it off.",
    "cta": ("Step out of the story and speak to the viewer. Ask the binary "
            "question the story raises, then an explicit call to SUBSCRIBE."),
}


def _plan_prompt(theme: str, recent: list) -> tuple[str, str]:
    system = f"{LONG_BRIEF}\n\n{STRUCTURE}\n\n{PLAN_SCHEMA}"
    user = (
        f'Theme lock for this story: "{theme}".\n\n'
        f"Recent entries in this theme (avoid repeating fingerprints/hooks/curves):\n"
        f"{json.dumps(recent, ensure_ascii=False)}\n\n"
        f"Plan one new long-form story now. Plan only — do not write the prose yet."
    )
    return system, user


def _beat_prompt(plan: dict, name: str, previous_tail: str, correction: str = "") -> tuple[str, str]:
    spec = LONG_BEATS[name]
    logical = spec["brief"]
    brief = plan["beats"].get(logical, "")

    system = (
        f"{LONG_BRIEF}\n\n{STRUCTURE}\n\n"
        f"{BEAT_SCHEMA.replace('<BEAT_NAME>', name)}"
    )

    # Halves of one logical beat need distinct jobs or they restate each other.
    if spec["part"] == "first":
        part_note = (
            f"\nThis is the FIRST HALF of the '{logical}' beat. Set it up and get "
            f"it moving, but stop before its conclusion — the second half finishes it. "
            f"Do not resolve it here."
        )
    elif spec["part"] == "second":
        part_note = (
            f"\nThis is the SECOND HALF of the '{logical}' beat. The first half is "
            f"immediately above; carry it forward to its conclusion. Do not restate "
            f"what it already covered."
        )
    else:
        part_note = ""

    continuity = (
        f"The story so far ended with:\n...{previous_tail}\n\n"
        f"Continue seamlessly from there. Do not recap it.\n\n"
        if previous_tail else ""
    )
    sentences = max(2, round(spec["target"] / 18))
    user = (
        f"Story plan:\n"
        f"{json.dumps({k: v for k, v in plan.items() if k not in ('publishing_kit', 'beats')}, ensure_ascii=False)}\n\n"
        f"{continuity}"
        f"Write ONLY this piece of the story.\n"
        f"Its job: {BEAT_ROLE[logical]}{part_note}\n"
        f"Planned content for the '{logical}' beat: {brief}\n\n"
        f"LENGTH IS A HARD REQUIREMENT: about {spec['target']} words, roughly "
        f"{sentences} sentences. It must land between {spec['min']} and "
        f"{spec['max']} words. Write this piece only — later pieces cover the "
        f"rest of the story, so do not get ahead of yourself.\n"
        f"{correction}"
    )
    return system, user


def _tail(text: str, words: int = 40) -> str:
    return " ".join(text.split()[-words:])


def generate_long_story(theme: str, recent: list) -> dict:
    """One planning call, then one call per section. Raises on give-up."""
    plan = call_groq(*_plan_prompt(theme, recent))
    for key in ("beats", "keywords", "dna", "publishing_kit"):
        if key not in plan:
            raise ValueError(f"plan missing '{key}'")
    missing_briefs = [b for b in LOGICAL_BEATS if not plan["beats"].get(b)]
    if missing_briefs:
        raise ValueError(f"plan is missing beat briefs: {missing_briefs}")
    print(f"[long] Plan: {plan.get('title')} ({plan.get('theme')})")

    terms = [t.strip() for t in str(plan["keywords"]).split(",") if t.strip()]
    if len(terms) < LONG_MIN_KEYWORD_TERMS:
        raise ValueError(
            f"plan gave {len(terms)} keyword terms, need >= {LONG_MIN_KEYWORD_TERMS}"
        )

    sections: dict[str, str] = {}
    previous_tail = ""
    for name in BEAT_ORDER:
        spec = LONG_BEATS[name]
        last_error = None
        correction = ""
        for attempt in range(MAX_BEAT_ATTEMPTS):
            try:
                result = call_groq(*_beat_prompt(plan, name, previous_tail, correction))
                text = str(result.get("text", "")).strip()
                if not text:
                    raise ValueError("empty beat text")
                n = len(text.split())
                if n > spec["max"] or n < spec["min"]:
                    # Tell the model HOW it missed. A bare retry just re-rolls
                    # the same distribution — this is what fixed the original
                    # 881/1177/1103-word overshoot.
                    direction = "TOO LONG" if n > spec["max"] else "TOO SHORT"
                    delta = n - spec["target"]
                    correction = (
                        f"\nYour previous attempt was {n} words — {direction} by "
                        f"{abs(delta)} words against the {spec['target']}-word target. "
                        f"{'Cut detail and tighten sentences.' if delta > 0 else 'Add specific detail and scene.'} "
                        f"Return {spec['target']} words this time."
                    )
                    raise ValueError(f"{n} words, need {spec['min']}-{spec['max']}")
                if name == "cta" and "subscribe" not in text.lower():
                    correction = "\nYour previous attempt omitted the word 'subscribe'. It must appear."
                    raise ValueError("cta must contain an explicit 'Subscribe'")
                sections[name] = text
                previous_tail = _tail(text)
                print(f"[long]   {name}: {n} words (target {spec['target']})")
                break
            except Exception as e:
                last_error = e
                print(f"[long]   {name} attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        else:
            raise ValueError(f"beat '{name}' failed {MAX_BEAT_ATTEMPTS}x: {last_error}")

    story = {k: v for k, v in plan.items() if k != "beats"}
    story["beats"] = plan["beats"]
    story["sections"] = sections
    story["story"] = "\n\n".join(sections[n] for n in BEAT_ORDER)
    story["target_duration_seconds"] = TARGET_DURATION_SECONDS
    return story


def main():
    dry_run = os.environ.get("DRY_RUN") == "1"
    sb = None if dry_run else create_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
    )

    target = QUEUE_TARGETS[VARIANT]
    if dry_run:
        unclaimed, state_rows = 0, []
        print("[long] DRY_RUN — no Supabase reads or writes.")
    else:
        unclaimed = (
            sb.table("story_queue").select("id", count="exact")
            .is_("claimed_at", "null").eq("variant", VARIANT).execute().count
        )
        print(f"[long] Unclaimed long stories: {unclaimed}")
        if unclaimed >= target:
            print("[long] Queue healthy, nothing to do.")
            return
        state_rows = sb.table("story_state").select(
            "variant,theme,hook,fingerprint,curve"
        ).execute().data

    written = 0
    for _ in range(STORIES_PER_RUN):
        if unclaimed + written >= target:
            break
        theme = pick_theme(state_rows, variant=VARIANT) if state_rows else THEMES[0]
        recent = [
            r for r in state_rows
            if r.get("theme") == theme and (r.get("variant") or "short") == VARIANT
        ][-15:]

        for attempt in range(MAX_STORY_ATTEMPTS):
            try:
                story = generate_long_story(theme, recent)
                validate_story(story, variant=VARIANT)
            except Exception as e:
                print(f"[long] Story attempt {attempt + 1} failed: {e}")
                continue

            total = len(story["story"].split())
            print(f"[long] Story OK: {story['title']} — {total} words "
                  f"(~{total / 3.42:.0f}s narrated at 1.2x)")

            if dry_run:
                print(json.dumps(story, ensure_ascii=False, indent=2)[:4000])
            else:
                sb.table("story_queue").insert({
                    "variant": VARIANT,
                    "theme": story["theme"], "title": story["title"], "payload": story,
                }).execute()
                state_rows.append({
                    "variant": VARIANT, "theme": story["theme"],
                    "hook": story["dna"].get("hook"),
                    "fingerprint": story["dna"].get("fingerprint"),
                    "curve": story["curve"],
                })
            written += 1
            break

    print(f"[long] Done. Wrote {written} stories. Queue now ~{unclaimed + written}.")

    # An empty long queue means the next long render has nothing to post. Fail
    # loudly so the Telegram alert fires, matching the short generator.
    if not dry_run and unclaimed + written == 0:
        raise SystemExit(
            "[long] FATAL: long queue is empty and no story could be generated — "
            "nothing will be posted. See the errors above."
        )


if __name__ == "__main__":
    sys.exit(main())
