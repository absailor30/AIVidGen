# Research: self-hosted avatar video generation as a Flow/Veo alternative

Status: research notes only, no code changed. Branch
`claude/avatar-research-upstream-notes`, based on `main`, separate from the
Tier-4 illustrated-lane scoping branch
(`claude/short-story-tier-4-aividgen-6ow70v`).

## Why this note exists

The illustrated-lane scoping doc (`avatar-illustrated-lane.md`, on the other
branch) concluded that no open-source video model matches Flow/Veo 3 for a
consistent talking avatar, and that Flow's own economics don't support daily
automation at volume:

- Metered Veo 3 API: ~$30-56 per 75s story → **$3,600-6,750/month** at 4
  videos/day. Not viable.
- Flow's 1,000 credits/month plan: ~160-220 credits per 75s story on Veo 3
  Fast (8s segments) → **~5-6 stories/month total**, not 4/day. Roughly a
  20-30x shortfall against the current posting cadence.

That math hasn't changed. What's changed is the open-source side: a specific
model exists now that's a much closer fit than "no faces, text-to-image can't
hold a person" (the premise `generate_images.py` was written under).

## HunyuanVideo-Avatar (Tencent)

Github: `tencent-hunyuan/HunyuanVideo-Avatar`
Hugging Face: `tencent/HunyuanVideo-Avatar`

Unlike general text-to-video models (HunyuanVideo base, Wan2.x, Mochi-1,
CogVideoX) that generate a scene and hope a described face stays consistent,
this is **purpose-built for identity-preserving, audio-driven avatar
animation** — closer to SadTalker/LivePortrait's job than to Flow's, but with
real scene dynamics instead of a mostly-static photo.

- Multimodal diffusion transformer (MM-DiT); takes a reference avatar image +
  audio, outputs emotion-controllable, dynamic video with the character held
  consistent.
- Explicitly claims better identity preservation than standard HunyuanVideo
  I2V mode, "where the face can drift across frames" — i.e. addresses the
  exact failure mode `generate_images.py`'s docstring cites for why it
  avoids faces entirely.
- **Via the WanGP wrapper** (a web UI that runs 20+ Wan/HunyuanVideo/LTX
  models, optimized for low-VRAM): reported to generate **15s of voice/song
  -driven video on 10GB VRAM**. That fits inside a T4 (16GB), not just a
  rented A100 — this is the load-bearing fact that makes it worth a spike.

### What this does and doesn't solve

Solves:
- Cost. Self-hosted (RunPod hourly, or even Colab for testing) is a flat
  compute cost, not a per-second/per-credit metered fee. At T4-class hardware
  this could be single-digit dollars per hour of generation time rather than
  Flow's credit economics.
- The face-consistency problem within one 15s segment, per the model's own
  claim (unverified by us — see Open questions).

Doesn't solve:
- **Segment count.** 60-90s of story still needs ~4-6 segments at 15s each
  (better than Veo's ~8s chunks, roughly half the stitching problem, not
  zero of it). Cross-segment consistency (same face across separately-run
  15s generations) is a different question from within-segment consistency,
  and isn't addressed by the "10GB VRAM, 15s" claim on its own.
- **Quality gap vs. Flow.** No source claims parity with Veo 3 — only that
  it's the strongest open option specifically for avatars. Untested by us
  whether the gap is "acceptable for a daily content channel" or "obviously
  worse to any viewer."
- **Audio path fork**, same issue flagged in the illustrated-lane doc: if
  HunyuanVideo-Avatar drives its own lip-synced audio from a reference clip,
  the existing `edge-tts` narration step in `render_from_supabase.py` /
  `task.py` still needs bypassing for this path, same as the Flow-based
  avatar variant would need.

### TalkVerse (arXiv, Dec 2025) — flagged, not evaluated

A more recent paper specifically targets *minute-long* audio-driven video
generation, which would remove the segmentation problem entirely if it
holds up. As of this research pass it reads as research-stage — unclear
whether a usable public checkpoint/inference code exists yet, versus just a
paper. Worth a follow-up check before relying on it; not something to build
against today.

## Recommended next step

A manual spike, outside the pipeline codebase, before any integration work:

1. Stand up WanGP + HunyuanVideo-Avatar on a rented GPU (RunPod, or Colab if
   it fits) or eligible local hardware.
2. Generate 2-3 sample 15s clips using one fixed reference face + a short
   audio clip resembling actual story narration (cadence, not just a clean
   read).
3. Judge two things separately: (a) does the face hold up within one 15s
   clip, and (b) does it look like the *same* face if you regenerate a
   second clip from the same reference image (the cross-segment case a real
   60-90s story needs).
4. Only after that: decide whether this replaces Flow for the avatar
   variant, or whether Flow's quality is worth its cost for a smaller,
   lower-frequency avatar lane (as scoped in `avatar-illustrated-lane.md`).

No pipeline code should be written against this model until step 3 has an
answer — the entire value proposition rests on a claim ("10GB, 15s, identity
preserved") that this research pass could not independently verify.
