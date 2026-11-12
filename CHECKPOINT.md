# Pipeline checkpoint — 2026-10-04

A snapshot of how Twisty! StoryVault runs, why it is set up this way, and what
is still open. Update this in place rather than adding dated copies.

## Lanes

| Lane | Cadence | Destinations | Scheduler |
|---|---|---|---|
| `short` | 4x daily | YouTube + Instagram | Cloudflare Worker, 03:00 / 07:00 / 11:15 / 15:00 UTC |
| `long` (generate) | 1x daily | Supabase queue | GitHub cron, `0 13 * * *` |
| `long` (render) | 1x daily | YouTube only | Cloudflare Worker, `30 21 * * *` (03:00 IST) |
| `illustrated` | manual | YouTube (unlisted) | none — experiment |
| `trial` | paused (manual dispatch only) | Instagram trial Reels | GitHub cron `0 16 * * *`, commented out |
| character video | manual, once | not posted yet | none — experiment, RunPod pod |
| metrics | 1x daily | Supabase (YouTube + Instagram) | GitHub cron, `30 2 * * *` |
| IG token refresh | weekly | Supabase | GitHub cron, `0 1 * * 1` |

**The long render runs on the Worker, not GitHub's cron.** GitHub queues
scheduled workflows 2–3h late on this repo. The Worker's `30 21 * * *`
trigger, long silent, started firing on 2026-09-21 while the GitHub schedule
was still active, so long-form posted twice a night until the GitHub schedule
was removed (#29). Only one of the two may ever schedule it.

**The `trial` lane** posts one Instagram trial Reel (shown to non-followers
only, graduates to followers if it performs) and never posts to YouTube. Its
cron is commented out: Meta refused the first one with "Trial Reel Not Enough
Followers" (error_subcode 2207081). Restore the cron once the account
qualifies.

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
- **Groq 429s: per-minute limits wait, daily quotas don't.** A per-minute 429
  backs off (up to 120s, 6 attempts). A daily-quota 429 (TPD) moves straight to
  the next model in the chain, and when every model is out the generators stop
  with `GroqQuotaExhausted`. All top-up steps are `continue-on-error`, so a
  generation failure can't cost a render that already has a story queued.
- **Background music is back**, from 15 YouTube Audio Library tracks in
  `resource/songs/`, levelled by loudness. The inherited MoneyPrinterTurbo
  tracks drew copyright claims and were deleted, not just disabled:
  `get_bgm_file()` picks any `*.mp3` in that folder, so one unlicensed file
  brings the claims back.
- **Follower stories:** a consented, hand-written summary in
  `story_submissions` is written into the Shorts queue ahead of everything
  else, with every name and detail changed. Kept in Supabase rather than a
  workflow input because this repo is public.
- **Failures that are not failures.** A run can exit non-zero with the video
  already live on YouTube — that is deliberate, so an Instagram or bookkeeping
  problem cannot pass silently. Read the log before assuming nothing posted.

## Character video experiment

One 72s story ("The Stolen Pitch") was made end to end with four consistent,
recurring characters: refs from Flow (Nano Banana Pro), clips from WanGP +
MiniMax H3 Ref2VA on a RunPod L40, narration and edit with edge-tts + ffmpeg.
Everything needed to repeat it — prompts, pod scripts, `assemble.py`, timings,
and what broke — is in `experiments/character_video/README.md`. It is not
wired into any workflow and nothing from it has been posted.

The load-bearing findings: two refs per character (close-up + full body) hold
identity; parts must stay close-up/medium and ≤5s; the room image works best as
a style reference rather than a frame to copy. An L40 is the cheapest pod that
fits (needs ~67GB RAM, ~28GB VRAM); a story costs roughly $2–2.5 of pod time.

Where it is heading (budget: $20/month, one story a day):

- **Recurring cast** — `experiments/character_video/cast_plan.md`. Theme
  research from `story_metrics` (median day-3 views: Wedding & Family
  Entitlement 304, In-Law Conflicts 301, Sibling Rivalry 202 lead; Business
  Partnership Betrayal 39 trails) and a 16-actor repertory cast with Flow
  prompts for multi-angle refs. Refs are made by hand in Flow; none exist yet
  beyond the original four.
- **Hybrid lane** — `docs/proposals/hybrid-character-lane.md`. MiniMax only for
  the 4–5 beats that need a moving face; set/prop libraries, freeze-frames and
  Remotion for the rest; one weekly pod batch of 7 stories ≈ $12/month.
- **Headless WanGP exists.** `python wgp.py --process <settings.json|queue.zip>`
  runs without the web UI, and `shared/api.py` exposes `init()` /
  `submit_task()` / `submit_manifest()` for in-process batches. MiniMax Ref2VA
  is model `minimax_h3_ref2va_pruned_pdd`; references go in `image_refs` with a
  reference `video_prompt_type` — take the exact keys from the UI's "Export
  Settings" before scripting it. Not yet run on a pod.
- **Runpod from Claude Code.** The Runpod plugin only installs in a local
  Claude Code, not cloud sessions. Cloud sessions use the REST API
  (`rest.runpod.io`) with a `RUNPOD_API_KEY` environment variable instead —
  added to the cloud environment on 2026-10-04, untested yet (new sessions only
  pick it up). The environment's network allowlist now includes the Runpod
  docs, API and MCP hosts and huggingface.co.

## The Recipe Clause (4-part drama, Twisty! StoryVault) — state as of 2026-11-12

Branch: `claude/short-story-tier-4-aividgen-6ow70v`. Never push to `main`; no PRs unless asked.
Standing rules: pods ≤ $1/hr, stop them when done and monitor them; secrets only via the
credential form, never in chat; commit and push repo changes.

- **Part 1** published earlier (`publish/recipe_clause_ep1.*`).
- **Part 2 done and scheduled.** Published as a **YouTube Short** https://youtu.be/H_frceW-DnI,
  public **Fri 13 Nov 2026 22:00 IST (16:30 UTC)**. Cut: 2:00, back-lot "garage" scene (lines 14-17)
  removed, Grok watermark blurred, music "Cold Plated" + "Letters Under Seal", yellow Anton
  "TO BE CONTINUED / FOLLOW FOR / PART 3" end card (wanted on every episode). Files:
  `experiments/character_video/publish/` (mp4, 16:9 thumb, `recipe_clause_ep2_thumb_9x16.jpg`, json kit).
  Still the user's job: pick the Shorts cover frame in the YouTube app; check playlist placement.
- **Voices locked (v4)** in `voices/part2/` (Fish Drama 3 "Fish B": temp 0.95, top_k 50, top_p 0.95;
  take picks and speed changes in that README). Assembler: `recipe_assemble_p2.py` (env vars GROK, LIP,
  VOICES, MUSIC, WORK, OUT, FONT). Publish via `publish_episode.yml` (needs a full SHA, not a short one).
- **Lip-sync lesson.** InfiniteTalk animates every face in frame; use single-face crop close-ups
  (approved). LatentSync 1.6 tested and rejected as "fake". Pipeline: faster-whisper timings, afftdn,
  room IR reverb 0.18, loudnorm -21 LUFS, 160-180 wpm.
- **Open experiment 1 - Aria voice clone.** User preferred Grok's own Aria voice but Grok is expensive.
  `gtest/aria_grok_ref.wav` (7.6 s) is the reference. The Fish clone test on the user's pod
  `7c012nczdwf71v` **failed: all 12 takes `AttributeError in __init__.py:397`**. Pod is stopped (EXITED,
  $0.82/hr; delete it if no longer needed). Next: restart it, read WanGP's log for the full traceback, fix,
  re-run `clone_test.py`. **Alternative that already works:** Qwen3-TTS Space
  (huggingface.co/spaces/Qwen/Qwen3-TTS) Voice Clone with that reference gave a clean take with every word
  intact; speaker similarity vs Grok 0.78 (ours 0.75), pace ~146 wpm (needs speeding to 160-180). User to
  judge by ear. Open decision: new Aria voice from Part 3 only, or redo Part 2 (re-voice, re-lip-sync,
  re-render, re-upload).
- **Open experiment 2 - cheap video from stills.** HF Space `zerogpu-aoti/wan2-2-fp8da-aoti-faster`
  (Wan 2.2 I2V 14B Lightning, user is on PRO). Findings: face identity holds, even in two-person shots;
  16 fps native, interpolation gives 32 fps; Frame Upscale Factor 2 gives 960x1664 and is clearly sharper;
  negative prompt only works if Guidance Scale > 1; expression overshoots (slight smile became a grin)
  and the model invents mouth movement with no audio; first+last-frame mode works but drifts from the
  last frame when start and end framing differ a lot (studio-grey first frame morphed into the kitchen).
  Verdict so far: fine for silent filler (walk-ins, reactions, b-roll), not for acting or dialogue; talking
  shots still need Grok + InfiniteTalk. Script `experiments/character_video/wan22_i2v_test.py` is for the
  RunPod WanGP route and is untested (model id / profile names are guesses); the user is using the Space UI.
  Next: matching kitchen mid-shot as first frame, closer end frame.
- **Not here:** the chatbot/companion-app idea moves to a separate chat.

## Open items

- Drop the dead `GOOGLE_CLIENT_SECRET_JSON` references from both workflows.
- Point the image provider at a router once its API shape is known. Keep
  Pollinations as the keyless fallback, and parallelise the frame fetches —
  they are currently sequential, which is most of the illustrated lane's
  runtime.
- The illustrated lane has no schedule and posts unlisted. Give it a cron only
  once the look has been judged and its `story_metrics` rows can be compared
  against the short lane.
- Character video: run one `--process` job on a pod to prove headless MiniMax
  works, then confirm `RUNPOD_API_KEY` by listing pods from a new session.
  Next content step: three 60–75s stories for the top themes (wedding, in-law,
  sibling) written as hybrid shot lists. Until output quality is consistent,
  any automated version needs a human approval step before posting, and the
  AI-content labels on both platforms. Supabase flags `story_metrics` as having
  RLS disabled — enabling it needs a read policy for any anon-key reader first
  (the GitHub jobs use the service key and are unaffected).
