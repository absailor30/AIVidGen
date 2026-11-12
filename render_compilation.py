"""Render an hour-long compilation in pieces, then stitch and upload it.

A long video cannot go through render_from_supabase.py in one pass: an 11 min
video already takes 30-60 min on a runner, so an hour would pass the 6 h job
ceiling, and one failed narration would lose all of it. build_compilation.py
(TARGET_MINUTES) stores one narration per story in payload["segments"]; each is
rendered here as its own short 16:9 video with its own footage and captions,
and the pieces are joined without re-encoding.

    python render_compilation.py preflight            # is the channel allowed >15 min?
    SHARD=0 SHARDS=4 python render_compilation.py segments
    python render_compilation.py one 12               # a single segment (used by `segments`)
    python render_compilation.py publish              # stitch, upload, record

Env: QUEUE_ID (story_queue row), SEG_DIR (default ./segments), and for publish
the same YouTube variables as render_from_supabase.py. DRY_RUN=1 stitches to
SEG_DIR/final.mp4 and uploads nothing.
"""

import os
import shutil
import subprocess
import sys

SEG_DIR = os.environ.get("SEG_DIR") or "segments"
MIN_SHARE = 0.85          # publish needs at least this share of the segments
SEGMENT_TIMEOUT = 45 * 60
ATTEMPTS = 3


def _row(sb):
    rows = sb.table("story_queue").select("*").eq("id", int(os.environ["QUEUE_ID"])).execute().data
    if not rows or not rows[0]["payload"].get("segments"):
        raise SystemExit(f"[compilation] Queue row {os.environ['QUEUE_ID']} has no segments.")
    return rows[0]


def _seg_path(i: int) -> str:
    return os.path.join(SEG_DIR, f"seg_{i:03d}.mp4")


def _ts(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def preflight():
    """Fail before hours of rendering if YouTube would refuse a >15 min upload."""
    from googleapiclient.discovery import build
    from render_from_supabase import _youtube_credentials

    try:
        items = build("youtube", "v3", credentials=_youtube_credentials()).channels().list(
            part="status", mine=True).execute().get("items") or []
        status = items[0]["status"].get("longUploadsStatus") if items else None
    except Exception as e:
        print(f"[compilation] Could not read the channel's long-upload status ({e}); continuing.")
        return
    print(f"[compilation] longUploadsStatus: {status}")
    if status in ("disallowed", "eligible"):
        raise SystemExit("[compilation] This channel cannot upload videos over 15 minutes yet. "
                         "Verify it at https://www.youtube.com/verify, then run this again.")


def render_one(i: int):
    from render_from_supabase import render_video, supabase_client

    seg = _row(supabase_client())["payload"]["segments"][i]
    print(f"[compilation] Segment {i}: {seg['title']} ({len(seg['story'].split())} words)")
    path = render_video(seg, "long")
    if not path:
        raise SystemExit(f"[compilation] Segment {i} did not render.")
    os.makedirs(SEG_DIR, exist_ok=True)
    shutil.copy(path, _seg_path(i))


def render_shard():
    from render_from_supabase import supabase_client

    shard, shards = int(os.environ.get("SHARD") or 0), int(os.environ.get("SHARDS") or 1)
    total = len(_row(supabase_client())["payload"]["segments"])
    failed = []
    for i in range(shard, total, shards):
        # A process per segment: a hung or crashed render costs one story, and
        # moviepy's memory is returned between stories.
        for attempt in range(1, ATTEMPTS + 1):
            try:
                subprocess.run([sys.executable, __file__, "one", str(i)],
                               check=True, timeout=SEGMENT_TIMEOUT)
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"[compilation] Segment {i} attempt {attempt}/{ATTEMPTS} failed: {e}")
        else:
            failed.append(i)
    if failed:
        # Not fatal here: publish decides whether enough of the video exists.
        print(f"[compilation] Segments that never rendered: {failed}")


