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
from collections import Counter

import requests
from supabase import create_client

BIBLE_PATH = os.path.join(os.path.dirname(__file__), "Outputs", "STORY_ENGINE_BIBLE_v4.1.md")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
QUEUE_TARGET = 4

THEMES = [
    "Family Inheritance",
    "Career Sabotage / Workplace Betrayal",
    "Marriage & Infidelity",
    "Landlord / Tenant Dispute",
    "Business Partnership Betrayal",
]

REQUIRED_KEYS = ["theme", "title", "story", "keywords", "dna", "curve",
                 "variables_changed", "score", "cooldown_flag", "tracking_tag", "publishing_kit"]
REQUIRED_DNA_KEYS = ["hook", "relationship", "conflict", "emotion", "payoff", "fingerprint"]
REQUIRED_KIT_KEYS = ["youtube_title", "youtube_description", "youtube_tags",
                      "instagram_caption", "instagram_hashtags"]

AUTOMATION_TAIL = """

---

ADDITIONAL AUTOMATION REQUIREMENT: respond with ONLY a single JSON object
(no markdown fences, no commentary before or after), matching exactly:

{
  "theme": "...", "title": "...",
  "story": "... 320-480 words, first person, one paragraph, no quotation marks, MUST end with a short spoken follow-CTA line woven naturally into the closing (e.g. 'Follow for the next one.') ...",
  "keywords": "... 15-25 word stock-footage search string, plain words, no commas ...",
  "dna": {"hook": "...", "relationship": "...", "conflict": "...", "emotion": "...", "payoff": "...", "fingerprint": "..."},
  "curve": "...",
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


def call_groq(system: str, user: str) -> dict:
    resp = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"},
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.9,
            "max_tokens": 3000,
        },
        timeout=60,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response: {text[:300]}")
    return json.loads(match.group(0))


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

    with open(BIBLE_PATH, encoding="utf-8") as f:
        bible = f.read()
    system_prompt = bible + AUTOMATION_TAIL

    state_rows = sb.table("story_state").select("theme,hook,fingerprint,curve").execute().data

    written = 0
    attempts = 0
    while unclaimed + written < QUEUE_TARGET and attempts < (QUEUE_TARGET - unclaimed) * 3:
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
