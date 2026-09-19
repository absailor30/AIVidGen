# Pipeline checkpoint — 2026-09-19

A snapshot of how Twisty! StoryVault runs, why it is set up this way, and what
is still open. Update this in place rather than adding dated copies.

## Lanes

| Lane | Cadence | Destinations | Scheduler |
|---|---|---|---|
| `short` | 4x daily | YouTube + Instagram | Cloudflare Worker, 03:00 / 07:00 / 11:15 / 15:00 UTC |
| `long` (generate) | 1x daily | Supabase queue | GitHub cron, `0 13 * * *` |
| `long` (render) | 1x daily | YouTube only | GitHub cron, `30 19 * * *` |
| `illustrated` | manual | YouTube (unlisted) | none — experiment |
| metrics | 1x daily | Supabase | GitHub cron, `30 2 * * *` |
| IG token refresh | weekly | Supabase | GitHub cron, `0 1 * * 1` |

The long lane's cron asks for 19:30 UTC to land near 21:30. GitHub queues
scheduled workflows rather than firing them on time; measured over five
consecutive nights the delay was 2h24, 2h03, 2h11, 2h05, 1h54 — mean 2h07,
spread ±15 min. Re-measure from the run list if the posting time drifts.

**Long-form generation is a separate workflow from long-form rendering**, and
that separation is load-bearing. They shared a slot until run #14, which found
an empty queue, tried to generate inline, and was rate-limited by Groq — a long
story is 17 sequential calls, the heaviest thing on the free tier. Nothing
posted. Now `story_generate_long.yml` fills a buffer of 3 about six hours
ahead, and the render's own top-up step is `continue-on-error` so a 429 in that
fallback can never take down a render that has a story waiting.

## How content is chosen

Themes are weighted by **median views at day 3** — reach, not retention — in
`THEME_WEIGHTS` in `generate_stories_cloud.py`.

An earlier version ranked on average view percentage. The two measures turned
out to be nearly unrelated: Career Sabotage retains best of everything and
reaches almost fewest people. Weighting on retention demoted Marriage &
Infidelity, which is second on reach, and channel-wide daily views fell from
~1750 to ~550 before matched-age data showed what had happened. Re-derive the
weights from `story_metrics` periodically rather than trusting them
indefinitely; medians, not means, because single videos go viral and drag a
mean badly.

Day-3 views are the fair comparison because raw view counts are dominated by
how recently a video was posted — anything older than ~5 days barely moves.

## Things that are true and easy to forget

- **A green run proves the whole Google credential chain.** The access token in
  `GOOGLE_TOKEN_PICKLE_B64` expires hourly, so every run refreshes against the
  live OAuth client before it can upload.
- **`GOOGLE_CLIENT_SECRET_JSON` is read by no code.** It is passed by two
  workflows and referenced in one docstring. Deleting it breaks nothing.
- **The Instagram token lives in Supabase**, in `ig_token`, refreshed weekly.
  The `IG_ACCESS_TOKEN` secret is only the seed for the first refresh and the
  way back in if the stored one ever lapses. Instagram tokens cannot be
  refreshed once expired, which is why the job runs weekly rather than monthly.
- **The Cloudflare Worker's `30 21 * * *` trigger has never fired.** Its other
  four crons work. The long lane runs on GitHub's cron instead.
- **Groq 429s now wait, and say why.** The backoff honours a reported reset up
  to 120s over 6 attempts (it used to clip every wait to 30s, which could not
  ride out a per-minute token cap), and each retry logs Groq's response body.
  A per-minute limit and an exhausted daily quota are both a bare `429` and
  need opposite responses; the body is the only thing that tells them apart.
- **Failures that are not failures.** A run can exit non-zero with the video
  already live on YouTube — that is deliberate, so an Instagram or bookkeeping
  problem cannot pass silently. Read the log before assuming nothing posted.

## Open items

- Delete the Worker's `30 21 * * *` cron trigger in the Cloudflare dashboard.
  Harmless today, a double-post if it ever wakes up.
- Drop the dead `GOOGLE_CLIENT_SECRET_JSON` references from both workflows.
- Point the image provider at a router once its API shape is known. Keep
  Pollinations as the keyless fallback, and parallelise the frame fetches —
  they are currently sequential, which is most of the illustrated lane's
  runtime.
- The illustrated lane has no schedule and posts unlisted. Give it a cron only
  once the look has been judged and its `story_metrics` rows can be compared
  against the short lane.
