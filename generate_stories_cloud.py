"""
generate_stories_cloud.py — Fully autonomous story writer for GitHub Actions.

Uses Groq's free-tier API (llama-3.3-70b-versatile) to write new Twisty!
StoryVault stories following STORY_ENGINE_BIBLE_v4.1.md, so the pipeline
never needs a human (or Claude session) to keep the queue fed. Runs before
the render step in story_render.yml.

Required environment variables:
  SUPABASE_URL, SUPABASE_SERVICE_KEY, GROQ_API_KEY
"""

import json
import os
import re
import time
from collections import Counter

import requests
from supabase import create_client

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq retires models on a rolling basis and answers a retired name with a bare
# 404. That is indistinguishable from any other failure to the retry loop below,
# so a retirement used to silently drain the queue. We now try a list of models
# in order and remember the first that answers. Set GROQ_MODEL to pin one.
# Ordered best-first, and verified against what this key actually serves (see
# .github/workflows/groq_models.yml — the Llama line is gone from this account,
# which is what took the pipeline down). Reasoning models are last resort: they
# spend the token budget on hidden reasoning, which truncates the story JSON.
GROQ_MODELS = [m for m in [
    os.environ.get("GROQ_MODEL"),
    "qwen/qwen3.8-27b",       # clean prose, no reasoning preamble
    "openai/gpt-oss-120b",    # works, but reasoning eats the budget
    "openai/gpt-oss-20b",
    "allam-2-7b",             # small and Arabic-focused; quality fallback only
] if m]
_active_model = None

# A 260-360 word story plus its JSON envelope (dna, curve, keywords, YouTube
# title/description/tags) runs ~1200 tokens. The old 1500 left no margin, so a
# slightly long response was cut mid-string and failed to parse. Override with
# the GROQ_MAX_TOKENS repo variable if stories start getting clipped again.
MAX_TOKENS = int(os.environ.get("GROQ_MAX_TOKENS") or 4000)

# How deep to keep each variant's queue. Long stories cost ~5 Groq calls each,
# so a shallower buffer keeps a single run from spending its whole budget there.
QUEUE_TARGETS = {"short": 4, "long": 2}
QUEUE_TARGET = QUEUE_TARGETS["short"]   # back-compat for anything importing this

# Compact system prompt. We deliberately do NOT send the full 28KB story bible
# on every call — Groq's free tier is 12,000 tokens/MINUTE, and the bible alone
# is ~7K tokens, so sending it each attempt instantly trips the rate limit. The
# AUTOMATION_TAIL below is fully self-contained, so this short brief is enough.
CHANNEL_BRIEF = """You are the head writer for "Twisty! StoryVault", a faceless
first-person storytelling channel for YouTube Shorts and Instagram Reels. Brand
promise: "Every story has another side." Your stories are emotional, grounded,
realistic family/relationship dramas that hook instantly and end with a
satisfying, karmic vindication where the narrator comes out on top."""

THEMES = [
    "Family Inheritance",
    "Career Sabotage / Workplace Betrayal",
    "Marriage & Infidelity",
    "Wedding & Family Entitlement",
    "Sibling Rivalry & Favoritism",
    "In-Law Conflicts",
    "Friendship Betrayal & Glow-Up",
]

REQUIRED_KEYS = ["theme", "title", "story", "keywords", "dna", "curve",
                 "variables_changed", "score", "cooldown_flag", "tracking_tag", "publishing_kit"]
REQUIRED_DNA_KEYS = ["hook", "relationship", "conflict", "emotion", "payoff", "fingerprint"]
REQUIRED_KIT_KEYS = ["youtube_title", "youtube_description", "youtube_tags",
                      "instagram_caption", "instagram_hashtags"]
# Long-form is YouTube-only, so the Instagram fields are not required. Nothing
# downstream reads them for that variant (upload_to_youtube uses only these).
REQUIRED_KIT_KEYS_LONG = ["youtube_title", "youtube_description", "youtube_tags"]

