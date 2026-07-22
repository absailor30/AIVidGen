"""
telegram_bot.py — lets the user trigger/check the Twisty! StoryVault
pipeline from Telegram, via a GitHub Actions cron poller (no server to host).

Commands (must come from TELEGRAM_CHAT_ID, all others ignored):
  /render or /run  -> triggers story_render.yml via workflow_dispatch
  /status          -> replies with unclaimed queue depth + last run result

Required environment variables:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
  GH_DISPATCH_TOKEN (a GitHub token with 'actions: write' on this repo),
  SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

import os

import requests
from supabase import create_client

REPO = "absailor30/AIVidGen"
TG_API = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"
CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])


def send(text: str):
    requests.post(f"{TG_API}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=15)


def trigger_render():
    resp = requests.post(
        f"https://api.github.com/repos/{REPO}/actions/workflows/story_render.yml/dispatches",
        headers={
            "Authorization": f"Bearer {os.environ['GH_DISPATCH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
        json={"ref": "main"},
        timeout=15,
    )
    if resp.status_code == 204:
        send("Render triggered. Check back in a few minutes with /status.")
    else:
        send(f"Failed to trigger render: {resp.status_code} {resp.text[:200]}")


def report_status():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    unclaimed = sb.table("story_queue").select("id", count="exact").is_("claimed_at", "null").execute().count

    runs_resp = requests.get(
        f"https://api.github.com/repos/{REPO}/actions/workflows/story_render.yml/runs?per_page=1",
        headers={"Authorization": f"Bearer {os.environ['GH_DISPATCH_TOKEN']}"},
        timeout=15,
    )
    runs = runs_resp.json().get("workflow_runs", [])
    if runs:
        r = runs[0]
        last = f"{r['status']}/{r['conclusion']} at {r['created_at']}"
    else:
        last = "unknown"

    send(f"Queue: {unclaimed} unclaimed stories.\nLast render run: {last}")


def main():
    resp = requests.get(f"{TG_API}/getUpdates", timeout=30)
    updates = resp.json().get("result", [])

    max_update_id = None
    for u in updates:
        max_update_id = u["update_id"]
        msg = u.get("message", {})
        if msg.get("chat", {}).get("id") != CHAT_ID:
            continue
        text = (msg.get("text") or "").strip().lower()
        if text in ("/render", "/run"):
            trigger_render()
        elif text == "/status":
            report_status()

    if max_update_id is not None:
        requests.get(f"{TG_API}/getUpdates", params={"offset": max_update_id + 1}, timeout=30)


if __name__ == "__main__":
    main()
