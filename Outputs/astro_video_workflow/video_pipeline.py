# ============================================================
# video_pipeline.py — MoneyPrinterTurbo API interactions
# ============================================================

import requests
import time
import os
from config import MPT_HOST, OUTPUT_DIR, VIDEO_ASPECT_RATIO, VIDEO_DURATION

def submit_video(subject: str, lang: str, voice: str) -> str:
    """Submit a video generation task. Returns task_id."""
    url = f"{MPT_HOST}/api/v1/videos"

    payload = {
        "video_subject": subject,
        "video_language": lang,
        "voice_name": voice,
        "voice_rate": 1.0,
        "video_aspect": VIDEO_ASPECT_RATIO,
        "video_duration": VIDEO_DURATION,
        "custom_audio_file": "",
        "video_clip_duration": 5,
        "video_count": 1,
        "subtitle_enabled": True,
        "subtitle_position": "bottom",
        "font_size": 60
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    task_id = data.get("task_id") or data.get("id")
    if not task_id:
        raise ValueError(f"No task_id in response: {data}")
    return task_id


def wait_for_video(task_id: str, poll_interval: int = 15, timeout: int = 1800) -> bool:
    """
    Poll until task is done.
    state == 1  → complete
    state == -1 → failed
    Returns True on success, False on failure.
    """
    url = f"{MPT_HOST}/api/v1/tasks/{task_id}"
    elapsed = 0

    while elapsed < timeout:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            state    = data.get("state", 0)
            progress = data.get("progress", 0)
            print(f"  [{task_id}] state={state} progress={progress}%", flush=True)

            if state == 1:
                return True
            if state == -1:
                print(f"  [ERROR] Task {task_id} failed.")
                return False
        except Exception as e:
            print(f"  [WARN] Poll error: {e}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"  [TIMEOUT] Task {task_id} did not complete in {timeout}s.")
    return False


def download_video(task_id: str, filename: str) -> str:
    """Download the finished video. Returns local file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    url = f"{MPT_HOST}/api/v1/download/tasks/{task_id}/final-1.mp4"
    dest = os.path.join(OUTPUT_DIR, filename)

    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return dest
