"""Queue a long-form compilation of the channel's best-performing Shorts.

The single-story long-form lane averaged ~10 views a video, while the same
channel's Shorts regularly reach hundreds. This stitches proven Short stories
into one 16:9 video (~11 min) with chapters, so long-form is tested on content
viewers already chose, rather than on a fresh 10-minute story.

It writes one `long` row to story_queue; the normal long renderer posts it
(dispatch story_render_long.yml with force=true while the auto lane is paused).
No Groq calls: the intro, transitions, title and description are templated.

    python build_compilation.py                 # best theme, 7 stories
    THEME="In-Law Conflicts" STORIES=7 python build_compilation.py
    DRY_RUN=1 python build_compilation.py       # print, write nothing
"""

import json
import os
import re
import statistics

from supabase import create_client

STORIES = int(os.environ.get("STORIES") or 7)
MIN_AGE_DAYS = 3          # judge stories on settled views
WORDS_PER_SEC = 3.42      # long-form narration rate (1.2x Jenny)
MIN_WORDS = 2150          # ~10.5 min, keeps the video over 10:15

THEME_PHRASE = {
    "Wedding & Family Entitlement": "Wedding Drama",
    "Marriage & Infidelity": "Cheating Spouse",
    "Sibling Rivalry & Favoritism": "Sibling Betrayal",
    "In-Law Conflicts": "In-Law Nightmare",
    "Career Sabotage / Workplace Betrayal": "Workplace Betrayal",
    "Family Inheritance": "Inheritance Drama",
    "Friendship Betrayal & Glow-Up": "Friend Betrayal",
    "Neighbour & Roommate Conflicts": "Nightmare Neighbor",
    "Family Money & Borrowed Cash": "Family Money",
    "Bridesmaid & Wedding Party Drama": "Bridesmaid Drama",
    "Holiday Dinner Blow-Up": "Holiday Dinner",
    "Landlord / Tenant Dispute": "Landlord Revenge",
}
ORDINAL = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]


def _ts(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def candidates(sb) -> list[dict]:
    latest = sb.table("story_metrics").select("collected_on").order(
        "collected_on", desc=True).limit(1).execute().data[0]["collected_on"]
    views = {r["youtube_id"]: r["views"] or 0 for r in sb.table("story_metrics")
             .select("youtube_id,views").eq("collected_on", latest).execute().data}
    used = set()
    for r in sb.table("story_queue").select("payload").eq("theme", "Compilation").execute().data:
        used.update(r["payload"].get("compilation_of") or [])
    rows = sb.table("story_queue").select("id,theme,title,payload,youtube_id,created_at") \
        .eq("variant", "short").eq("rendered", True).execute().data
    out = []
    for r in rows:
        yt = r.get("youtube_id")
        if not yt or yt not in views or yt in used:
            continue
        story = (r["payload"] or {}).get("story")
        if not story:
            continue
        out.append({"queue_id": r["id"], "youtube_id": yt, "theme": r["theme"],
                    "title": r["payload"].get("title") or r["title"], "story": story,
                    "keywords": r["payload"].get("keywords") or "", "views": views[yt]})
    return out


def pick(cands: list[dict], theme: str | None) -> tuple[str, list[dict]]:
    by_theme: dict[str, list[dict]] = {}
    for c in cands:
        by_theme.setdefault(c["theme"], []).append(c)
    if not theme:
        eligible = {t: v for t, v in by_theme.items() if len(v) >= STORIES}
        theme = max(eligible, key=lambda t: statistics.median(
            sorted((c["views"] for c in eligible[t]), reverse=True)[:STORIES]))
    best = sorted(by_theme[theme], key=lambda c: c["views"], reverse=True)[:STORIES]
    return theme, best


def build(theme: str, chosen: list[dict]) -> dict:
    phrase = THEME_PHRASE.get(theme, theme)
    n = len(chosen)
    intro = (f"{n} {phrase.lower()} stories, every one told by the person it happened to. "
             f"Each one ends with a twist nobody saw coming. Stay to the end, because the "
             f"last one is the wildest of them all.")
    outro = ("Which one would you have walked away from? Tell me in the comments, and "
             "subscribe for a new story every day.")
    parts = [intro]
    chapters = [("0:00", "Intro")]
    words_so_far = len(intro.split())
    for i, c in enumerate(chosen):
        head = f"Story {ORDINAL[i]}. {c['title']}."
        chapters.append((_ts(words_so_far / WORDS_PER_SEC), c["title"]))
        body = re.sub(r"\s+", " ", c["story"]).strip()
        parts.append(f"{head}\n\n{body}")
        words_so_far += len(head.split()) + len(body.split())
    parts.append(outro)
    story_text = "\n\n".join(parts)

    title = f"{n} {phrase} Stories That Left Everyone Speechless"
    chapter_lines = "\n".join(f"{t} {name}" for t, name in chapters)
    description = (f"{n} true-style {phrase.lower()} stories with a twist, back to back.\n\n"
                   f"{chapter_lines}\n\n"
                   f"Narrated stories with AI voice and stock footage. "
                   f"Subscribe for a new story every day.\n"
                   f"[[TWISTY: theme=Compilation; source_theme={theme}]]")
    terms = []
    for c in chosen:
        kw = [t.strip() for t in re.split(r",", c["keywords"]) if t.strip()]
        if len(kw) < 2:  # Short keywords are one plain search string
            words = c["keywords"].split()
            kw = [" ".join(words[i:i + 3]) for i in range(0, min(len(words), 9), 3)]
        terms += kw[:3]
    return {
        "theme": "Compilation",
        "title": title,
        "story": story_text,
        "keywords": ", ".join(terms[:18]),
        "curve": f"Compilation of {n} proven Shorts ({theme}), best last.",
        "dna": {"hook": chosen[-1]["title"], "conflict": f"{n} {phrase.lower()} stories",
                "relationship": "", "emotion": "", "payoff": "",
                "fingerprint": f"compilation:{theme}"},
        "publishing_kit": {"youtube_title": title[:100], "youtube_description": description,
                           "youtube_tags": [phrase.lower() + " stories", "story compilation",
                                            "reddit style stories", "family drama stories",
                                            "revenge stories", "storytime"]},
        "compilation_of": [c["youtube_id"] for c in chosen],
        "source_theme": theme,
        "estimated_seconds": round(words_so_far / WORDS_PER_SEC),
    }


def main():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    theme, chosen = pick(candidates(sb), os.environ.get("THEME") or None)
    # Open on the second-strongest story and close on the strongest: the intro
    # promises the last one is the wildest, and it holds viewers to the end.
    chosen.sort(key=lambda c: c["views"], reverse=True)
    if len(chosen) > 2:
        chosen = [chosen[1]] + chosen[2:][::-1] + [chosen[0]]
    story = build(theme, chosen)
    words = len(story["story"].split())
    print(f"[compilation] {story['title']}: {len(chosen)} stories, {words} words, "
          f"~{story['estimated_seconds'] // 60}:{story['estimated_seconds'] % 60:02d}")
    for c in chosen:
        print(f"  {c['views']:>6} views  {c['title']}")
    if words < MIN_WORDS:
        raise SystemExit(f"[compilation] {words} words is under {MIN_WORDS} (~10.5 min); "
                         f"raise STORIES.")
    if os.environ.get("DRY_RUN") == "1":
        print(story["publishing_kit"]["youtube_description"])
        return
    row = sb.table("story_queue").insert({"variant": "long", "theme": "Compilation",
                                          "title": story["title"], "payload": story}).execute()
    print(f"[compilation] Queued as story_queue id {row.data[0]['id']}")


if __name__ == "__main__":
    main()
