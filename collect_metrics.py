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


def google_call(label: str, request, attempts: int = 4):
    """Execute a Google API request, retrying transient server-side failures.

    Run #26 (2026-10-05) died on a single YouTube Analytics 500 backendError
    ("Internal error encountered.") -- Google's side, gone on the next try --
    and because that call comes before the snapshot write, the whole day's
    metrics were lost. 5xx and 429 are retried with 5/10/20s backoff; any
    other error (a 403 for a missing scope, a 400 for a bad query) is a real
    problem and is raised at once.
    """
    import time
    from googleapiclient.errors import HttpError
    delay = 5.0
    for attempt in range(attempts):
        try:
            return request.execute()
        except HttpError as e:
            status = getattr(e.resp, "status", 0)
            if not (status >= 500 or status == 429) or attempt == attempts - 1:
                raise
            print(f"[metrics] {label}: HTTP {status}, retrying in {delay:.0f}s "
                  f"({attempt + 1}/{attempts - 1})")
            time.sleep(delay)
            delay *= 2


def fetch_public_stats(creds, video_ids: list[str]) -> dict[str, dict]:
    """views/likes/comments, keyed by video id."""
    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", credentials=creds)
    out: dict[str, dict] = {}
    for i in range(0, len(video_ids), DATA_BATCH):
        chunk = video_ids[i:i + DATA_BATCH]
        resp = google_call("public stats",
                           youtube.videos().list(part="statistics", id=",".join(chunk)))
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
        resp = google_call("retention averages", analytics.reports().query(
            ids="channel==MINE",
            startDate=ANALYTICS_START,
            endDate=today,
            dimensions="video",
            metrics="estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
            filters="video==" + ",".join(chunk),
            maxResults=len(chunk),
        ))
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
    resp = google_call(f"curve {video_id}", analytics.reports().query(
        ids="channel==MINE",
        startDate=ANALYTICS_START,
        endDate=date.today().isoformat(),
        dimensions="elapsedVideoTimeRatio",
        metrics="audienceWatchRatio,relativeRetentionPerformance",
        filters=f"video=={video_id}",
    ))
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


# --- Instagram ---------------------------------------------------------------
IG_GRAPH = "https://graph.instagram.com"

# Reels this young are snapshotted daily. Older ones barely move, and keeping
# the call count down matters: the Instagram API's per-account hourly limit is
# far smaller than YouTube's quota.
IG_MAX_AGE_DAYS = 30

