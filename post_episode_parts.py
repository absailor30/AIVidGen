"""Upload a character episode, already cut into Shorts, as scheduled YouTube posts.

Reads a manifest in episodes/ (see recipe_clause_ep1.json): the part files live
on the branch it names, one part goes public per day at publish_hour_utc from
first_day on. Each upload is private with publishAt, so YouTube flips it public
on its own; nothing here needs to run again on the day.

    python post_episode_parts.py episodes/recipe_clause_ep1.json [PARTS_DIR]
"""

import datetime as dt
import glob
import json
import os
import sys

from render_from_supabase import upload_to_youtube


def main():
    manifest = json.load(open(sys.argv[1]))
    parts_dir = sys.argv[2] if len(sys.argv) > 2 else manifest["files_dir"]
    files = sorted(glob.glob(os.path.join(parts_dir, "part*.mp4")))
    if not files:
        raise SystemExit(f"no part*.mp4 in {parts_dir}")
    first = dt.date.fromisoformat(manifest["first_day"])
    hh, mm = map(int, manifest["publish_hour_utc"].split(":"))
    total = len(files)
    for i, path in enumerate(files, 1):
        when = dt.datetime(first.year, first.month, first.day, hh, mm) + dt.timedelta(days=i - 1)
        nxt = f"Part {i + 1} drops tomorrow." if i < total else "Subscribe for episode 2."
        kit = {
            "youtube_title": manifest["title"].format(n=i)[:100],
            "youtube_description": manifest["description"].format(n=i, next=nxt),
            "youtube_tags": manifest["tags"],
        }
        os.environ["YOUTUBE_PUBLISH_AT"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
        vid = upload_to_youtube(path, kit)
        print(f"[episode] Part {i}/{total}: https://youtube.com/shorts/{vid} "
              f"goes public {os.environ['YOUTUBE_PUBLISH_AT']}")


if __name__ == "__main__":
    main()
