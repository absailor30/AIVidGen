"""
Pulls per-video performance into Supabase so content decisions can be made from
evidence instead of the model's own opinion of its work.

Context: every published story already carries a tracking tag encoding its DNA
(theme, hook class, fingerprint, ending), and story_state stores those as
columns beside youtube_id. What has never existed is a single number about how
any of it performed -- so the batch analysis STORY_ENGINE_BIBLE describes
("sort by completion rate, find which variable combos outperformed") has been
unrunnable. This script supplies the missing half.

Two APIs, deliberately separated:

  * YouTube Data API   -- views/likes/comments. Public counters.
  * YouTube Analytics  -- watch time and averageViewPercentage. Owner-only, and
                          needs the yt-analytics.readonly scope, which the
                          upload token was not created with.

The Analytics half is optional at runtime. If the token lacks the scope the
script still collects the Data API numbers, says exactly what is missing, and
exits successfully -- so this is useful the day it lands rather than the day the
token is re-consented.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, GOOGLE_TOKEN_PICKLE_B64.
"""
import base64
import os
import pickle
import sys
from datetime import date

from supabase import create_client

# The Analytics API needs a start date, and "lifetime" is expressed by starting
# before the channel existed. The first story went out 2026-07-13.
ANALYTICS_START = "2026-01-01"
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"

# Data API videos.list caps id lists at 50; the Analytics filter caps at 500.
DATA_BATCH = 50
ANALYTICS_BATCH = 200


def supabase_client():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def youtube_credentials():
    from google.auth.transport.requests import Request as GoogleRequest

    creds = pickle.loads(base64.b64decode(os.environ["GOOGLE_TOKEN_PICKLE_B64"]))
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
    return creds


def published_video_ids(sb) -> list[str]:
    """Every video we have ever put on YouTube, newest first."""
    rows = (sb.table("story_state")
            .select("youtube_id")
            .not_.is_("youtube_id", "null")
            .order("created_at", desc=True)
            .execute().data)
    # Dedupe while preserving order -- a re-run could in principle repeat an id.
    seen, ids = set(), []
    for r in rows:
        vid = r["youtube_id"]
        if vid and vid not in seen:
            seen.add(vid)
            ids.append(vid)
    return ids


def fetch_public_stats(creds, video_ids: list[str]) -> dict[str, dict]:
    """views/likes/comments, keyed by video id."""
    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", credentials=creds)
    out: dict[str, dict] = {}
    for i in range(0, len(video_ids), DATA_BATCH):
        chunk = video_ids[i:i + DATA_BATCH]
        resp = youtube.videos().list(part="statistics", id=",".join(chunk)).execute()
        for item in resp.get("items", []):
            s = item.get("statistics", {})
            out[item["id"]] = {
                # A video with comments or likes disabled simply omits the key.
                "views": int(s["viewCount"]) if "viewCount" in s else None,
                "likes": int(s["likeCount"]) if "likeCount" in s else None,
                "comments": int(s["commentCount"]) if "commentCount" in s else None,
            }
        print(f"[metrics] Public stats: {len(out)}/{len(video_ids)} videos")
    return out


def fetch_retention(creds, video_ids: list[str]) -> dict[str, dict]:
    """Watch time and averageViewPercentage -- the numbers that actually rank content.

    averageViewPercentage is the closest thing the API offers to the bible's
    "completion rate", and it is the one metric here that is comparable across
    videos of different lengths.
    """
    from googleapiclient.discovery import build

    analytics = build("youtubeAnalytics", "v2", credentials=creds)
    today = date.today().isoformat()
    out: dict[str, dict] = {}
    for i in range(0, len(video_ids), ANALYTICS_BATCH):
        chunk = video_ids[i:i + ANALYTICS_BATCH]
        resp = analytics.reports().query(
            ids="channel==MINE",
            startDate=ANALYTICS_START,
            endDate=today,
            dimensions="video",
            metrics="estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
            filters="video==" + ",".join(chunk),
            maxResults=len(chunk),
        ).execute()
        # Column order is described by the response, not assumed.
        cols = [h["name"] for h in resp.get("columnHeaders", [])]
        for row in resp.get("rows", []):
            rec = dict(zip(cols, row))
            out[rec["video"]] = {
                "estimated_minutes_watched": rec.get("estimatedMinutesWatched"),
                "average_view_duration_seconds": rec.get("averageViewDuration"),
                "average_view_percentage": rec.get("averageViewPercentage"),
            }
    print(f"[metrics] Retention: {len(out)}/{len(video_ids)} videos")
    return out


def main():
    sb = supabase_client()
    creds = youtube_credentials()

    video_ids = published_video_ids(sb)
    if not video_ids:
        # Nothing published is not a normal state for this channel; treat it as
        # a signal that something upstream is broken rather than a quiet no-op.
        sys.exit("[metrics] No published videos found in story_state.")
    print(f"[metrics] {len(video_ids)} published videos to collect.")

    stats = fetch_public_stats(creds, video_ids)

    # The upload token predates this script, so the Analytics scope is very
    # likely absent on first run. Check up front and degrade rather than dying
    # three API calls in with a 403 the alert cannot explain.
    scopes = set(getattr(creds, "scopes", None) or [])
    if ANALYTICS_SCOPE in scopes:
        retention = fetch_retention(creds, video_ids)
    else:
        retention = {}
        print(f"[metrics] Skipping retention: token lacks {ANALYTICS_SCOPE}.\n"
              f"[metrics] Re-run the local OAuth flow with that scope added and "
              f"refresh GOOGLE_TOKEN_PICKLE_B64 to collect completion rates.")

    today = date.today().isoformat()
    rows = []
    for vid in video_ids:
        if vid not in stats and vid not in retention:
            continue  # deleted, private, or not ours
        rows.append({"youtube_id": vid, "collected_on": today,
                     **stats.get(vid, {}), **retention.get(vid, {})})

    if not rows:
        sys.exit("[metrics] No metrics returned for any video.")

    # on_conflict makes a same-day re-run idempotent: it refreshes today's
    # snapshot instead of failing on the unique constraint.
    for i in range(0, len(rows), 100):
        sb.table("story_metrics").upsert(
            rows[i:i + 100], on_conflict="youtube_id,collected_on").execute()
    print(f"[metrics] Wrote {len(rows)} snapshots for {today}.")


if __name__ == "__main__":
    main()
