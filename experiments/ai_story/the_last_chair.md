# THE LAST CHAIR — AI-only story pilot #1

**Theme:** In-Law Conflicts (top theme) set at a holiday dinner (third theme).
**Format:** 9:16, 1080x1920, ~85 s, no narrator voice over picture except the
two framing lines; the story is told through dialogue.
**Cast (repertory, `cast_plan.md` on branch `claude/short-story-tier-4-aividgen-6ow70v`):**
PRIYA (28, daughter-in-law, our hero, lavender wrap dress), ELEANOR (58,
mother-in-law, silver-blonde bob, pearls, cream sheath dress), ETHAN (32,
husband, light-blue shirt, navy blazer). All fictional adults.
**Set:** one room. Eleanor's formal dining room on Thanksgiving: long table,
candles, roast turkey, nine place cards, evening window. One location keeps the
reference work and pod time small for a first run.

## The triple hook

1. **Visual hook (0-2 s):** a close-up of a gloved hand sliding a place card
   off the table and dropping it in the trash. The card reads PRIYA.
2. **Spoken hook (2-6 s):** Priya, to camera-adjacent, quiet: "My mother-in-law
   counted the chairs. Nine. There are ten of us."
3. **Open loop (6-10 s):** Priya: "She forgot who paid for this table."
   The viewer now needs the payoff, and it is promised, not given.

Then a re-hook at ~45 s ("Ethan, tell her what you signed in March.") and a
cliffhanger last line that sets up Part 2.

## Script (lines are exact; numbers are clip ids)

| # | Speaker | Line | Delivery |
|---|---|---|---|
| L01 | PRIYA (VO) | My mother-in-law counted the chairs. Nine. There are ten of us. | quiet, dry |
| L02 | PRIYA (VO) | She forgot who paid for this table. | flat, certain |
| L03 | ELEANOR | Oh, Priya. I thought you were working tonight. | sweet, false |
| L04 | PRIYA | I took the night off. You knew that. You called my boss to check. | calm |
| L05 | ELEANOR | Family dinner is for family, darling. Ethan understands. | smiling, cold |
| L06 | ETHAN | Mom... can we not do this today? | tired, caught |
| L07 | ELEANOR | Do what? I simply set the table I can afford. | smug |
| L08 | PRIYA | Ethan, tell her what you signed in March. | still, measured (RE-HOOK) |
| L09 | ETHAN | ...The house loan. Priya paid it off. The deed's in her name now. | low, ashamed |
| L10 | ELEANOR | That's not possible. This is my house. | shaken |
| L11 | PRIYA | It was. Now it's the house I let you live in. | soft, no anger |
| L12 | PRIYA | So. Let's count the chairs again. | beat, then a small smile |
| L13 | ELEANOR | You wouldn't dare. | whisper |
| L14 | PRIYA (VO) | She was right. I wouldn't. Not tonight. Tonight I just wanted my seat. Monday, I wanted my answer. | cliffhanger |

Spoken: ~150 words, about 60 s of dialogue plus ~25 s of picture beats.

## Shot list

Rules carried over from the Recipe Clause work: one speaking person per clip
(so each clip's audio is one clean voice), mouths closed in silent shots,
"Nobody looks at the camera", everyone already in position from frame 1,
close-up or chest-up only, no readable text except the one place card insert.

**Dialogue coverage is over-the-shoulder (OTS).** Speaker's face sharp, facing
camera, filling the upper two thirds; the listener is a soft, out-of-focus
shoulder and back of head on one edge. The listener stays on the **same edge**
for the whole pair: when Eleanor speaks, Priya's shoulder is on the LEFT; when
Priya speaks, Eleanor's shoulder is on the RIGHT. That keeps the 180-degree line
so the cut reads as two people facing each other.

| Shot | Lines | Type | Still (start frame) | Video prompt |
|---|---|---|---|---|
| S01 | hook | insert, 2 s | gloved hand at the table edge, place card "PRIYA" | A woman's hand in a cream glove slides a white place card off the dinner table and drops it into a small brass bin. Close-up, shallow focus, candlelight. No faces. |
| S02 | L01-L02 | wide, 6 s | the full table, candles, nine places set, Eleanor adjusting a napkin at the far end | Slow push-in down the length of the Thanksgiving table toward ELEANOR at the head, who straightens a napkin and does not look up. Nobody looks at the camera. No one speaks. |
| S03 | L03, L05, L07, L10, L13 | **OTS-A** | ELEANOR on camera, PRIYA's lavender shoulder + long black hair soft on the LEFT edge | Keep the over-the-shoulder framing exactly. ELEANOR says, in one take: "[LINE]". The foreground shoulder stays almost still. Subtle drift, no cut, no zoom. No music, no other voices. |
| S04 | L04, L08, L11, L12 | **OTS-B** | PRIYA on camera, ELEANOR's silver bob + cream dress soft on the RIGHT edge | same template, PRIYA speaks |
| S05 | L06, L09 | **OTS-C** | ETHAN on camera, between them, PRIYA's shoulder soft on the LEFT edge | same template, ETHAN speaks |
| S06 | reaction | single, 3 s | ELEANOR's hand gripping the back of a chair, knuckles white | Close-up of a woman's hand with pearls at the wrist tightening on a dining chair back. No one speaks. |
| S07 | L14 | wide, 6 s | PRIYA pulls out the tenth chair and sits; Eleanor and Ethan standing, frozen | PRIYA calmly pulls a chair to the table and sits; the other two stay standing and still. Slow pull-out, candles flicker. No one speaks. |

Five stills (S03, S04, S05 are reused for every line in their row), so the
references stay consistent and each speaking clip is 3-6 s.

## Voices

One locked voice per character; generate each line as its own file.
- PRIYA: warm, low-mid, calm, faint South Asian-American accent, never raises her voice.
- ELEANOR: polished, clipped, sweet on the surface, cold underneath, older.
- ETHAN: soft, hesitant, mid-range, apologetic.
- VO lines (L01, L02, L14) are Priya's voice, slightly closer and drier.

## Assembly

S01 → S02 (VO L01-L02) → dialogue cutting OTS-A / OTS-B / OTS-C on each line,
S06 after L10, S07 under L14. Word-timed captions in the bottom third, never
over a face. Quiet piano bed ducked under dialogue, cut to silence for 0.8 s
before L09 and before L12. End card: "PART 2 MONDAY".

## Run order on the pod

1. Stills for the five rows (cast refs + this table).
2. One OTS-A and one OTS-B line first; check that the cut reads as two people
   facing each other before generating the rest.
3. Remaining lines, then S01/S02/S06/S07.
4. Voices, Whisper check of each line, assembly.
