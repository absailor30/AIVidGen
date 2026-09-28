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
from datetime import date, datetime, timezone

from supabase import create_client

# The Analytics API needs a start date, and "lifetime" is expressed by starting
# before the channel existed. The first story went out 2026-07-13.
ANALYTICS_START = "2026-01-01"
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"

# Data API videos.list caps id lists at 50; the Analytics filter caps at 500.
DATA_BATCH = 50
ANALYTICS_BATCH = 200

# Retention curves are captured once per video, at this age. Three days is the
# same age the matched-age analysis compares everything at, so a curve lines up
# with the averages already in story_metrics instead of mixing a day-1 curve
# with a day-40 one. It is also late enough that a Short has most of its views.
CURVE_MIN_AGE_DAYS = 3

# Hard ceiling on curve requests per run. The report takes ONE video per call
# (Google's reference: it "does not support the ability to specify multiple
# values for the video filter"), so the first run backfills the whole catalogue
# at one request each. This bounds that run; anything left over is picked up
# the next day.
#
# Sized against the workflow's 15-minute timeout, not the API: the existing
# snapshot takes under a minute, and 150 sequential calls stays around 6-7
# minutes even on a slow day. A timeout would kill the whole job, snapshot
# write included, so the ~230-video backfill spans two runs instead.
CURVE_MAX_PER_RUN = 150


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


def videos_needing_curves(sb) -> list[tuple[str, int]]:
    """(youtube_id, age_days) for videos old enough that have no curve yet.

    A video gets exactly one curve. It is re-requested only while the report
    comes back empty -- YouTube withholds retention for videos with too few
    views -- so a slow starter is retried daily until it qualifies.
    """
    now = datetime.now(timezone.utc)
    rows = (sb.table("story_state")
            .select("youtube_id,created_at")
            .not_.is_("youtube_id", "null")
            .execute().data)
    have = {r["youtube_id"] for r in
            sb.table("story_retention").select("youtube_id").execute().data}
    out, seen = [], set()
    for r in rows:
        vid = r["youtube_id"]
        if not vid or vid in seen or vid in have:
            continue
        seen.add(vid)
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        age = (now - created).days
        if age >= CURVE_MIN_AGE_DAYS:
            out.append((vid, age))
    # Youngest first: they are the ones closest to the intended day-3 capture,
    # so if the per-run cap bites, the backlog is what waits, not fresh videos.
    out.sort(key=lambda t: t[1])
    return out


def fetch_retention_curve(analytics, video_id: str) -> list[dict]:
    """The 100-point audience retention curve for one video.

    This is what averageViewPercentage cannot tell us: not how much of a story
    people watched on average, but WHERE they left. The structure analysis
    found the median viewer gone at 62% of the story -- inside the betrayal
    beat, before the payoff -- and only the curve can say whether that is a
    steady slide or a cliff at one sentence.
    """
    resp = analytics.reports().query(
        ids="channel==MINE",
        startDate=ANALYTICS_START,
        endDate=date.today().isoformat(),
        dimensions="elapsedVideoTimeRatio",
        metrics="audienceWatchRatio,relativeRetentionPerformance",
        filters=f"video=={video_id}",
    ).execute()
    cols = [h["name"] for h in resp.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in resp.get("rows", [])]


def collect_curves(sb, creds) -> tuple[int, int, int]:
    """Capture curves for every eligible video. Returns (captured, empty, failed).

    Deliberately runs AFTER the daily snapshot is written, and one video's
    failure never stops the rest: curves are the new, optional half of this
    job, and must not be able to cost the snapshot that already works.
    """
    from googleapiclient.discovery import build

    pending = videos_needing_curves(sb)
    if not pending:
        print("[metrics] Curves: nothing new to capture.")
        return 0, 0, 0
    if len(pending) > CURVE_MAX_PER_RUN:
        print(f"[metrics] Curves: {len(pending)} pending, capturing the youngest "
              f"{CURVE_MAX_PER_RUN} this run; the rest follow tomorrow.")
        pending = pending[:CURVE_MAX_PER_RUN]

    analytics = build("youtubeAnalytics", "v2", credentials=creds)
    today = date.today().isoformat()
    captured = empty = failed = 0
    for vid, age in pending:
        try:
            points = fetch_retention_curve(analytics, vid)
        except Exception as e:
            failed += 1
            print(f"[metrics] Curve failed for {vid}: {str(e)[:160]}")
            continue
        if not points:
            empty += 1          # below YouTube's view threshold; retry tomorrow
            continue
        rows = [{
            "youtube_id": vid,
            "elapsed_ratio": p.get("elapsedVideoTimeRatio"),
            "audience_watch_ratio": p.get("audienceWatchRatio"),
            "relative_retention_performance": p.get("relativeRetentionPerformance"),
            "age_days": age,
            "collected_on": today,
        } for p in points]
        sb.table("story_retention").upsert(
            rows, on_conflict="youtube_id,elapsed_ratio").execute()
        captured += 1

    print(f"[metrics] Curves: {captured} captured, {empty} not yet available "
          f"(too few views), {failed} failed, of {len(pending)} eligible.")
    return captured, empty, failed


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

    # Curves need the same Analytics scope as the averages. Without it there
    # is nothing to attempt, and the scope message above already said so.
    if ANALYTICS_SCOPE in scopes:
        captured, empty, failed = collect_curves(sb, creds)
        # Partial failure is logged and tolerated. Total failure is not: a
        # collector that attempts curves every day and silently lands none is
        # exactly the kind of quiet breakage this job exists to prevent.
        if failed and not captured and not empty:
            sys.exit(f"[metrics] Every retention curve request failed ({failed}). "
                     f"The daily snapshot above was still written.")


if __name__ == "__main__":
    main()
