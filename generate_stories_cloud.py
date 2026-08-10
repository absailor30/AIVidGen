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
GROQ_MODEL = "llama-3.3-70b-versatile"
QUEUE_TARGET = 4

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


def validate_story(story: dict):
    missing = [k for k in REQUIRED_KEYS if k not in story]
    if missing:
        raise ValueError(f"Missing keys: {missing}")
    if any(k not in story["dna"] for k in REQUIRED_DNA_KEYS):
        raise ValueError("dna missing required keys")
    if any(k not in story["publishing_kit"] for k in REQUIRED_KIT_KEYS):
        raise ValueError("publishing_kit missing required keys")
    if len(story["variables_changed"]) < 6:
        raise ValueError("variables_changed needs >= 6 items")
    if story["score"] < 85:
        raise ValueError(f"score {story['score']} below 85")
    # Enforce the ~90-120s narration length (350-420 target, allow a little slack).
    word_count = len(story["story"].split())
    if not (260 <= word_count <= 360):
        raise ValueError(f"story word count {word_count} outside 260-360 range")
    lowered = story["story"].lower()
    for banned in ("part 1", "part 2", "part one", "part two", "to be continued"):
        if banned in lowered:
            raise ValueError(f"story must be self-contained, found '{banned}'")


def call_groq(system: str, user: str) -> dict:
    # Retry on 429 (rate limit), honoring the reset window the API reports.
    for attempt in range(4):
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.9,
                "max_tokens": 1500,
            },
            timeout=60,
        )
        if resp.status_code == 429 and attempt < 3:
            wait = _parse_retry_seconds(resp)
            print(f"[generate] Rate limited, waiting {wait:.0f}s before retry...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break

    text = resp.json()["choices"][0]["message"]["content"]
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


def pick_theme(state_rows: list) -> str:
    counts = {t: 0 for t in THEMES}
    for r in state_rows[-100:]:
        if r.get("theme") in counts:
            counts[r["theme"]] += 1
    return min(counts, key=counts.get)


def main():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    unclaimed = sb.table("story_queue").select("id", count="exact").is_("claimed_at", "null").execute().count
    print(f"[generate] Unclaimed stories: {unclaimed}")
    if unclaimed >= QUEUE_TARGET:
        print("[generate] Queue healthy, nothing to do.")
        return

    system_prompt = CHANNEL_BRIEF + AUTOMATION_TAIL

    state_rows = sb.table("story_state").select("theme,hook,fingerprint,curve").execute().data

    written = 0
    attempts = 0
    while unclaimed + written < QUEUE_TARGET and attempts < (QUEUE_TARGET - unclaimed) * 6:
        attempts += 1
        theme = pick_theme(state_rows)
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
                "theme": story["theme"], "title": story["title"], "payload": story,
            }).execute()
            state_rows.append({"theme": story["theme"], "hook": story["dna"].get("hook"),
                                "fingerprint": story["dna"].get("fingerprint"), "curve": story["curve"]})
            written += 1
            print(f"[generate] Queued: {story['title']} ({story['theme']})")
        except Exception as e:
            print(f"[generate] Attempt failed, retrying: {e}")

    print(f"[generate] Done. Wrote {written} stories. Queue now ~{unclaimed + written}.")


if __name__ == "__main__":
    main()
