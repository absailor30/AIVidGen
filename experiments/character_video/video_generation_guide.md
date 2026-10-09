# High-quality character video — the full playbook

Everything learned from "The Stolen Pitch" in one place: pod, model,
settings, references, prompt format, framing rules, retakes and the edit.
Story channel use only.

---

## 1. Pod

| Setting | Value | Why |
|---|---|---|
| GPU | **L40** (48GB VRAM, ~250GB RAM), ~$0.82/hr | MiniMax peaks at ~67GB RAM / ~28GB VRAM; cheaper pods with <64GB RAM crash or crawl |
| Fallback | RTX PRO 4500 SE (32GB / 94GB) | untested; slower; needs its own SageAttention build |
| Container disk | **100GB** | models (~60GB incl. packages) download here every session |
| Volume | small Global volume at `/workspace` | only `start.sh`, `tunnel.sh`, the SageAttention wheel, outputs |
| Image | `runpod/pytorch` (cu128, Python 3.12) | |

Start-up (Jupyter terminal):
```bash
bash /workspace/start.sh        # terminal 1 — wait for "Running on local URL"
bash /workspace/tunnel.sh       # terminal 2 — open the trycloudflare URL
```
Scripts: `pod/start.sh`, `pod/tunnel.sh`, `pod/build_sageattention.sh`.

- RunPod's own HTTP proxy breaks WanGP buttons → always use the tunnel.
- Check the page shows **Attention mode sage2**. If not, the wheel is missing:
  run `pod/build_sageattention.sh` once (L40 only, ~20 min).
- Don't stop WanGP between parts: restarting re-pins ~60GB (a few minutes).
  Stopping the **pod** wipes the container disk (models re-download).
- First generation of a session: +5–15 min for model download and load.

## 2. Model and settings (WanGP)

| Setting | Value |
|---|---|
| Model | **MiniMax H3 → Ref2VA Pruned 20B → PDD 8-Step** (not plain H3 — it has no reference input) |
| Mode | **Text Prompt** |
| Reference images | **Use Reference Images** |
| Audio | **Generate without an Audio Reference** (narration is added in the edit) |
| Resolution | **704×1280** (9:16) |
| Steps | 8 (fixed by PDD) |
| Frames | seconds × 24 (4s ≈ 96, 4.5s ≈ 108, 5s ≈ 120) |
| Length per part | **≤ 5s** — cost grows faster than length (4.5s ≈ 7 min, 7s ≈ 13 min without sage; ~33% less with sage) |
| Seed | random; regenerate with a new seed for retakes |
| Memory profile | `--profile 1` (HighRAM_HighVRAM) on the L40 |

Settings reset when WanGP restarts — re-check model, mode, resolution, frames.

## 3. References — the part that makes or breaks identity

**Per character: two images, close-up first, then full body.**
```
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, …
```
- Upload order = Picture number. Background (if any) is Picture 1.
- Characters seen **only from behind** get just the full-body ref.
- Add a third ref (an expression image, e.g. `_shock`) only when that
  emotion *is* the shot.
- Max 9 images per part; fewer refs = faster and fewer duplicate people.
- Refs: one person, plain grey background, sharp face, ~1K is enough.
- **Crop the Flow ✦ watermark** from every ref — the model copies it.
- Never mix tools for one character (all Flow, or all Krea).
- New outfit = new ref made **from** the existing ref (face stays); a new
  text-only base gives a different person.

**Background — pick one method per part:**

| Method | When | Subject line |
|---|---|---|
| A. Style ref (default) | camera movement, new angles | "the office from <Picture 1>, used only as a style reference for the room's materials, colors and lighting; the room may be seen from any angle, with new parts invented to match" + `partially_preserved` |
| B. Extra angle | a specific reverse view must match | a second room image (Flow, "same room, reverse angle") |
| C. No BG ref | close-ups, moody shots, saves a slot | describe the room in text + "shallow depth of field, background softly blurred" |
| Exact | the room must match a frame (e.g. elevator at the end) | "preserving the …" + `fully_preserved` |

## 4. Prompt format (six sections, no blank lines inside)

```
subject_definitions:
<Subject 1> is …
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, hair and outfit.
summary:
[reference generation] One sentence: who does what, where.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - …
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> … Exactly one person is visible. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Close-up, chest up, face large and clear. <Subject 2> … Nobody looks at the camera. Slow push-in.
[Shot 2] At 00:03.000, cut to …
overall_soundscape: … No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

**Lines that fix known failures — include every time:**

| Problem | Line |
|---|---|
| Opens on the empty room, person walks in | "From the very first frame, every person in this shot is already in position; no empty establishing shot, nobody walks into frame." |
| Posing / smiling at camera | "Nobody looks at the camera." (drop it only for a deliberate to-camera beat) |
| Duplicate people | "Exactly N people are visible, each appearing only once." |
| Garbled screen / document text | "shows only abstract charts / icons, no readable text, no words, no letters, no numbers" |
| Grey studio background copied from refs | "the [room] clearly visible behind her, softly blurred. Not a studio background." |
| Unwanted speech | "No one speaks, no dialogue, no voices." |

**Framing rules:**
- Faces: **close-up or chest-up**. "Waist up" drifts wide in big rooms.
- Wide shots only with backs to camera (faces distort when small).
- Two people max per shot for reliable identity; 3–4 only from behind.
- One clear action per shot; actions are loose — write the *emotion*, not
  fine motor detail ("tired, rubs her eyes" may become "touches her hair";
  both read as tired).
- Multi-shot parts: cut with `At 00:0X.000, cut to …`; keep each shot ≥ 2s.

## 5. Retakes — when to regenerate

Regenerate (new seed) only for: **wrong person, duplicate person, broken
face/hands, wrong mood, empty-room opening longer than ~1s that you can't
trim.** Accept anything that conveys the right emotion — ~25% of parts need
one retake; budget for it.

## 6. Edit (narration + assembly)

`assemble.py` (ffmpeg + edge-tts, `en-US-JennyNeural`, rate +20%):
- One segment = one narration line + the clip pieces under it; visuals are
  speed-matched to the line (keep factors within 0.7–1.4×; warnings tell you
  which trims to change).
- A pause after a punchline (`"She froze."`, 1.6s) beats a sped-up clip.
- Trim empty openings; mute clip audio; flashback grade
  (`eq=saturation=0.45,colorbalance=bs=0.12,vignette`) for memories;
  `delogo` over the bottom-right corner; burned subtitles; 1080×1920 out.
- Freeze-frames with slow zoom cover long lines cheaply.

## 7. Cost and time (L40, SageAttention)

| Item | Time |
|---|---|
| Pod start + install | ~10–15 min |
| Model download/load (first gen) | ~5–15 min |
| 4–5s part | ~4.5–5 min |
| 12-part story | ~1 h generation ≈ $0.80–1.00 (+ retakes) |
| Edit (`assemble.py`) | ~1 min |

## 8. Before posting

- AI label on: YouTube "Altered or synthetic content" = Yes; Instagram AI info.
- Characters are fictional adults; wardrobe platform-safe.