# Per-BEAT word budgets for the long variant, derived from the narration rate:
# JennyNeural is ~2.85 words/sec at 1.0x, and long-form renders at 1.2x, so
# ~3.42 words/sec.
#
# These are per-beat rather than per-section because the first attempt at
# section-sized targets failed every time: asked for a 718-word chunk covering
# four beats, the model returned 881, 1177 and 1103 words — consistently ~45%
# over, and an identical retry just rolls the same dice. A single narrative
# beat with a ~100-325 word target is something a 27B model can actually hit.
#
# Total targets 565s (~9.4 min), deliberately under the 10-minute ceiling so
# that even a run of long-ish beats stays near it.
LONG_BEATS = {
    #            seconds  target  min   max
    "hook":     {"seconds": 28, "target":  96, "min":  67, "max": 125},
    "lock_in":  {"seconds": 28, "target":  96, "min":  67, "max": 125},
    "body_1":   {"seconds": 95, "target": 325, "min": 266, "max": 384},
    "rehook_1": {"seconds": 18, "target":  62, "min":  43, "max":  81},
    "body_2":   {"seconds": 95, "target": 325, "min": 266, "max": 384},
    "rehook_2": {"seconds": 18, "target":  62, "min":  43, "max":  81},
    "body_3":   {"seconds": 95, "target": 325, "min": 266, "max": 384},
    "rehook_3": {"seconds": 18, "target":  62, "min":  43, "max":  81},
    "truth":    {"seconds": 57, "target": 195, "min": 160, "max": 230},
    "closing":  {"seconds": 85, "target": 291, "min": 239, "max": 343},
    "cta":      {"seconds": 28, "target":  96, "min":  67, "max": 125},
}
BEAT_ORDER = list(LONG_BEATS)

# Per-beat bands alone would allow 7.4-11.4 min; this gate keeps the aggregate
# sane even when several beats land at opposite ends of their range.
LONG_TOTAL_MIN, LONG_TOTAL_MAX = 1700, 2250
LONG_MIN_KEYWORD_TERMS = 10

AUTOMATION_TAIL = """

---

ADDITIONAL AUTOMATION REQUIREMENT — THIS OVERRIDES ANY CONFLICTING GUIDANCE ABOVE.

NARRATIVE FORMAT (most important):
Write a self-contained, first-person "satisfying vindication" story with FOUR beats,
flowing as one continuous paragraph (do not label the beats):
  1. HOOK — the very first sentence drops the reader straight into a shocking,
     specific injustice that creates instant tension. E.g. "My sister announced at
     my engagement party that my wedding gown was actually hers."
  2. BUILD-UP — how it started and escalated; concrete details that make it real
     and make the reader's blood boil.
  3. TRIGGER (lowest point) — the injustice peaks: the people who should have my
     back side with the wrongdoer, and I'm left stuck, humiliated, or cornered.
  4. SATISFYING CLOSE — I come out on top through a believable turn (not luck alone),
     and the wrongdoer is left jealous / exposed / regretful. Karmic, earned, and
     fully resolved. E.g. a designer friend hears what happened and gets me a far
     better gown; my sister can't hide her envy.

HARD RULES:
- The story MUST be COMPLETE and fully resolved in this single piece. NO cliffhangers,
  NO "Part 1", "Part 2", "to be continued", or any promise of a continuation.
- Length: aim for 300-340 words (this runs ~90-120 seconds narrated). NEVER write
  fewer than 270 words — expand each of the four beats with concrete, specific,
  sensory detail rather than rushing to the ending.
- First person, one paragraph, no quotation marks around dialogue.
- End with a short spoken follow-CTA woven naturally into the closing line
  (e.g. "Follow for the next one.").
- Keep it grounded and realistic — no over-the-top or implausible twists.

Respond with ONLY a single JSON object (no markdown fences, no commentary before or
after), matching exactly:

{
  "theme": "...", "title": "...",
  "story": "... the 350-420 word first-person story described above ...",
  "keywords": "... 15-25 word stock-footage search string, plain words, no commas ...",
  "dna": {"hook": "...", "relationship": "...", "conflict": "...", "emotion": "...", "payoff": "... the satisfying/karmic resolution ...", "fingerprint": "..."},
  "curve": "... describe the hook -> build-up -> trigger -> satisfying-close arc ...",
  "variables_changed": ["...", "..."],
  "score": 88,
  "cooldown_flag": "...",
  "tracking_tag": "[[TWISTY: theme=...; hook=...; fingerprint=...; ending=...]]",
  "publishing_kit": {
    "youtube_title": "...", "youtube_description": "... teaser + tracking_tag on its own line + hashtags + 'Follow for the next one.' ...",
    "youtube_tags": ["...", "..."],
    "instagram_caption": "... ends with a binary question + 'Follow for the next one.' ...",
    "instagram_hashtags": ["...", "..."]
  }
}

variables_changed must list at least 6 items. score must be 85 or higher.
Output valid JSON only.
"""


