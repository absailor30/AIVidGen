# Pipeline checkpoint — 2026-10-24

A snapshot of how Twisty! StoryVault runs, why it is set up this way, and what
is still open. Update this in place rather than adding dated copies.

## Lanes

| Lane | Cadence | Destinations | Scheduler |
|---|---|---|---|
| `short` | 3x daily | YouTube + Instagram | Cloudflare Worker: 12:45 / 15:45 / 19:45 UTC (18:15 / 21:15 / 01:15 IST) |
| `cartoon` | 1x daily | YouTube + Instagram | Worker's 17:45 UTC (23:15 IST) slot, handed over by `.github/cartoon_slots` |
| `long` (generate) | 1x daily | Supabase queue | GitHub cron, `0 13 * * *` |
| `long` (render) | 1x daily | YouTube only | Cloudflare Worker, `30 21 * * *` (03:00 IST) |
| `trial` | paused | Instagram trial Reels | none: the account was below the follower minimum |
| `illustrated` | manual | YouTube (unlisted) | none, experiment |
| metrics | 1x daily | Supabase | GitHub cron, `30 2 * * *` |
| IG token refresh | weekly | Supabase | GitHub cron, `0 1 * * 1` |

Slot times are set in the Cloudflare dashboard (the Worker's Cron Triggers),
moved to the IST evening on 2026-10-06 from Instagram's audience insights. The
long-form cron must stay in `LONG_CRONS` in `cloudflare_worker.js`.

### The cartoon lane

A Short drawn instead of filmed: each beat of the story becomes an animated
scene (setting, cast with expressions, phone / call / document props) with
word-synced captions, rendered by HyperFrames (headless Chrome + ffmpeg) in
`cartoon_render.py` + `cartoon/template.html`. Groq storyboards each story;
a keyword plan takes over when Groq is out of quota. Narration is Jenny at
1.4x, music levelled like the stock lane and scaled by 0.9.

- It draws from the regular `short` queue and records `variant = cartoon` in
  `story_state`, so its numbers can be compared with stock footage.
- `.github/cartoon_slots` decides which Worker slots it takes: `*T17` means the
  17:45 UTC slot every day; a dated line (`2026-10-10T19`) takes one slot once.
- `story_render.yml` takes `variant` and `dry_run` inputs. A dry run renders,
  posts nothing, returns the story to the queue, attaches the video to the run,
  and pushes it to the `previews` branch.
- **A cloned voice was tried and rejected** (2026-10-10). Chatterbox (MIT)
  cloned the owner's voice from a sample in the private bucket
  (`rendered-videos/voice/`), but the result was judged far worse than Jenny.
  `voice_clone.py` and `voice_test.yml` remain on main, unused.

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
- **YouTube can drop an upload mid-transfer** with `410 Gone` (run #361). The
  upload now restarts with a fresh session up to 3 times on 404/410/429/5xx;
  nothing publishes until an upload completes, so a retry cannot double-post.
- **Music is levelled per track** to -32 LUFS (`_pick_bgm`); "too loud" was
  one track being much hotter than the rest, not the overall volume.
- **Groq's free tier is 200k tokens a day** and a busy day uses nearly all of
  it. Generation fails fast on a daily-quota 429 and the render still posts
  from the queue; a cartoon storyboard falls back to the keyword plan.
- **Groq 429s now wait, and say why.** The backoff honours a reported reset up
  to 120s over 6 attempts (it used to clip every wait to 30s, which could not
  ride out a per-minute token cap), and each retry logs Groq's response body.
  A per-minute limit and an exhausted daily quota are both a bare `429` and
  need opposite responses; the body is the only thing that tells them apart.
- **Failures that are not failures.** A run can exit non-zero with the video
  already live on YouTube — that is deliberate, so an Instagram or bookkeeping
  problem cannot pass silently. Read the log before assuming nothing posted.

## Theme experiment (2026-10-24 to 2026-11-23)

Four new themes (Neighbour & Roommate Conflicts, Family Money & Borrowed Cash,
Bridesmaid & Wedding Party Drama, Holiday Dinner Blow-Up) run at weight 2 each,
8 of 20, in shorts and long-form alike. **Do not change `THEME_WEIGHTS` before
the review**: moving them mid-run is what makes the comparison unreadable. At
the review, compare median day-3 views and subs per 1k views by theme from
`story_metrics` (shorts: about 12 videos per new theme; long-form: about 3, so
long-form is a quality check only), then cut the losers and re-weight.
Confounders to remember: thumbnails went live on long-form 2026-10-23, the
cartoon lane runs daily, and the hook change merged 2026-10-15.

## Added since 2026-10-11

- **Subscriber and audience tracking.** `collect_metrics.py` records per-video
  `subscribers_gained/lost/shares` in `story_metrics` and fills
  `channel_breakdown` (daily, traffic source, subscribed status, country, each
  split Shorts vs long-form, last 28 days). First read: ~1.2% of Shorts views
  come from subscribers; Shorts views are almost all the Shorts feed; long-form
  gets almost no search or channel-page views. Shorts ~1.0 subs per 1k views,
  long-form ~3.4; US ~65% of audience.
- **Long-form thumbnails.** `thumbnail.py` takes the sharpest of 12 frames from
  the finished video (8-60% in), darkens the bottom and adds 3-5 words of
  story-based text (Groq, falls back to title words). `upload_to_youtube`
  sets it for the `long` variant only, best effort (log line "Thumbnail not
  set" if the channel is not phone-verified). **Not yet seen on a real upload**;
  check the first 21:30 UTC long-form after 2026-10-23.
- **Audit (2026-10-23).** Long-form is the critical failure (median 13 views,
  60% leave in the first 10%). Shorts reach has plateaued, CTAs are ineffective,
  cartoons lose viewers early (hook change merged 2026-10-15). Re-audit
  cartoon vs stock once there is a week of data after the hook change.
- **Decided against:** AI cute-animal videos (saturated, low subscriber
  conversion, policy risk, muddles the channel's audience signal).

## The character film (not built, planned)

Goal: a character-driven "movie", 10 min now and 1 hour later, with the owner's
own characters (Maya, Vanessa, Daniel, Leo have images; a 16-person cast is
planned), a distinct voice per character, no narrator, rendered on RunPod with
open models. `film/the-will-part-2.md` is a full Part 2 script, 34-shot list
with prompts, TTS script and RunPod order of work.
- **"The Will" was invented by Claude on 2026-10-15** (Daniel reads his will,
  Vanessa goes after the firm, Maya and Leo find a forged page). It is not a
  channel story. **Part 1 does not exist yet**; Part 2 assumes the recap in its
  section 1. "The Pitch He Stole" (Short, 2026-10-05) is a different, workplace
  story. Open question for the owner: rebuild Part 2 around the pitch story, or
  write a proper Part 1 of "The Will".
- Open-model route found by research: voice design (MOSS-VoiceGenerator or
  Qwen3-TTS VoiceDesign) -> MOSS-TTSD dialogue -> LongCat-Video-Avatar /
  InfiniteTalk talking video; Wan 2.2 for non-dialogue shots; Qwen-Image-Edit
  for stills; SeedVR2 upscale. Models make 5-15 s clips, at most 2 speakers per
  shot, so cut shot/reverse-shot. MiniMax-H3 is unusable (licence excludes
  US/EU/UK/Korea); JoyAI-Echo is non-commercial.
- Flow (Google) works for the owner (Omni 15 credits per 10 s; 1,000 monthly +
  50 daily credits). Suggested Chapter 1 in Flow with ~500 credits, as 3-4
  chapters over a month, to test whether viewers stay.
- The owner made a Short, "The Stolen pitch" (AI-labelled, realistic woman in a
  yellow jacket), outside this repo's pipeline; the model and workflow behind
  it are unknown to Claude.
- Idea under review: github.com/lemomo-ai/lemo-opuscar (MIT, film styles made
  in code, tuned for Claude Opus 5.5, Kokoro TTS). Possibly useful for cartoon
  pacing/sound and a new long-form look; not for lip-synced character dialogue.
  Only its README was read; next step was to read `DIRECTOR.md` and
  `TECHNIQUE.md` and borrow what helps.

## Open items

- Compare the `cartoon` and `short` lanes in `story_metrics` (hook change merged
  2026-10-15) and the hook/CTA experiment arms.
- Theme experiment review is scheduled for 2026-11-26 (see above).
- Pin `openai/gpt-oss-120b` via `/model` on the Telegram bot if not done.
- Re-enable the `trial` lane once Instagram allows trial Reels on the account.
- Delete the `previews` branch (it held a cloned-voice sample) and, if unused,
  the voice sample in `rendered-videos/voice/`.
- Drop the dead `GOOGLE_CLIENT_SECRET_JSON` references from both workflows.
- Point the image provider at a router once its API shape is known. Keep
  Pollinations as the keyless fallback, and parallelise the frame fetches —
  they are currently sequential, which is most of the illustrated lane's
  runtime.
- The illustrated lane has no schedule and posts unlisted. Give it a cron only
  once the look has been judged and its `story_metrics` rows can be compared
  against the short lane.
