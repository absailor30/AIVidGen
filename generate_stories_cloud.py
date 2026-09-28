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
import sys
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

# Groq 429 backoff. The old values -- 4 attempts capped at 30s, falling back to
# 15s when Groq sends no reset header -- gave up after ~45 seconds, which is
# nothing against a per-minute token cap that resets in 60. Six attempts at up
# to 120s rides out a minute-window limit; a daily quota will still exhaust
# these, which is exactly what the body logged on each retry is there to tell
# apart. Worst case is ~12 minutes of waiting, well inside every job timeout.
GROQ_429_ATTEMPTS = 6
MAX_RETRY_WAIT = 120.0

# How deep to keep each variant's queue.
# "illustrated" queues the same stories as "short" -- only the backdrop
# differs at render time -- but needs its own queue so the two lanes never
# claim each other's rows.
# The long lane keeps a deeper buffer than the others on purpose. It is the
# only lane whose generation is a separate scheduled job (story_generate_long),
# so the buffer is what makes an empty queue at render time survivable: run #14
# died because generation and rendering shared a slot and Groq rate-limited the
# 17 calls a long story needs, leaving nothing to post.
QUEUE_TARGETS = {"short": 4, "long": 3, "illustrated": 2}
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

# Weighted by measured REACH, not retention. This replaces an earlier set of
# weights derived from average view percentage, which turned out to be the
# wrong axis.
#
# With eight daily snapshots there are now enough videos of matched age to
# compare fairly. Median views at day 3 (the age-independent measure), beside
# retention over the same videos:
#
#   theme                     n   median day-3 views   retention
#   Wedding & Entitlement     3            797           68.3%
#   Marriage & Infidelity     6            378           65.1%
#   Sibling Rivalry           6            246           62.7%
#   In-Law Conflicts          5            219           64.6%
#   Career Sabotage          10            110           77.6%
#   Family Inheritance        6             99           55.7%
#
# The two columns barely relate. Career Sabotage retains best of everything and
# reaches fewer people than all but one theme; Family Inheritance is poor at
# both. Retention says how much of a video someone watches once it starts,
# which is not what decides how many people YouTube shows it to. Weighting on
# it demoted Marriage & Infidelity to 1 when it is second on reach, and
# promoted Family Inheritance, and channel-wide daily views fell from ~1750 to
# ~550 over the week that followed.
#
# So: rank by median day-3 views, with retention only breaking ties. Medians
# rather than means -- one Career Sabotage video pulled 754 views and dragged
# its mean to 204 against a median of 110.
#
# Wedding & Entitlement rests on only 3 videos, so weight 4 is deliberately
# short of what its median alone would justify; its lowest of the three (365)
# still beats every other theme's median, which is what earns it the top slot.
# Friendship Betrayal has no matched-age data at all yet and stays at 1 purely
# to keep sampling it.
#
# A weight is a relative share of the queue, not a ranking -- weight 4 gets
# roughly four times the slots of weight 1. Nothing is dropped outright, so a
# down-weighted theme keeps earning data and can be promoted when it does.
# Re-derive these from story_metrics rather than trusting them indefinitely.
THEME_WEIGHTS = {
    "Wedding & Family Entitlement": 4,
    "Marriage & Infidelity": 3,
    "Sibling Rivalry & Favoritism": 2,
    "In-Law Conflicts": 2,
    "Career Sabotage / Workplace Betrayal": 1,
    "Family Inheritance": 1,
    "Friendship Betrayal & Glow-Up": 1,
}

THEMES = list(THEME_WEIGHTS)

REQUIRED_KEYS = ["theme", "title", "story", "keywords", "dna", "curve",
                 "variables_changed", "score", "cooldown_flag", "tracking_tag", "publishing_kit"]
REQUIRED_DNA_KEYS = ["hook", "relationship", "conflict", "emotion", "payoff", "fingerprint"]
REQUIRED_KIT_KEYS = ["youtube_title", "youtube_description", "youtube_tags",
                      "instagram_caption", "instagram_hashtags"]
# Long-form is YouTube-only, so the Instagram fields are not required. Nothing
# downstream reads them for that variant (upload_to_youtube uses only these).
REQUIRED_KIT_KEYS_LONG = ["youtube_title", "youtube_description", "youtube_tags"]