def _check_self_contained(text: str):
    lowered = text.lower()
    for banned in ("part 1", "part 2", "part one", "part two", "to be continued"):
        if banned in lowered:
            raise ValueError(f"story must be self-contained, found '{banned}'")


def validate_story(story: dict, variant: str = "short"):
    missing = [k for k in REQUIRED_KEYS if k not in story]
    if missing:
        raise ValueError(f"Missing keys: {missing}")
    if any(k not in story["dna"] for k in REQUIRED_DNA_KEYS):
        raise ValueError("dna missing required keys")
    kit_keys = REQUIRED_KIT_KEYS_LONG if variant == "long" else REQUIRED_KIT_KEYS
    if any(k not in story["publishing_kit"] for k in kit_keys):
        raise ValueError("publishing_kit missing required keys")
    if len(story["variables_changed"]) < 6:
        raise ValueError("variables_changed needs >= 6 items")
    if story["score"] < 85:
        raise ValueError(f"score {story['score']} below 85")

    if variant == "long":
        return _validate_long(story)

    # Enforce the ~90-120s narration length (350-420 target, allow a little slack).
    word_count = len(story["story"].split())
    if not (260 <= word_count <= 360):
        raise ValueError(f"story word count {word_count} outside 260-360 range")
    _check_self_contained(story["story"])


def _validate_long(story: dict):
    """Long-form: per-beat budgets, a real keyword list, and a spoken CTA."""
    sections = story.get("sections")
    if not isinstance(sections, dict):
        raise ValueError("long story needs a 'sections' object")
    missing = [k for k in LONG_BEATS if k not in sections]
    if missing:
        raise ValueError(f"beats missing: {missing}")

    # Per-beat counts are what make a single-beat retry possible; a total that
    # happens to land in range can still hide a collapsed truth-reveal.
    for name, spec in LONG_BEATS.items():
        n = len(str(sections[name]).split())
        if not (spec["min"] <= n <= spec["max"]):
            raise ValueError(
                f"beat '{name}' is {n} words, outside {spec['min']}-{spec['max']} "
                f"(target {spec['target']} for {spec['seconds']}s)"
            )

    total = len(story["story"].split())
    if not (LONG_TOTAL_MIN <= total <= LONG_TOTAL_MAX):
        raise ValueError(
            f"story word count {total} outside {LONG_TOTAL_MIN}-{LONG_TOTAL_MAX} range"
        )

    if "subscribe" not in str(sections["cta"]).lower():
        raise ValueError("cta section must contain an explicit 'Subscribe' call-out")

    # The renderer's search terms come from splitting this on commas
    # (app/services/task.py). A space-separated string collapses to ONE term and
    # silently yields a video that loops the same few clips for ten minutes.
    terms = [t.strip() for t in str(story["keywords"]).split(",") if t.strip()]
    if len(terms) < LONG_MIN_KEYWORD_TERMS:
        raise ValueError(
            f"keywords must be >= {LONG_MIN_KEYWORD_TERMS} comma-separated terms, got {len(terms)}"
        )

    _check_self_contained(story["story"])


def _is_model_gone(resp) -> bool:
    """True when Groq rejected the request because the model name no longer exists."""
    if resp.status_code == 404:
        return True
    if resp.status_code == 400:
        return "model" in resp.text.lower() and (
            "does not exist" in resp.text.lower()
            or "decommission" in resp.text.lower()
            or "not found" in resp.text.lower()
        )
    return False