def publish():
    from render_from_supabase import (_youtube_credentials, sb_retry, supabase_client,
                                      upload_to_youtube)
    from thumbnail import _duration, make_thumbnail, set_thumbnail

    sb = supabase_client()
    row = _row(sb)
    story = row["payload"]
    segs = story["segments"]
    have = [i for i in range(len(segs)) if os.path.exists(_seg_path(i))]
    missing = sorted(set(range(len(segs))) - set(have))
    print(f"[compilation] {len(have)}/{len(segs)} segments rendered; missing: {missing or 'none'}")
    if 0 in missing or len(segs) - 1 in missing or len(have) < MIN_SHARE * len(segs):
        raise SystemExit("[compilation] Too much is missing (the intro, the outro, or over "
                         "15% of the stories). Nothing uploaded; re-run with the same queue id.")

    chapters, at = [], 0.0
    list_file = os.path.join(SEG_DIR, "list.txt")
    with open(list_file, "w") as f:
        for i in have:
            f.write(f"file '{os.path.abspath(_seg_path(i))}'\n")
            chapters.append(f"{_ts(at)} {segs[i]['title']}")
            at += _duration(_seg_path(i))
    final = os.path.join(SEG_DIR, "final.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                    "-c", "copy", "-movflags", "+faststart", final], check=True,
                   capture_output=True)
    total = _duration(final)
    print(f"[compilation] Stitched {_ts(total)} ({os.path.getsize(final) / 1e6:.0f} MB); "
          f"segments add up to {_ts(at)}.")
    if abs(total - at) > 5:
        raise SystemExit("[compilation] Stitched length does not match the segments; "
                         "chapters would be wrong. Nothing uploaded.")

    phrase, n = story.get("phrase") or "Family Drama", len(have)
    kit = dict(story["publishing_kit"])
    hour = total >= 3600
    if not hour:
        # Never claim an hour the video does not have.
        kit["youtube_title"] = f"{n} {phrase} Stories That Left Everyone Speechless"
    length = "1 hour" if hour else f"{int(total // 60)} minutes"
    kit["youtube_description"] = (
        f"{length} of {phrase.lower()} stories with a twist, back to back: {n} stories.\n\n"
        + "\n".join(chapters) + "\n\n"
        "Narrated stories with AI voice and stock footage. Subscribe for a new story every day.\n"
        f"[[TWISTY: theme=Compilation; source_theme={story.get('source_theme')}]]")
    print(f"[compilation] Title: {kit['youtube_title']}")

    if os.environ.get("DRY_RUN"):
        print(kit["youtube_description"])
        print(f"[compilation] Dry run: {final} kept, nothing uploaded.")
        return

    youtube_id = upload_to_youtube(final, kit)
    print(f"[compilation] Uploaded: https://youtube.com/watch?v={youtube_id}")
    try:
        from googleapiclient.discovery import build
        text = f"{'1 HOUR' if hour else n} {phrase.upper()}"
        thumb = make_thumbnail(final, text, os.path.join(SEG_DIR, "thumb.jpg"))
        set_thumbnail(build("youtube", "v3", credentials=_youtube_credentials()), youtube_id, thumb)
        print(f"[compilation] Thumbnail set: {text}")
    except Exception as e:
        print(f"[compilation] Thumbnail not set (video still uploaded): {e}")

    dna = story["dna"]
    try:
        sb_retry("record story_state", lambda: sb.table("story_state").insert({
            "variant": "long", "theme": "Compilation", "title": kit["youtube_title"],
            "hook": dna.get("hook"), "conflict": dna.get("conflict"),
            "fingerprint": dna.get("fingerprint"), "curve": story["curve"],
            "score": story.get("score"), "tracking_tag": story.get("tracking_tag"),
            "youtube_id": youtube_id}).execute())
        sb_retry("mark queue row rendered", lambda: sb.table("story_queue").update(
            {"rendered": True, "youtube_id": youtube_id, "title": kit["youtube_title"]})
            .eq("id", row["id"]).execute())
    except Exception as e:
        raise SystemExit(f"[compilation] Video is uploaded (id {youtube_id}); only the Supabase "
                         f"bookkeeping failed: {e}")
    print("[compilation] Done.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "preflight":
        preflight()
    elif mode == "segments":
        render_shard()
    elif mode == "one":
        render_one(int(sys.argv[2]))
    elif mode == "publish":
        publish()
    else:
        raise SystemExit(__doc__)
