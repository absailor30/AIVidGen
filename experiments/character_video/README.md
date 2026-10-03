# Character video experiment — "The Stolen Pitch"

Status: manual proof of concept, done once (Oct 2026). Not wired into any
workflow. This folder is the base for a future automated lane.

Result: a 72s 9:16 narrated story with four consistent, recurring characters
(Maya, Vanessa, Daniel, Leo), generated on a RunPod L40 with WanGP + MiniMax H3
Ref2VA and assembled with edge-tts + ffmpeg.

## Pipeline as run

1. **Character refs (Flow, Nano Banana Pro, free):** one full-body ref per
   character, plus a straight-on head-and-shoulders close-up made from it.
   Same tool for every image of a character — mixing tools gives the video
   model two slightly different faces.
2. **Clips (RunPod L40, WanGP):** MiniMax H3 → Ref2VA Pruned 20B → PDD 8-Step,
   704×1280, Text Prompt + Use Reference Images, no audio reference.
   Prompts: `prompts/`. 12 parts, 4–8s each.
3. **Assembly (same pod):** `assemble.py` — edge-tts narration per segment
   (en-US-JennyNeural, same voice as `render_from_supabase.py`), trims, flashback
   grade, speed fixes, watermark blur, clip audio muted, subtitles burned in,
   output 1080×1920.

## What worked

- **Two refs per character** (close-up first, then full body; prompt says
  "the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body)")
  held identity in every part, including tight close-ups.
- **Characters seen from behind get only the full-body ref** — fewer refs,
  faster, no face needed.
- **Background as a style reference** ("used only as a style reference for the
  room's materials, colors and lighting; the room may be seen from any angle")
  gave new camera angles while the room still read as the same place. Best
  default. A second Flow-made angle of the room, or no background ref with a
  text description + shallow focus, also worked.

## What broke, and the fix

| Problem | Fix |
|---|---|
| Clip opens on the empty background image, then the character walks in | Add "From the very first frame, every person in this shot is already in position; no empty establishing shot, nobody walks into frame." Still trim a second sometimes. |
| Characters pose and smile at the camera | Add "Nobody looks at the camera." |
| Faces small and distorted in wide shots | Close-up / chest-up framing only. "Waist up" still drifts wide in big rooms. |
| Model copies the ref's grey studio background into a close-up | Describe the room behind them explicitly: "the conference room clearly visible behind her, softly blurred. Not a studio background." |
| Flow's ✦ watermark copied into the video | Crop the bottom-right corner of every ref before upload. `assemble.py` also blurs that corner. |
| Readable text on screens is garbled | "abstract charts / icons only, no readable text, no words, no letters". |
| Actions are loose (asked "rub eyes", got "adjust hair") | Accept anything that conveys the right emotion; regenerate only for wrong person, duplicate, broken face, wrong mood. |

## Timings and cost (L40, 48GB VRAM / 250GB RAM, $0.82/hr)

- Without SageAttention: 4.5s part ≈ 7 min, 7s part ≈ 13 min (cost grows
  faster than length — keep parts ≤5s).
- With SageAttention: same 4s part 7:03 → 4:43 total (denoising ~1.7× faster;
  text encoding / VAE decode unaffected).
- Peak use: 67GB RAM, 28GB VRAM, GPU at 100%. Cheaper pods with <64GB RAM
  (A40, A6000) crash or crawl; 24GB cards (3090) offload and slow down.
- Whole story ≈ 2–3 hours of pod time including setup, ≈ $2–2.5.

## Pod setup that worked

- No large network volume. Models (~60GB incl. packages) download to a 100GB
  container disk each session (HuggingFace pulled ~170 MB/s) — faster than
  loading them from a Global network volume, and no $12/month storage bill.
- A small Global volume at `/workspace` holds only `start.sh`, `tunnel.sh`,
  the SageAttention wheel and outputs. Global volumes reject chmod, so pip/cp
  print "Operation not permitted"; check file sizes, the data is usually fine.
- RunPod's HTTP proxy breaks WanGP's buttons — use `pod/tunnel.sh`.
- Restarting WanGP (Ctrl+C) re-pins models from local disk in a few minutes;
  stopping the pod wipes the container disk.

Scripts: `pod/start.sh`, `pod/tunnel.sh`, `pod/build_sageattention.sh`.

## Before posting

Tick YouTube's "altered or synthetic content" label and Instagram's AI label.
Characters are fictional adults; nothing NSFW goes near this pipeline.

## Open items toward automation

- WanGP headless/batch mode (no browser) — not yet verified; fallback is
  calling the model from our own script.
- Groq writes the story + per-part prompts from a fixed template.
- Recurring cast with stored refs, so no image generation per story.
- Clips to Supabase Storage; `assemble.py` moves into a GitHub Action.
- A human approval step before posting until output quality is consistent.
- Custom Docker image with torch/requirements/SageAttention preinstalled to
  cut ~10–15 min of pip install per pod start.