def call_groq(system: str, user: str) -> dict:
    global _active_model

    # Prefer the model already known to work this run, then fall through the rest.
    candidates = ([_active_model] if _active_model else []) + [
        m for m in GROQ_MODELS if m != _active_model
    ]
    resp = None
    for model in candidates:
        # Retry on 429 (rate limit), honoring the reset window the API reports.
        for attempt in range(4):
            resp = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "temperature": 0.9,
                    "max_tokens": MAX_TOKENS,
                },
                timeout=60,
            )
            if resp.status_code == 429 and attempt < 3:
                wait = _parse_retry_seconds(resp)
                print(f"[generate] Rate limited, waiting {wait:.0f}s before retry...")
                time.sleep(wait)
                continue
            break

        if _is_model_gone(resp):
            print(f"[generate] Model '{model}' unavailable ({resp.status_code}), trying next.")
            continue

        resp.raise_for_status()
        if _active_model != model:
            print(f"[generate] Using Groq model: {model}")
            _active_model = model
        break
    else:
        raise RuntimeError(
            f"No usable Groq model. Tried {GROQ_MODELS}; all returned model-not-found. "
            f"Check https://console.groq.com/docs/models and set the GROQ_MODEL secret."
        )

    choice = resp.json()["choices"][0]
    text = choice["message"].get("content") or ""

    # Say plainly when the model ran out of room, rather than surfacing it as a
    # baffling "Expecting ',' delimiter" from the half-written JSON. This is the
    # exact failure that produced 0 stories on run #195.
    if choice.get("finish_reason") == "length":
        raise ValueError(
            f"response hit the {MAX_TOKENS}-token cap and was cut off mid-JSON "
            f"(model {_active_model}). Raise GROQ_MAX_TOKENS, or switch to a "
            f"model that does not spend the budget on hidden reasoning."
        )
    if not text.strip():
        raise ValueError(
            f"model {_active_model} returned empty content — it likely spent the "
            f"whole {MAX_TOKENS}-token budget on hidden reasoning."
        )

    # Some models narrate before answering. Drop <think> blocks and markdown
    # fences so a good story is not thrown away over its wrapper.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*```(?:json)?|```\s*$", "", text.strip(), flags=re.MULTILINE)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response: {text[:300]}")
    return json.loads(match.group(0))


def _parse_retry_seconds(resp) -> float:
    """Seconds to wait after a 429, from Retry-After or the token-reset header (capped)."""
    retry_after = resp.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass
    reset = resp.headers.get("x-ratelimit-reset-tokens", "")  # e.g. "17.78s" or "1m2s"
    m = re.match(r"(?:(\d+)m)?([\d.]+)s", reset)
    if m:
        secs = int(m.group(1) or 0) * 60 + float(m.group(2))
        return min(secs + 1.0, 30.0)
    return 15.0


def pick_theme(state_rows: list, variant: str | None = None) -> str:
    """Least-used theme. Scoped per variant when given, so a long video does not
    starve the short rotation of a theme (different audiences, independent cycles)."""
    rows = state_rows
    if variant is not None:
        rows = [r for r in rows if (r.get("variant") or "short") == variant]
    counts = {t: 0 for t in THEMES}
    for r in rows[-100:]:
        if r.get("theme") in counts:
            counts[r["theme"]] += 1
    return min(counts, key=counts.get)


def main():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    target = QUEUE_TARGETS["short"]
    unclaimed = (
        sb.table("story_queue").select("id", count="exact")
        .is_("claimed_at", "null").eq("variant", "short").execute().count
    )
    print(f"[generate] Unclaimed short stories: {unclaimed}")
    if unclaimed >= target:
        print("[generate] Queue healthy, nothing to do.")
        return

    system_prompt = CHANNEL_BRIEF + AUTOMATION_TAIL

    state_rows = sb.table("story_state").select("variant,theme,hook,fingerprint,curve").execute().data

    written = 0
    attempts = 0
    while unclaimed + written < target and attempts < (target - unclaimed) * 6:
        attempts += 1
        theme = pick_theme(state_rows, variant="short")
        recent = [r for r in state_rows if r.get("theme") == theme][-25:]
        user_prompt = (
            f"Theme lock for this spin-off: \"{theme}\".\n\n"
            f"Recent entries in this theme batch (avoid repeating fingerprints/hooks/curves):\n"
            f"{json.dumps(recent, ensure_ascii=False)}\n\n"
            f"Generate one new story now."
        )
        try:
            story = call_groq(system_prompt, user_prompt)
            validate_story(story)
            sb.table("story_queue").insert({
                "variant": "short",
                "theme": story["theme"], "title": story["title"], "payload": story,
            }).execute()
            state_rows.append({"variant": "short", "theme": story["theme"],
                                "hook": story["dna"].get("hook"),
                                "fingerprint": story["dna"].get("fingerprint"), "curve": story["curve"]})
            written += 1
            print(f"[generate] Queued: {story['title']} ({story['theme']})")
        except Exception as e:
            print(f"[generate] Attempt failed, retrying: {e}")

    print(f"[generate] Done. Wrote {written} stories. Queue now ~{unclaimed + written}.")

    # An empty queue means the next render has nothing to post. Exit non-zero so
    # the workflow's Telegram failure alert fires, instead of reporting a green
    # run that quietly published nothing.
    if unclaimed + written == 0:
        raise SystemExit(
            "[generate] FATAL: queue is empty and no stories could be generated — "
            "nothing will be posted. See the errors above."
        )


if __name__ == "__main__":
    main()