# Requested if the account is allowed them. Insights availability depends on
# account size and Meta's rollouts, and the names have changed before ("plays"
# became "views" in 2025), so none of these is assumed: each is probed once per
# run and only the ones Meta accepts are used for the rest.
IG_INSIGHT_METRICS = ["views", "reach", "shares", "saved", "total_interactions",
                      "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]


def ig_token(sb) -> str | None:
    """Same rule as the renderer: the auto-refreshed token if unexpired, else env."""
    env = (os.environ.get("IG_ACCESS_TOKEN") or "").strip() or None
    try:
        rows = sb.table("ig_token").select("access_token,expires_at").eq("id", 1).execute().data
    except Exception as e:
        print(f"[metrics] IG: could not read stored token ({str(e)[:80]}); using env.")
        return env
    if rows:
        exp = datetime.fromisoformat(rows[0]["expires_at"].replace("Z", "+00:00"))
        if exp > datetime.now(timezone.utc):
            return rows[0]["access_token"]
    return env


def _ig_get(path: str, token: str, **params) -> dict:
    import requests
    resp = requests.get(f"{IG_GRAPH}/{path}", params={**params, "access_token": token}, timeout=30)
    body = resp.json() if resp.content else {}
    if not resp.ok:
        err = body.get("error", {}) if isinstance(body, dict) else {}
        raise RuntimeError(f"HTTP {resp.status_code} code {err.get('code')}: "
                           f"{str(err.get('message') or resp.text)[:160]}")
    return body


def _is_rate_limited(e: Exception) -> bool:
    return any(f"code {c}:" in str(e) for c in (4, 17, 32, 613))


def probe_ig_metrics(media_id: str, token: str) -> list[str]:
    """Which insight metrics this account may read, tested one at a time.

    One request per metric, once per run. Asking for all of them together
    fails the whole request if Meta rejects any single name, which would lose
    the ones that do work.
    """
    ok = []
    for m in IG_INSIGHT_METRICS:
        try:
            _ig_get(f"{media_id}/insights", token, metric=m)
            ok.append(m)
        except Exception as e:
            print(f"[metrics] IG: insight '{m}' unavailable ({str(e)[:110]})")
            if _is_rate_limited(e):
                break
    print(f"[metrics] IG: usable insights: {ok or 'none -- likes/comments only'}")
    return ok


def collect_instagram(sb) -> tuple[int, int]:
    """Snapshot recent Reels into ig_metrics. Returns (written, failed).

    Never raises: Instagram is the optional half of this job. A missing token,
    an insights restriction or a rate limit costs Instagram numbers, not the
    YouTube snapshot written before this runs.
    """
    token = ig_token(sb)
    if not token:
        print("[metrics] IG: no token; skipping Instagram.")
        return 0, 0
    now = datetime.now(timezone.utc)
    rows = (sb.table("story_state").select("instagram_id,created_at")
            .not_.is_("instagram_id", "null").execute().data)
    ids = []
    for r in rows:
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        if r["instagram_id"] and (now - created).days <= IG_MAX_AGE_DAYS:
            ids.append(r["instagram_id"])
    ids = list(dict.fromkeys(ids))
    if not ids:
        print("[metrics] IG: no recent Reels.")
        return 0, 0

    metrics = probe_ig_metrics(ids[0], token)
    fields = "like_count,comments_count"
    if metrics:
        fields += f",insights.metric({','.join(metrics)})"

    today = date.today().isoformat()
    out, failed = [], 0
    for mid in ids:
        try:
            d = _ig_get(mid, token, fields=fields)
        except Exception as e:
            failed += 1
            print(f"[metrics] IG: {mid} failed ({str(e)[:110]})")
            if _is_rate_limited(e):
                print("[metrics] IG: rate limited; stopping, the rest follow tomorrow.")
                break
            continue
        ins = {}
        for item in (d.get("insights") or {}).get("data", []):
            vals = item.get("values") or [{}]
            ins[item["name"]] = vals[0].get("value")
        out.append({"instagram_id": mid, "collected_on": today,
                    "likes": d.get("like_count"), "comments": d.get("comments_count"),
                    "metrics": ins})
    for i in range(0, len(out), 100):
        sb.table("ig_metrics").upsert(out[i:i + 100],
                                      on_conflict="instagram_id,collected_on").execute()
    print(f"[metrics] IG: wrote {len(out)} Reel snapshots, {failed} failed, "
          f"of {len(ids)} under {IG_MAX_AGE_DAYS} days old.")
    return len(out), failed


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
    retention_failed = False
    if ANALYTICS_SCOPE in scopes:
        try:
            retention = fetch_retention(creds, video_ids)
        except Exception as e:
            # Keep going: views/likes/comments are still worth recording, and
            # the job still exits non-zero at the end so the alert fires.
            retention, retention_failed = {}, True
            print(f"[metrics] Retention averages failed after retries ({str(e)[:160]}); "
                  f"writing public stats without them.")
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

    curves_all_failed = False
    # Curves need the same Analytics scope as the averages. Without it there
    # is nothing to attempt, and the scope message above already said so.
    if ANALYTICS_SCOPE in scopes:
        captured, empty, failed = collect_curves(sb, creds)
        # Partial failure is logged and tolerated. Total failure is not: a
        # collector that attempts curves every day and silently lands none is
        # exactly the kind of quiet breakage this job exists to prevent.
        if failed and not captured and not empty:
            curves_all_failed = True

    # Instagram last, so nothing above can be lost to it.
    try:
        collect_instagram(sb)
    except Exception as e:
        print(f"[metrics] IG: collection crashed ({str(e)[:160]}); YouTube data above is saved.")

    if retention_failed:
        sys.exit("[metrics] YouTube Analytics failed after retries; today's snapshot "
                 "was written without watch time or retention.")
    if ANALYTICS_SCOPE in scopes and curves_all_failed:
        sys.exit("[metrics] Every retention curve request failed. "
                 "The daily snapshot above was still written.")


if __name__ == "__main__":
    main()
