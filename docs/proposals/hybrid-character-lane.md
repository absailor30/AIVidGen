# Proposal: hybrid character lane (1 story/day, ≤ $20/month)

Status: scope only, no code. Builds on `experiments/character_video/` (the
manual "Stolen Pitch" run) and `experiments/character_video/cast_plan.md`.

## Why hybrid

A full-video story is ~12 MiniMax parts ≈ 1 h of L40 ≈ $1–1.30 with retakes,
plus ~20 min of pod startup per session → $35–45/month at one story a day.
The budget is $20. So only the shots that need a **moving, recognisable
face** get generated video; everything else comes from assets that are free
or made once.

## Shot types

| Type | Source | Cost | Used for |
|---|---|---|---|
| **A. Character clip** | MiniMax H3 Ref2VA on the pod, 2 refs per actor | ~4.5 min L40 per 4s part (with SageAttention) | the 4–5 beats that carry the story: the reveal, the shock face, the confrontation, the exit |
| **B. Set shot** | **Set library**: rooms made once in Flow (office day/night, conference room, kitchen, living room, wedding venue, church, restaurant, corridor, apartment door, lawyer's office), animated with slow push/pan | free after the one-time library | establishing beats, transitions, "Monday morning…" lines |
| **C. Freeze-frame** | a held frame pulled from a type-A clip, with slow zoom | free | stretch a strong face to cover a long narration line instead of slow-motion |
| **D. Insert** | Flow still of a prop (phone with blurred screen, ring, envelope, receipt, house keys) from a reusable props library, animated | free after library | "the text message", "the will", "the receipt" beats |
| **E. Optional: LTX-2 B-roll** | LTX-2 on the same pod, no people | ~1 min per clip | only if B/D stills look too static; costs an extra model download and load per session |

Typical 60–75s story: **4–5 type A**, 3–4 type B, 1–2 type C, 1–2 type D.

## Budget

Per story: 5 parts × ~4.5 min ≈ 23 min + ~20% retakes ≈ **28 min of L40**.

| Schedule | Pod time / month | Cost / month |
|---|---|---|
| Pod every day (startup paid daily) | 30 × (20 + 28) min ≈ 24 h | ≈ $20 — no headroom |
| **Pod once a week, 7 stories per session** | 4 × (20 + 7 × 28) min ≈ 14.5 h | **≈ $12** |
| Weekly + custom Docker image (startup ~8 min) | ≈ 13.5 h | ≈ $11 |

**Recommendation: weekly batch.** Generate 7 stories in one session, store the
clips, let the daily job assemble and post one per day. It leaves ~$8/month
for retakes and experiments. It needs a 7-story buffer, the same idea the
long lane already uses with its generate/render split.

## Pipeline

```
Weekly (manual trigger at first, cron later)
  1. GitHub Action: Groq writes 7 stories as a shot list (JSON, below)
     → story_queue rows with variant = "character"
  2. GitHub Action: start the L40 pod via the RunPod API
  3. Pod: start.sh → run each type-A shot headless → upload clips to
     Supabase Storage → stop itself
Daily (existing scheduler slot)
  4. GitHub Action: claim the next ready story → edge-tts narration →
     Remotion render (clips + set shots + freeze-frames + captions)
  5. Human approval (one tap) → existing YouTube/Instagram upload code,
     with the AI-content label set
```

### Shot-list JSON (what Groq produces per story)

```json
{
  "theme": "In-Law Conflicts",
  "cast": {"narrator": "priya", "mother_in_law": "eleanor", "husband": "ethan"},
  "beats": [
    {"narration": "...", "type": "set", "set": "kitchen_day", "motion": "push_in"},
    {"narration": "...", "type": "character", "actors": ["eleanor"],
     "framing": "chest_up", "background": "kitchen_day", "action": "...",
     "emotion": "smug", "seconds": 4},
    {"narration": "...", "type": "freeze", "from_beat": 1},
    {"narration": "...", "type": "insert", "prop": "house_keys"}
  ]
}
```

The MiniMax prompt is built **by code from this JSON**, not written by the
LLM, using the template that worked by hand (two refs per actor, style-ref
background, "From the very first frame…", "Nobody looks at the camera",
no readable text). Groq only picks actors, sets, actions and emotions from
fixed lists, so it cannot ask for an actor or set that has no refs.

### Remotion (replaces ffmpeg in `assemble.py`)

- One composition: a timeline of beats from the JSON, each beat's length taken
  from its narration audio, with no speed-squeezing of character clips.
  Freeze-frames and set shots absorb the slack.
- Word-by-word captions, the flashback grade, the watermark-corner blur.
- Renders on GitHub Actions (Node + Chromium, CPU only). Check the Remotion
  licence terms for the account before using it.

## Risks

- **WanGP headless mode is unverified.** If it can't run unattended, the pod
  needs its own small script around the MiniMax pipeline. This is the first
  thing to test, because the whole design depends on it.
- **Quality varies.** About a quarter of parts need a retake (wrong pose,
  duplicate person, empty-room opening). Without a human approval step, bad
  clips get posted. A face-similarity check against the actor's refs
  (insightface is already installed with WanGP) can catch some of these, not all.
- **RunPod L40 availability is often "Low".** A weekly batch can wait or fall
  back to the RTX PRO 4500 SE (untested, and it needs its own SageAttention
  build).
- **Flow has no free API.** The cast, set and props libraries are made by hand
  once. Every story has to be castable from those libraries.

## Phases

1. **Libraries (manual, Flow):** cast refs from `cast_plan.md`, ~10 sets,
   ~10 props.
2. **Headless test:** one type-A shot generated on the pod from a script, no
   browser.
3. **Remotion template:** re-cut "The Stolen Pitch" with Remotion to prove the
   hybrid timeline on known clips.
4. **One hand-triggered weekly batch** end to end, posted unlisted.
5. **Schedule it**, keeping the human approval step until a few weeks of output
   are consistently good.

## Open questions

- Should story length go down to ~50–60s for this lane, which means fewer type-A shots?
- Is the approval step a Supabase flag you flip from your phone, or a
  Telegram/WhatsApp message with approve/reject?
- Does this lane replace the `illustrated` lane, or run alongside it?
