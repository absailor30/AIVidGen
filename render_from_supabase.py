"""
render_from_supabase.py — Headless entry point for GitHub Actions.

Pulls the oldest unclaimed row from Supabase `story_queue`, renders it via
AIVidGen's task pipeline *in-process* (no persistent uvicorn server needed —
fits an ephemeral Actions runner), uploads to YouTube, and records the result
back to Supabase `story_state` for cooldown tracking (STORY_ENGINE_BIBLE §12.4).

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
import pickle
import random
import sys

from supabase import create_client

from app.models.schema import TaskVideoRequest
from app.services import state as sm
from app.services import task
from app.utils import utils

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
VOICE_SPEED = 1.3


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
        "video_terms": random.choice(SATISFYING_KEYWORDS),
        "video_aspect": "9:16",
        "video_language": "en",
        "voice_name": STORY_VOICE,
        "voice_rate": VOICE_SPEED,
        "video_source": "pexels",
        "pexels_api_key": os.environ["PEXELS_API_KEY"],
        "video_count": 1,
        "subtitle_enabled": False,  # rely on YouTube's own auto-captions
    }
    params = TaskVideoRequest(**payload)
    task_id = utils.get_uuid()
    sm.state.update_task(task_id)
    task.start(task_id, params, stop_at="video")

    result = sm.state.get_task(task_id)
    if result.get("state") != 1:  # TASK_STATE_COMPLETE
        print(f"[render] Task did not complete successfully: state={result.get('state')}")
        return None

    videos = result.get("combined_videos") or result.get("videos") or []
    if not videos:
        print("[render] No output video path found.")
        return None
    return videos[0]


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
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": os.environ.get("YOUTUBE_PRIVACY", "private"),
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response.get("id")


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
        sb.table("story_queue").update({"error": "render failed"}).eq("id", row["id"]).execute()
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
    sb.table("story_queue").update({"rendered": True, "youtube_id": youtube_id}).eq("id", row["id"]).execute()
    print("[main] Done.")


if __name__ == "__main__":
    main()
