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
  IG_ACCESS_TOKEN                      — token from Meta's "API setup with Instagram login" flow
                                          (no linked Facebook Page needed)
  IG_USER_ID                           — Instagram account's numeric user ID (from graph.instagram.com/me)

Instagram publishing: the rendered video is uploaded to the private Supabase
Storage bucket "rendered-videos", a short-lived signed URL is generated (the
only way Instagram's Graph API can fetch it — it doesn't accept raw bytes),
Instagram is told to fetch + publish from that URL, and the storage object is
deleted immediately after. Nothing is ever permanently publicly accessible.
"""

import base64
import os
import pickle
import random
import sys
import time

import requests
from supabase import create_client

from app.config import config
from app.models.schema import TaskVideoRequest
from app.services import state as sm
from app.services import task
from app.utils import utils

# AIVidGen reads provider keys from its own config.toml (config.app), not from
# our env vars directly — inject them at runtime instead of writing a file.
if os.environ.get("PEXELS_API_KEY"):
    config.app["pexels_api_keys"] = [os.environ["PEXELS_API_KEY"]]

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
        "subtitle_enabled": True,  # burned-in — Instagram has no auto-caption equivalent for API-published Reels
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


STORAGE_BUCKET = "rendered-videos"
GRAPH_API_BASE = "https://graph.instagram.com"  # Instagram API with Instagram Login (no linked FB Page needed)


def remux_faststart(video_path: str) -> str:
    """
    Moves the MP4 moov atom to the front of the file. Standard ffmpeg/moviepy
    output puts it at the end, which is fine for YouTube but causes Instagram's
    ingestion to sometimes drop the audio track since it starts processing
    before the full file (and its audio index) has downloaded. Fast, lossless
    stream-copy — no re-encoding.
    """
    import subprocess

    out_path = video_path.replace(".mp4", "_faststart.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-c", "copy", "-movflags", "+faststart", out_path],
        check=True, capture_output=True,
    )
    return out_path


def get_signed_video_url(sb, video_path: str, story_id) -> tuple[str, str]:
    """Remuxes for faststart, uploads to the private bucket, returns (storage_path, signed_url)."""
    faststart_path = remux_faststart(video_path)
    storage_path = f"{story_id}.mp4"
    with open(faststart_path, "rb") as f:
        sb.storage.from_(STORAGE_BUCKET).upload(
            storage_path, f.read(), file_options={"content-type": "video/mp4"}
        )
    signed = sb.storage.from_(STORAGE_BUCKET).create_signed_url(storage_path, 3600)
    return storage_path, signed["signedURL"]


def delete_from_storage(sb, storage_path: str):
    try:
        sb.storage.from_(STORAGE_BUCKET).remove([storage_path])
    except Exception as e:
        print(f"[instagram] Cleanup warning (non-fatal): {e}")


def upload_to_instagram(video_url: str, kit: dict) -> str | None:
    """Publishes a Reel via the Instagram API (Instagram Login) using a temporary signed URL."""
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_USER_ID"]

    caption = f"{kit['instagram_caption']}\n\n" + " ".join(
        f"#{h.lstrip('#')}" for h in kit["instagram_hashtags"]
    )

    create_resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "access_token": token,
        },
        timeout=60,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json()["id"]

    # Poll until Instagram finishes downloading/processing the video
    deadline = time.time() + 300
    while time.time() < deadline:
        status_resp = requests.get(
            f"{GRAPH_API_BASE}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Instagram container processing failed")
        time.sleep(10)
    else:
        raise TimeoutError("Instagram container never finished processing")

    publish_resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    publish_resp.raise_for_status()
    return publish_resp.json().get("id")


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

    instagram_id = None
    if os.environ.get("IG_ACCESS_TOKEN") and os.environ.get("IG_USER_ID"):
        storage_path = None
        try:
            storage_path, signed_url = get_signed_video_url(sb, video_path, row["id"])
            instagram_id = upload_to_instagram(signed_url, story["publishing_kit"])
            print(f"[main] Posted to Instagram: media id {instagram_id}")
        except Exception as e:
            print(f"[main] Instagram publish failed (video still rendered locally): {e}")
        finally:
            if storage_path:
                delete_from_storage(sb, storage_path)
    else:
        print("[main] Skipping Instagram — IG_ACCESS_TOKEN / IG_USER_ID not set.")

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
        "instagram_id": instagram_id,
    }).execute()
    sb.table("story_queue").update({
        "rendered": True, "youtube_id": youtube_id, "instagram_id": instagram_id,
    }).eq("id", row["id"]).execute()
    print("[main] Done.")


if __name__ == "__main__":
    main()
