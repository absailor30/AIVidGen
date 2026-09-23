# Scoping: avatar generation in the `illustrated` lane

Status: scoping only, no code changed. Lives on branch
`claude/short-story-tier-4-aividgen-6ow70v`, separate from `main`, for review
before any merge.

## Where this plugs in today

`render_from_supabase.py` picks a `VARIANT_PROFILES` entry (`short`,
`illustrated`, `long`) and builds a `TaskVideoRequest` payload. For
`illustrated`, `render_video()` calls `generate_images.generate_images()` to
produce N static frames, passes them in as `video_materials` with
`video_source: "local"`, and `task.py` / `video.py` turn each image into a
clip with a slow Ken Burns zoom (100%→120%), concatenated and scored over a
separately-synthesized `edge-tts` narration track. Frame count is derived
from narration length (`generate_images.image_count`): ~1 frame per
`clip_duration` (5s) seconds of speech.

An avatar-video step would replace `generate_images.generate_images()` with
something that returns video clips (or one clip) instead of stills, feeding
the same `video_materials` / `image_mode` path — that seam already exists and
is the natural insertion point.

## The blocking design conflict, not just an add-on

`generate_images.py`'s docstring is explicit: **"No people, no faces, no
recurring characters. Text-to-image cannot hold a person consistent across
fifteen frames, and a near-miss face reads as uncanny."** That's the opposite
premise of Tier 4's avatar requirement. This isn't a missing feature, it's a
design decision made after (presumably) trying the alternative. Before
building this, worth confirming that decision was about *image* models
specifically and doesn't also apply to single-shot avatar-video tools
(Flow/Veo/Runway/Pika), which is a materially different failure mode (they
hold a face for one continuous shot rather than stitching separately-sampled
frames).

## Architectural mismatch: stitched frames vs. single-shot generation

Current `illustrated` lane: **N independent stills + one separately
synthesized TTS track**, composited together. Tier 4's avatar spec: **one
continuous generation with the avatar's own lip-synced audio embedded**,
script → single avatar gen → voice → export — no stitching.

These don't compose cleanly:
- If the avatar tool outputs its own audio (native voice + lip sync), the
  existing `edge-tts` narration step must be skipped entirely for this path —
  otherwise you get two audio tracks. That's a fork in `render_video()`, not
  a parameter tweak.
- 60-90s is at or beyond the single-shot ceiling for most of these tools
  today (commonly ~8s per generation call, sometimes extended to ~1 min);
  realistically this still needs segmentation (multiple avatar-gen calls
  stitched with `concat_video_clips_with_ffmpeg`), which reintroduces the
  "does the face stay consistent across generations" problem the docstring
  above already flagged, just at video-shot granularity instead of frame
  granularity.
- `image_count()` / per-frame durations don't apply if a "frame" is now an
  8-15s video segment with its own audio — the pacing math in
  `generate_images.py` would need a parallel version keyed to segment count,
  not word-count-per-still.

## What a scoped v1 would actually need

1. **Provider integration module** (`generate_avatar_clips.py`, parallel to
   `generate_images.py`): takes the story dict + reference face/voice asset,
   calls whichever tool (Flow/Veo API, Runway, Pika — none of these are
   wired into this repo yet, no existing client code), returns a list of
   video file paths instead of image paths. No such client exists in this
   repo today; this is new integration work, not a config change.
2. **A reference asset**: a fixed face (and optionally voice) to hold
   consistent across a story's segments — this repo has no character/persona
   asset store; would need one (even if it's just a checked-in reference
   image + a seed value, mirroring `_story_seed()`).
3. **Audio path fork in `render_video()`**: if the avatar tool supplies its
   own voice, `edge-tts` synthesis must be bypassed for this profile, and
   subtitle timing (`generate_subtitle`) needs to derive cue timing from the
   avatar audio instead of a `SubMaker` built from `edge-tts`'s own output —
   that's a non-trivial change to `task.py`'s `generate_audio` /
   `generate_subtitle` sequence, not just a new material type.
4. **New `VARIANT_PROFILES` entry** (e.g. `"avatar"`) so this ships as an
   experiment next to `illustrated`, not a replacement — consistent with how
   `illustrated` itself was introduced to compete in `story_metrics` rather
   than replace `short`.
5. **Fallback story**: `illustrated` already has one (drop to Pexels if
   <2/3 of frames generate). An avatar lane needs an equivalent — most likely
   "fall back to the `illustrated` static-frame path" rather than to Pexels,
   since a story with a real avatar failing halfway shouldn't silently post
   as generic stock footage under the same variant name.
6. **Cost/rate accounting**: these are real per-second-of-video API costs,
   not a free keyless call like Pollinations. Needs its own budget/backoff
   handling, separate from the `generate_images.py` retry model.

## Net assessment

Feasible as a new, separate variant (`avatar`) that reuses the queue/render/
upload scaffolding in `render_from_supabase.py` — that plumbing is
variant-agnostic and doesn't need to change. Not feasible as a small patch to
the existing `illustrated` lane: the audio model, pacing model, and the
explicit no-faces design decision all need to be re-derived, not extended.
Biggest open unknown is whether any single-shot tool actually holds a
consistent face for 60-90s without segmentation — worth a manual spike
outside this codebase before writing `generate_avatar_clips.py`.
