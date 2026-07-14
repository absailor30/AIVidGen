"""
render_from_supabase.py — Headless entry point for GitHub Actions.

Pulls the oldest unclaimed row from Supabase `story_queue`, renders it via
AIVidGen's task pipeline *in-process* (no persistent uvicorn server needed —
fits an ephemeral Actions runner), uploads to YouTube, and records the result
back to Supabase `story_state` for cooldown tracking (STORY_ENGINE_BIBLE §12.4).

YouTube only for now — Instagram publishing was removed to reduce variables
while debugging a render-stage audio bug on the Linux CI runner.

Required environment variables:
  SUPABASE_URL, SUPABASE_SERVICE_KEY   — from the Supabase dashboard
  PEXELS_API_KEY                       — https://www.pexels.com/api/
  GOOGLE_CLIENT_SECRET_JSON            — contents of your OAuth client_secret.json
  GOOGLE_TOKEN_PICKLE_B64              — base64 of a locally-generated token.pickle
                                          (run youtube_uploader.py once locally first)
  YOUTUBE_PRIVACY                      — optional, default "private"
"""

import base64
import os
import shutil
import pickle
import random

# Force the system ffmpeg (installed via apt-get in the workflow) instead of
# imageio_ffmpeg's bundled per-platform binary. Local Windows testing (which
# had working audio, verified with ffprobe) used ffmpeg-win-x86_64-v7.1.exe;
# the broken CI runs used ffmpeg-linux-x86_64-v7.0.2 — testing whether that
# specific bundled Linux build has an audio-muxing regression.
_system_ffmpeg = shutil.which("ffmpeg")
if _system_ffmpeg:
    os.environ["IMAGEIO_FFMPEG_EXE"] = _system_ffmpeg
import sys

from supabase import create_client

# Diagnostic patch: FFMPEG_VideoWriter only includes audio in the ffmpeg
# command if `audiofile is not None` (a path to a pre-encoded temp audio
# file written just before this). ffmpeg itself runs with -loglevel error,
# which would silently hide a warning about a missing/empty/corrupt audio
# input. Logging the actual path + whether it exists + its size right here
# tells us definitively whether the temp audio file write step is the bug.
import moviepy.video.io.ffmpeg_writer as _ffmpeg_writer
_original_init = _ffmpeg_writer.FFMPEG_VideoWriter.__init__

def _patched_init(self, filename, size, fps, audiofile=None, **kwargs):
    if audiofile is not None:
        exists = os.path.exists(audiofile)
        size_bytes = os.path.getsize(audiofile) if exists else None
        print(f"[audio-debug] FFMPEG_VideoWriter audiofile={audiofile!r} exists={exists} size_bytes={size_bytes}")
    else:
        print("[audio-debug] FFMPEG_VideoWriter audiofile=None (no audio will be muxed)")
    _original_init(self, filename, size, fps, audiofile=audiofile, **kwargs)

_ffmpeg_writer.FFMPEG_VideoWriter.__init__ = _patched_init

from app.config import config
from app.models.schema import TaskVideoRequest
from app.services import state as sm
from app.services import task
from app.utils import utils

# AIVidGen reads provider keys from its own config.toml (config.app), not from
# our env vars directly — inject them at runtime instead of writing a file.
if os.environ.get("PEXELS_API_KEY"):
    config.app["pexels_api_keys"] = [os.environ["PEXELS_API_KEY"]]

# "Oddly satisfying" pool kept for optional use, but story-relevant keywords
# (the story's own §9 keyword string) are the default — see render_video().
SATISFYING_BACKGROUND = False
SATISFYING_KEYWORDS = [
    "slime asmr satisfying",
    "kinetic sand cutting satisfying",
    "soap cutting satisfying asmr",
    "pressure washing dirty surface satisfying",
    "paint pouring satisfying asmr",
    "cake icing smooth satisfying",
    "glass cutting oddly satisfying",
    "satisfying compilation asmr",
]

STORY_VOICE = "en-US-JennyNeural"
VOICE_SPEED = 1.4  # also trims render duration/file size


def supabase_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def claim_next_story(sb, theme: str | None = None):
    query = sb.table("story_queue").select("*").is_("claimed_at", "null").order("id").limit(1)
    if theme:
        query = query.eq("theme", theme)
    rows = query.execute().data
    if not rows:
        return None
    row = rows[0]
    sb.table("story_queue").update({"claimed_at": "now()"}).eq("id", row["id"]).execute()
    return row