# Per-BEAT word budgets for the long variant, at ~3.42 words/sec (JennyNeural
# 2.85 w/s x the 1.2x long-form rate).
#
# Every target is <=165 words, and that ceiling is empirical, not a guess. Two
# real runs showed a hard cliff in the model's length compliance:
#   target <=120  ->  84, 99, 113, 98, 56 words. Five for five, first attempt.
#   target 325    ->  412, 414, 391, 502, 548, 417, 412, 426, 535. Nine of ten
#                     misses, clustered ~410 — the model's natural "narrative
#                     block" length, sitting just above a 384 ceiling.
# Fighting that with retries wasted four attempts a beat. Splitting each body,
# the truth and the close into halves keeps every request inside the range the
# model reliably hits, and the halves get "first half"/"second half" briefs so
# they do not repeat each other.
#
# `brief` names the logical beat in the plan that this request draws from;
# `part` positions it within that beat.
LONG_BEATS = {
    "hook":      {"target":  96, "min":  67, "max": 125, "brief": "hook",     "part": None},
    "lock_in":   {"target":  96, "min":  67, "max": 125, "brief": "lock_in",  "part": None},
    "body_1a":   {"target": 163, "min": 114, "max": 212, "brief": "body_1",   "part": "first"},
    "body_1b":   {"target": 163, "min": 114, "max": 212, "brief": "body_1",   "part": "second"},
    "rehook_1":  {"target":  62, "min":  43, "max":  81, "brief": "rehook_1", "part": None},
    "body_2a":   {"target": 163, "min": 114, "max": 212, "brief": "body_2",   "part": "first"},
    "body_2b":   {"target": 163, "min": 114, "max": 212, "brief": "body_2",   "part": "second"},
    "rehook_2":  {"target":  62, "min":  43, "max":  81, "brief": "rehook_2", "part": None},
    "body_3a":   {"target": 163, "min": 114, "max": 212, "brief": "body_3",   "part": "first"},
    "body_3b":   {"target": 163, "min": 114, "max": 212, "brief": "body_3",   "part": "second"},
    "rehook_3":  {"target":  62, "min":  43, "max":  81, "brief": "rehook_3", "part": None},
    "truth_a":   {"target":  98, "min":  69, "max": 127, "brief": "truth",    "part": "first"},
    "truth_b":   {"target":  97, "min":  68, "max": 126, "brief": "truth",    "part": "second"},
    "closing_a": {"target": 146, "min": 102, "max": 190, "brief": "closing",  "part": "first"},
    "closing_b": {"target": 145, "min": 102, "max": 188, "brief": "closing",  "part": "second"},
    "cta":       {"target":  96, "min":  67, "max": 125, "brief": "cta",      "part": None},
}
for _spec in LONG_BEATS.values():
    _spec["seconds"] = round(_spec["target"] / 3.42)
BEAT_ORDER = list(LONG_BEATS)

# The 11 logical beats the planning call briefs (several map to two requests).
LOGICAL_BEATS = ["hook", "lock_in", "body_1", "rehook_1", "body_2", "rehook_2",
                 "body_3", "rehook_3", "truth", "closing", "cta"]

# Targets total 1938 words (~9.4 min), under the 10-minute ceiling. Per-beat
# bands alone would allow 6.6-12.3 min, so gate the aggregate too.
LONG_TOTAL_MIN, LONG_TOTAL_MAX = 1650, 2150
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
- End with ONE spoken call to action, woven naturally into the closing line.
  The user message carries a CTA INSTRUCTION for this story -- follow it exactly
  and use no other ask. It is rotated per story (share / comment a word /
  follow), because a single clear ask outperforms three competing ones, and
  because a channel that makes the same request every time gets tuned out.
  Echo which one you were given back in the "cta_style" field.
- Keep it grounded and realistic — no over-the-top or implausible twists.
- OPENING CLASS: vary it. Pick whichever of these best fits the story rather
  than defaulting to one — an unexpected call or message arriving, a moment of
  recognition, an observed behaviour, a found object, or an overheard sentence.
  Avoid opening on a found object more than occasionally: it was over half of
  everything the channel had published, and monotony is its own problem.
  (An earlier version of this brief banned object openings outright, on a
  retention gap measured across videos of wildly different ages. Compared
  fairly at day 3, unexpected-call and recognition retain 61.6% and 61.0% --
  indistinguishable -- so the gap did not survive. The ban also stopped any new
  object openings being produced, which made the question unmeasurable. Keep
  the classes in rotation so the data can settle it.)

Respond with ONLY a single JSON object (no markdown fences, no commentary before or
after), matching exactly:

{
  "theme": "...", "title": "...",
  "story": "... the 350-420 word first-person story described above ...",
  "keywords": "... 15-25 word stock-footage search string, plain words, no commas ...",
  "dna": {"hook": "...", "relationship": "...", "conflict": "...", "emotion": "...", "payoff": "... the satisfying/karmic resolution ...", "fingerprint": "..."},
  "curve": "... describe the hook -> build-up -> trigger -> satisfying-close arc ...",
  "cta_style": "... copy the cta_style token given in the CTA INSTRUCTION, exactly ...",
  "cta_keyword": "... the single word for the comment CTA, or \"\" for the other styles ...",
  "variables_changed": ["...", "..."],
  "score": 88,
  "cooldown_flag": "...",
  "tracking_tag": "[[TWISTY: theme=<the locked theme, copied exactly>; hook=<opening class: Unexpected Call | Recognition | Behavior | Object | Sentence>; fingerprint=...; ending=...]]",
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


def validate_cta(story: dict, expected_style: str):
    """The CTA is only rotated if the model actually used the style it was given.

    Without this the model drifts back to "follow for more" on every story --
    it is the most common ending in its training data, and the one the brief
    used to hardcode. A silent drift would look like rotation in the database
    and be a single CTA in the videos.
    """
    style = (story.get("cta_style") or "").strip()
    if style != expected_style:
        raise ValueError(f"cta_style is {style!r}, expected {expected_style!r}")

    text = story["story"].lower()
    if expected_style == "comment_word":
        word = (story.get("cta_keyword") or "").strip()
        if not word or not word.isalpha() or len(word) > 15:
            raise ValueError(f"cta_keyword must be one plain word, got {word!r}")
        if "comment" not in text:
            raise ValueError("comment CTA must ask the viewer to comment")
        # The word must appear in the STORY BODY, not just in the CTA line --
        # checking the whole text is vacuous, since the closing ask always
        # contains the word by construction. Everything before the final
        # "comment" is the body.
        body = text[:text.rfind("comment")]
        if word.lower() not in body:
            # The point of this style is a word the viewer just heard. One that
            # appears only in the ask reads as a spam prompt.
            raise ValueError(
                f"cta_keyword {word!r} does not appear in the story body "
                f"(only in the CTA line)"
            )
    elif expected_style == "share":
        if not any(w in text for w in ("send this", "share this", "send it", "share it")):
            raise ValueError("share CTA must ask the viewer to send or share it")
    elif expected_style == "follow":
        if "follow" not in text:
            raise ValueError("follow CTA must ask the viewer to follow")

    # Competing asks defeat the whole reason for rotating one at a time. Only
    # the tail is checked: a story can legitimately use these words in prose.
    tail = text[-320:]
    others = {"share": ("follow", "comment"), "comment_word": ("follow", "share this"),
              "follow": ("comment", "share this")}[expected_style]
    for other in others:
        if other in tail:
            raise ValueError(f"CTA style {expected_style} must not also ask to {other}")


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
    # The prompt locks a theme, but the model has quietly invented its own
    # before ("Monogamy & Financial Betrayal", 2026-09-11). An off-list theme
    # silently breaks the rotation -- pick_theme cannot count it, so it neither
    # gets scheduled nor blocks anything -- and it fragments the per-theme
    # performance data that now steers the weights.
    if story["theme"] not in THEMES:
        raise ValueError(f"theme {story['theme']!r} is not one of THEMES")

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
        for attempt in range(GROQ_429_ATTEMPTS):
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
            if resp.status_code == 429 and attempt < GROQ_429_ATTEMPTS - 1:
                wait = _parse_retry_seconds(resp)
                # Print the body. A per-minute token cap and an exhausted daily
                # quota both arrive as a bare 429, and they need opposite
                # responses -- wait it out vs. stop and fix the plan. Without
                # this the log said only "429" and the distinction was a guess.
                print(f"[generate] Rate limited ({model}), waiting {wait:.0f}s "
                      f"before retry. Groq said: {(resp.text or '').strip()[:300]}")
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
            return min(float(retry_after), MAX_RETRY_WAIT)
        except ValueError:
            pass
    reset = resp.headers.get("x-ratelimit-reset-tokens", "")  # e.g. "17.78s" or "1m2s"
    m = re.match(r"(?:(\d+)m)?([\d.]+)s", reset)
    if m:
        secs = int(m.group(1) or 0) * 60 + float(m.group(2))
        return min(secs + 1.0, MAX_RETRY_WAIT)
    return 15.0


CTA_STYLES = {
    # "share" asks for a send, which is the strongest ranking signal on both
    # Shorts and Reels -- a share is worth far more than a like, and these
    # stories are built to make someone think of a specific person.
    "share": (
        "Close by asking the viewer to SEND or SHARE this with someone who has "
        "been through the same thing. Make it specific to this story's situation, "
        "not generic -- name the kind of person who would recognise it. One "
        "sentence, spoken naturally as the last line. Do NOT ask for a follow, "
        "a like or a comment in this story."
    ),
    # "comment_word" trades reach for comment volume. The word has to come from
    # the story itself or the prompt reads as spam, which is why cta_keyword is
    # generated per story and validated against the story text.
    "comment_word": (
        "Close by asking the viewer to comment ONE specific word if they have "
        "been through the same thing. Choose a single word that appears in this "
        "story and carries its emotional weight (e.g. the object, the room, the "
        "phrase that stung). Put that word in the cta_keyword field, and use it "
        "in the closing line in the form: comment <WORD> if you went through "
        "the same. One sentence, spoken naturally. Do NOT ask for a follow, a "
        "like or a share in this story."
    ),
    "follow": (
        "Close by asking the viewer to follow for more stories like this. One "
        "sentence, spoken naturally as the last line, in the channel's voice -- "
        "not 'don't forget to smash that follow button'. Do NOT ask for a "
        "comment or a share in this story."
    ),
}


def pick_cta_style(state_rows: list, variant: str | None = None) -> str:
    """Least-used CTA style, rotated per variant.

    Deliberately one CTA per story rather than stacking all three. Asking for a
    share AND a comment AND a follow in the last ten seconds gets none of them;
    a single clear ask is the whole point of rotating instead of combining.

    Rotation is driven by story_state, so it survives across runs and runners --
    the generator is stateless and every run is a fresh container, so anything
    held in memory would reset the cycle on every invocation. Rows written
    before cta_style existed read as None and are ignored, which means the
    cycle simply starts fresh rather than skewing towards whatever is first.
    """
    rows = state_rows
    if variant is not None:
        rows = [r for r in rows if (r.get("variant") or "short") == variant]
    counts = {c: 0 for c in CTA_STYLES}
    for r in rows[-60:]:
        if r.get("cta_style") in counts:
            counts[r["cta_style"]] += 1
    # Least-used wins; ties break on CTA_STYLES order, which keeps the cycle
    # deterministic instead of drifting.
    return min(CTA_STYLES, key=lambda c: (counts[c], list(CTA_STYLES).index(c)))


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

    # Pick whichever theme is furthest below the share its weight entitles it
    # to. Equal weights reduce to the old least-used behaviour, and because a
    # pick immediately shrinks that theme's deficit, consecutive calls still
    # interleave themes rather than emitting a run of the same one -- which
    # STORY_ENGINE_BIBLE asks for explicitly (a batch is a tracking unit, not a
    # publishing schedule).
    total = sum(counts.values()) + 1  # +1: the story this call is about to make
    weight_sum = sum(THEME_WEIGHTS.values())
    return max(THEMES, key=lambda t: THEME_WEIGHTS[t] / weight_sum * total - counts[t])


def main():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    # Which queue to fill. The renderer reads the same variable, so a workflow
    # sets STORY_VARIANT once and both halves of the job agree.
    variant = os.environ.get("STORY_VARIANT") or "short"
    if variant not in QUEUE_TARGETS:
        sys.exit(f"[generate] Unknown STORY_VARIANT {variant!r}; "
                 f"expected one of {sorted(QUEUE_TARGETS)}")
    target = QUEUE_TARGETS[variant]
    unclaimed = (
        sb.table("story_queue").select("id", count="exact")
        .is_("claimed_at", "null").eq("variant", variant).execute().count
    )
    print(f"[generate] Unclaimed {variant} stories: {unclaimed}")
    if unclaimed >= target:
        print("[generate] Queue healthy, nothing to do.")
        return

    system_prompt = CHANNEL_BRIEF + AUTOMATION_TAIL

    # cta_style is selected because pick_cta_style rotates on it. Leave it out
    # and every run sees None, picks the first style, and "rotation" becomes a
    # single CTA forever.
    state_rows = sb.table("story_state").select(
        "variant,theme,hook,fingerprint,curve,cta_style"
    ).execute().data

    written = 0
    attempts = 0
    while unclaimed + written < target and attempts < (target - unclaimed) * 6:
        attempts += 1
        theme = pick_theme(state_rows, variant=variant)
        cta_style = pick_cta_style(state_rows, variant=variant)
        recent = [r for r in state_rows if r.get("theme") == theme][-25:]
        user_prompt = (
            f"Theme lock for this spin-off: \"{theme}\".\n\n"
            f"CTA INSTRUCTION (cta_style token: {cta_style})\n"
            f"{CTA_STYLES[cta_style]}\n\n"
            f"Recent entries in this theme batch (avoid repeating fingerprints/hooks/curves):\n"
            f"{json.dumps(recent, ensure_ascii=False)}\n\n"
            f"Generate one new story now."
        )
        try:
            story = call_groq(system_prompt, user_prompt)
            validate_story(story)
            validate_cta(story, cta_style)
            sb.table("story_queue").insert({
                "variant": variant,
                "theme": story["theme"], "title": story["title"], "payload": story,
            }).execute()
            state_rows.append({"variant": variant, "theme": story["theme"],
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
