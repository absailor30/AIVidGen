"""
Keeps the Instagram access token alive so posting never lapses again.

Instagram long-lived tokens last 60 days. On 2026-09-11 one expired silently and
every Reel failed for a day before anyone noticed -- the YouTube half kept
working, so the channel looked healthy.

Two facts from Meta's refresh_access_token reference drive the whole design:

  * a token can only be refreshed while it is still VALID (and at least 24h old)
  * once it expires it can NEVER be refreshed -- recovery means going back to
    the app dashboard by hand

So a missed refresh window is unrecoverable, not merely late. This runs weekly
rather than near the deadline: ~8 attempts before a token could lapse, and any
single failure has weeks of slack behind it. It also shouts while there is still
time to act, instead of after the fact.

Storage is Supabase, not a GitHub secret. Writing a secret back would need a PAT
with "Secrets: read and write" over the whole repo, which is a far heavier
credential than this job deserves; the pipeline already trusts Supabase with
everything else. The IG_ACCESS_TOKEN env var stays the seed for the first run
and the fallback if the stored token ever lapses.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, IG_ACCESS_TOKEN (seed/fallback).
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from supabase import create_client

REFRESH_URL = "https://graph.instagram.com/refresh_access_token"

# Meta refuses to refresh a token younger than 24 hours. Weekly scheduling means
# this is only ever hit right after a manual rotation, and skipping is correct
# there -- the fresh token already has ~60 days on it.
MIN_TOKEN_AGE = timedelta(hours=24)

# Loud warning threshold. At weekly cadence, fewer than this many days left
# means several refreshes have already failed silently.
ALERT_BELOW_DAYS = 21


def _stored(sb) -> dict | None:
    rows = sb.table("ig_token").select("*").eq("id", 1).execute().data
    return rows[0] if rows else None


def _parse(ts: str) -> datetime:
    # Postgres returns ISO 8601; normalise the trailing Z that fromisoformat
    # rejects on older Pythons.
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def current_token(sb) -> tuple[str, datetime | None, str]:
    """The token to refresh, and where it came from.

    Prefers the stored token, but only while it is actually usable. If the
    stored one has expired, a freshly pasted IG_ACCESS_TOKEN is the only way
    back, so the env var wins -- otherwise a single missed window would wedge
    this job permanently against a token it can never refresh.
    """
    env_token = (os.environ.get("IG_ACCESS_TOKEN") or "").strip()
    row = _stored(sb)
    now = datetime.now(timezone.utc)

    if row:
        expires_at = _parse(row["expires_at"])
        if expires_at > now:
            return row["access_token"], _parse(row["refreshed_at"]), "supabase"
        print(f"[ig-token] Stored token expired at {expires_at:%Y-%m-%d}; "
              f"falling back to IG_ACCESS_TOKEN.")

    if not env_token:
        sys.exit("[ig-token] No usable token: nothing stored and IG_ACCESS_TOKEN is unset.")
    return env_token, None, "env"


def refresh(token: str) -> tuple[str, int]:
    resp = requests.get(
        REFRESH_URL,
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=30,
    )
    if not resp.ok:
        # Meta explains itself in the body; a bare status here would be as
        # unactionable as the 400 that hid the original expiry.
        sys.exit(f"[ig-token] Refresh failed: HTTP {resp.status_code} "
                 f"{(resp.text or '').strip()[:400]}")
    data = resp.json()
    if "access_token" not in data:
        sys.exit(f"[ig-token] Refresh returned no access_token: {data}")
    return data["access_token"], int(data.get("expires_in", 0))


def main():
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    token, refreshed_at, source = current_token(sb)
    now = datetime.now(timezone.utc)
    print(f"[ig-token] Using token from {source}.")

    if refreshed_at and now - refreshed_at < MIN_TOKEN_AGE:
        # Not an error: the token was rotated in the last day and is already
        # near its full 60-day life.
        print(f"[ig-token] Token refreshed {now - refreshed_at} ago, under the "
              f"24h minimum. Nothing to do.")
        return

    new_token, expires_in = refresh(token)
    expires_at = now + timedelta(seconds=expires_in)
    days = expires_in / 86400

    sb.table("ig_token").upsert({
        "id": 1,
        "access_token": new_token,
        "expires_at": expires_at.isoformat(),
        "refreshed_at": now.isoformat(),
    }).execute()

    print(f"[ig-token] Refreshed. Valid until {expires_at:%Y-%m-%d} ({days:.0f} days).")

    if days < ALERT_BELOW_DAYS:
        # Weekly cadence means this should never happen without prior failures.
        sys.exit(f"[ig-token] WARNING: only {days:.0f} days of validity after a "
                 f"refresh. Expected ~60. Check the token in the Meta dashboard.")


if __name__ == "__main__":
    main()