def render_video(story: dict) -> str | None:
    payload = {
        "video_subject": story["title"],
        "video_script": story["story"],
        "video_terms": (
            random.sample(SATISFYING_KEYWORDS, k=min(4, len(SATISFYING_KEYWORDS)))
            if SATISFYING_BACKGROUND else story["keywords"]
        ),
        "video_aspect": "9:16",
        "video_language": "en",
        "voice_name": STORY_VOICE,
        "voice_rate": VOICE_SPEED,
        "video_source": "pexels",
        "pexels_api_key": os.environ["PEXELS_API_KEY"],
        "video_count": 1,
        "video_clip_duration": 3,
        "bgm_type": "",  # disabled temporarily to eliminate it as a variable in the audio-bug debugging
        "subtitle_enabled": True,  # burned-in — Instagram has no auto-caption equivalent for API-published Reels
        # Must be an actual filename in resource/fonts/ — "Arial" (no such file)
        # crashed the render thread silently (AIVidGen doesn't mark it failed on
        # an uncaught exception, it just hangs at whatever progress it had).
        "font_name": "BeVietnamPro-Medium.ttf",
        "text_fore_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 2,
    }
    params = TaskVideoRequest(**payload)
    task_id = utils.get_uuid()
    sm.state.update_task(task_id)

    # Run inside a thread, matching exactly how the real REST server executes
    # this (TaskManager.execute_task/run_task) rather than calling it directly
    # on the main thread — testing whether that's what's dropping audio on
    # the Linux CI runner (confirmed via ffprobe: local run via the actual
    # server has audio, this script's direct main-thread call does not).
    import threading
    render_thread = threading.Thread(target=task.start, args=(task_id, params), kwargs={"stop_at": "video"})
    render_thread.start()
    render_thread.join()

    result = sm.state.get_task(task_id)
    if result.get("state") != 1:  # TASK_STATE_COMPLETE
        print(f"[render] Task did not complete successfully: state={result.get('state')}")
        return None

    videos = result.get("combined_videos") or result.get("videos") or []
    if not videos:
        print("[render] No output video path found.")
        return None

    _log_stream_diagnostics(videos[0])
    return videos[0]


def _log_stream_diagnostics(video_path: str):
    """Prints whether the rendered file actually has an audio stream, so we
    can tell a render bug from a delivery bug directly in the CI log instead
    of inferring it from what YouTube/Instagram show afterward."""
    import subprocess
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg_exe, "-i", video_path], capture_output=True, text=True
    )
    stream_lines = [line.strip() for line in result.stderr.splitlines() if "Stream #" in line]
    has_audio = any("Audio:" in line for line in stream_lines)
    print(f"[render] ffmpeg used: {ffmpeg_exe}")
    print(f"[render] Streams in rendered file:")
    for line in stream_lines:
        print(f"[render]   {line}")
    print(f"[render] Has audio stream: {has_audio}")


def _youtube_credentials():
    from google.auth.transport.requests import Request as GoogleRequest

    creds = pickle.loads(base64.b64decode(os.environ["GOOGLE_TOKEN_PICKLE_B64"]))
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
    return creds


def upload_to_youtube(video_path: str, kit: dict) -> str | None:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = _youtube_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": kit["youtube_title"][:100],
            "description": kit["youtube_description"][:5000],
            "tags": kit["youtube_tags"],
            "categoryId": os.environ.get("YOUTUBE_CATEGORY_ID", "24"),  # 24 = Entertainment
        },
        "status": {
            "privacyStatus": os.environ.get("YOUTUBE_PRIVACY", "private"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response.get("id")

    playlist_id = os.environ.get("YOUTUBE_PLAYLIST_ID")
    if playlist_id and video_id:
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            ).execute()
        except Exception as e:
            print(f"[render] Failed to add to playlist (video still uploaded): {e}")

    return video_id


def main():
    theme = sys.argv[1] if len(sys.argv) > 1 else None
    sb = supabase_client()

    row = claim_next_story(sb, theme)
    if not row:
        print(f"[main] No queued stories{f' for theme {theme}' if theme else ''}. Exiting.")
        return

    story = row["payload"]
    print(f"[main] Rendering: {story['title']} ({story['theme']})")

    video_path = render_video(story)
    if not video_path:
        # Release the claim so the next run retries this story instead of leaving it stuck.
        sb.table("story_queue").update({"error": "render failed", "claimed_at": None}).eq("id", row["id"]).execute()
        sys.exit(1)

    youtube_id = None
    try:
        youtube_id = upload_to_youtube(video_path, story["publishing_kit"])
        print(f"[main] Uploaded: https://youtube.com/watch?v={youtube_id}")
    except Exception as e:
        print(f"[main] YouTube upload failed (video still rendered locally): {e}")

    dna = story["dna"]
    sb.table("story_state").insert({
        "theme": story["theme"],
        "title": story["title"],
        "hook": dna.get("hook"),
        "relationship": dna.get("relationship"),
        "conflict": dna.get("conflict"),
        "emotion": dna.get("emotion"),
        "payoff": dna.get("payoff"),
        "fingerprint": dna.get("fingerprint"),
        "curve": story["curve"],
        "score": story["score"],
        "tracking_tag": story["tracking_tag"],
        "youtube_id": youtube_id,
    }).execute()
    sb.table("story_queue").update({
        "rendered": True, "youtube_id": youtube_id,
    }).eq("id", row["id"]).execute()
    print("[main] Done.")


if __name__ == "__main__":
    main()
