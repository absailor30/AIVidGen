# Diff vs. upstream harry0703/MoneyPrinterTurbo

Status: research notes only, no code changed. Same branch as the avatar
research note (`claude/avatar-research-upstream-notes`, based on `main`).

Compared AIVidGen (`main`, this repo) against `harry0703/MoneyPrinterTurbo`
(upstream, at its current default-branch HEAD) by file listing + targeted
reads. This fork has diverged substantially in both directions — this is not
a "how far behind are we" diff, it's "what upstream has that might be worth
pulling in," since AIVidGen carries an entire story-automation stack
(Supabase queue, Groq generation, Instagram/YouTube publishing, Cloudflare
Worker scheduling) that upstream has none of.

## Worth evaluating

### `app/services/volcengine_seedance.py` — ByteDance Doubao-Seedance
Paid text-to-video generation via Volcengine's Ark API, wired into
`material.py` as a `video_source` option alongside Pexels/Pixabay/Coverr.
Submits a text prompt, polls a remote job, downloads the resulting clip.
Configurable duration (2-12s), resolution (480p/720p/1080p), aspect ratio.

- **Not avatar/identity-preserving** — same category as this repo's own
  `generate_images.py` (generated visuals instead of stock), except it
  generates actual video motion instead of a Ken-Burns-panned still.
  Relevant as a possible alternative or upgrade to the `illustrated` lane,
  not to the avatar problem.
- Worth a cost comparison against Flow/Veo and against Pollinations (current
  `illustrated` lane's free image provider) before adopting — Seedance is
  metered, unclear per-clip cost without checking current Ark pricing.

### `app/services/loomloom.py` — LoomLoom Market integration
Hosted marketplace SkillBot integration: can generate script candidates AND
text-to-video scenes (`video.text-to-video.aspect-ratio.v1` capability
profile) through a single API key, quote/confirm/run lifecycle. ~980 lines,
substantial integration.

- Two things this repo already does separately (Groq for scripts, would-be
  video generation) bundled into one paid marketplace call. Worth checking
  pricing/quality before considering — this is a third-party aggregator, not
  a specific model, so its actual output quality depends on what's behind it
  at run time.

### Kokoro TTS
Referenced in upstream's `app/config/config.py` and `app/services/voice.py`.
Free, open-source, self-hostable TTS engine.

- Directly comparable to this repo's `edge-tts` usage in
  `render_from_supabase.py` (`STORY_VOICE`, `VOICE_SPEED`, the
  `edge_tts_timeout` handling). If Kokoro's voice quality/cadence is
  acceptable, it removes a dependency on Microsoft's edge-tts endpoint
  entirely — worth a side-by-side listen test before switching, since this
  repo has already tuned `voice_rate` per variant against edge-tts's
  specific pacing (see the calibration comment in `render_from_supabase.py`
  around `VOICE_SPEED`).

### Material/response caching
`app/services/material_cache.py` (454 lines) and
`app/services/cache_manager.py` (215 lines) — a caching layer for fetched
materials. Could reduce redundant Pexels calls in the `short` lane if the
same keywords recur often; worth checking whether it would interact with
this repo's per-story local material handling (`build_payload`'s
`image_paths` / `video_materials` override).

## Lower priority / likely not relevant

- `app/services/task_artifacts.py`, `app/services/version_checker.py` —
  general robustness/bookkeeping, low risk to adopt if wanted, not
  investigated in depth here.
- `app/services/twelvelabs.py`, `app/services/metaso_minimax.py`,
  `app/services/muapi.py`, `app/services/ofox.py`, `app/services/sonilo.py`,
  `app/services/elevenlabs_music.py`, `app/services/bgm.py` — additional
  third-party provider integrations (video search/analysis, music, etc.).
  Not reviewed; `bgm.py` in particular conflicts with this repo's deliberate
  choice to ship no background music at all (see the NOTE on `bgm_type` in
  `render_from_supabase.py` — a copyright decision, not a taste one).

## Not relevant to this repo

- The full `webui_*` module and test suite (`app/services/webui_task.py`
  plus ~20 `test/services/test_webui_*.py` files) — AIVidGen runs headless
  via `render_from_supabase.py` in GitHub Actions, not through the Gradio
  WebUI upstream ships.
- i18n additions (`webui/i18n/az.json`, `ca.json`, `fr.json`, `it.json`,
  `ko.json`) — WebUI-only, not applicable headless.
- `Dockerfile.claude`, `docker-compose.claude.yml`, `.github/workflows/docker-ghcr.yml`
  — upstream's own CI/deployment tooling, unrelated to this repo's GitHub
  Actions-based render/publish workflows.
- `docs/skill/`, `docs/loomloom/*.template.json` — upstream's own
  documentation/skill scaffolding for its Claude Code integration.

## What this repo has that upstream doesn't

Not a gap — noted for completeness: the entire Supabase `story_queue` /
`story_state` pipeline, Groq-based story generation
(`generate_stories_cloud.py`, `generate_long_stories.py`), the
`illustrated` variant and its Pollinations-based `generate_images.py`,
Instagram Reels publishing, YouTube scheduled publishing, the Cloudflare
Worker scheduler, and IG token auto-refresh. None of this exists upstream.
This is not a fork that should ever merge wholesale in either direction —
cherry-pick specific files (Seedance, Kokoro, caching) if their eval pans
out, nothing more.

## Suggested next step

If any of the "worth evaluating" items look promising after a quick
cost/quality check, scope each as its own small, separate change — don't
bundle a Kokoro swap with a Seedance evaluation with the avatar work. They're
unrelated to each other.
