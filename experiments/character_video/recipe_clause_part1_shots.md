# The Recipe Clause — Part 1: shot list

Goes with `recipe_clause_part1.md`. Hybrid lane: MiniMax clips for movement and
every ⚡ reaction; cast stills (slow zoom/pan in the edit) under the rest of the
narration and dialogue.

## Settings (every clip)
- MiniMax H3 → Ref2VA Pruned 20B → PDD 8-Step, 704×1280, frames = 24 × seconds
- Every clip ≤ 5s. Load references **in the order listed**; `<Picture N>` = Nth image.
- Refs are the cleaned cast files (`/workspace/cast/<Actor>/…`) plus a set image.
- Two refs per on-camera character: close-up first, full body second. Back-to-camera = full body only.

## Missing before you start (make in Flow)
| File | Prompt (text only, attach nothing) |
|---|---|
| `set_dining` | Elegant modern restaurant dining room in the morning, warm wood tables set with white linen, brass pendant lights, large windows, empty, no people. Photorealistic, vertical 9:16, no text. |
| `set_kitchen` | Busy professional restaurant kitchen, stainless steel counters, steaming pots, pass with heat lamps, swing doors at the back, a large steel fridge, empty, no people. Photorealistic, vertical 9:16, no text. |
| `set_office` | Small restaurant back office, wooden desk with a tablet, framed photo of an old restaurant on the wall, door open to a corridor, warm lamp light, empty, no people. Photorealistic, vertical 9:16, no text. |
| `set_terrace` | Restaurant rooftop terrace at night, string lights, iron railing, city lights beyond, a lit window into the dining room, empty, no people. Photorealistic, vertical 9:16, no text. |
| `set_apartment` | Small cosy apartment kitchen at night, single warm pendant light, glass jars on a wooden counter, empty, no people. Photorealistic, vertical 9:16, no text. |
| `leo_chef_ref` | Attach `leo_ref`. *The man from the reference image, exact same face, hair, glasses, skin tone and body, now wearing white chef whites with a white apron and black kitchen clogs. Full body, head to shoes, front view, neutral relaxed pose. Plain light grey studio background, soft even studio lighting. Photorealistic, sharp focus, natural skin texture. No text, no other people.* |
| `leo_chef_close` | Attach `leo_chef_ref`. *The man from the reference image, exact same face, hair, skin tone, body and outfit. Close-up head-and-shoulders, facing the camera, neutral expression. (same ending)* |

Chef Laurent is an extra — prompt only, always back to camera, no ref.

## Prompt template
Fill the `{…}` parts from the table. Keep it on one block, no blank lines.
```
subject_definitions:
<Subject 1> is the {SET} from <Picture 1>, preserving its layout, lighting and colours.
{one line per character: <Subject N> is the {man/woman} shown in <Picture a> (face close-up) and <Picture b> (full body), preserving their identity, face, hair and outfit.}
summary:
[reference generation] {SUMMARY}
retention_analysis:
{one line per subject: <Subject N> (appears in [Shot 1]): fully_preserved - face, hair and outfit.}
detailed_description:
The target video is a vertical cinematic shot in <Subject 1>. From the very first frame exactly {N} {person/people} {is/are} in the scene. Nobody looks at the camera. No readable text anywhere.
[Shot 1] {SHOT}
overall_soundscape: {SOUND}. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

## Clips (29 · ~110s of video · ~2.3h on an L40 ≈ $2)
**A** = must be a clip. **B** = clip if time allows, otherwise a still with a slow push-in.

| # | Scene | Pri | Sec | References in order | Shot (paste into `{SHOT}`) | Sound |
|---|---|---|---|---|---|---|
| 1 | Cold open | A | 4 | set_kitchen, aria_close, aria_ref | Close-up on hands: <Subject 2> folds a white apron into a neat square on a steel counter and slides it forward. Tilt up to her calm, unreadable face. | quiet kitchen hum |
| 2 | Cold open | A | 3 | set_office, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2> stares down at a folded white apron on the desk, red nails hovering above it, lips tight. | silent room |
| 3 | Handover | B | 4 | set_dining, daniel_close, daniel_ref | Medium shot: <Subject 2> raises a champagne glass, proud warm smile, speaking to an off-screen crowd. | murmuring staff, glass clink |
| 4 | Handover | A | 4 | set_dining, vanessa_office_close, vanessa_office_ref | Medium shot: <Subject 2> steps forward beaming, red heels clicking on the wooden floor, chin lifted. | light applause |
| 5 | Handover | A | 3 | set_dining, aria_close, aria_ref | Close-up: <Subject 2> claps politely, face calm and unreadable, eyes steady. | light applause |
| 6 | Handover ⚡ | A | 3 | set_dining, leo_chef_close, leo_chef_ref | Close-up: <Subject 2> glances sideways toward someone off-screen with a worried look. | applause fading |
| 7 | The Cut | B | 5 | set_office, vanessa_office_close, vanessa_office_ref | Medium shot: <Subject 2> sits behind a wooden desk swiping a tablet, smug, then looks up across the desk. | quiet office, tablet taps |
| 8 | The Cut | A | 5 | set_office, aria_close, aria_ref | Medium shot: <Subject 2> unties her white apron, folds it once and sets it neatly on the desk in front of her, calm and unhurried. | fabric rustle |
| 9 | The Cut ⚡ | A | 3 | set_office, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2>'s smile freezes; she pushes something away with one finger, jaw tight. | silence |
| 10 | The Cut ⚡ | A | 3 | set_office, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2> opens her mouth to reply, closes it, then taps her tablet too hard. | sharp taps |
| 11 | The Cut | A | 4 | set_office, aria_close, aria_ref | Medium shot: <Subject 2> pulls the office door wider open and walks out without looking back. | door creak, footsteps |
| 12 | The Cut ⚡ | A | 3 | set_office, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2>'s jaw tightens as she stares at an open doorway. | door swinging |
| 13 | The Rule | A | 4 | set_kitchen, aria_kitchen_close, aria_kitchen_ref | Medium shot: <Subject 2> pins a laminated sheet to a steel fridge door and smooths it flat. Sheet is blank, no readable text. | kitchen hum |
| 14 | The Rule ⚡ | A | 3 | set_kitchen, leo_chef_close, leo_chef_ref | Close-up: <Subject 2> slowly breaks into a knowing grin. | kitchen hum |
| 15 | Day Three | B | 3 | set_kitchen, leo_chef_close, leo_chef_ref | Close-up: <Subject 2> tastes a sauce from a spoon and winces. | sizzling pans, busy kitchen |
| 16 | Day Three | A | 4 | set_kitchen, maya_v2_close, maya_v2_ref | Medium shot: <Subject 2> pushes through swing doors carrying two plates of food, frustrated. | busy kitchen, door swing |
| 17 | Day Three | A | 4 | set_kitchen, vanessa_office_close, vanessa_office_ref | Medium shot: <Subject 2> storms into the kitchen holding a phone, angry. | busy kitchen |
| 18 | Day Three ⚡ | A | 3 | set_kitchen, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2> glances sideways at a fridge, jaw tightening. | kitchen hum |
| 19 | Day Three ⚡ | A | 4 | set_kitchen, vanessa_office_close, vanessa_office_ref, leo_chef_ref | Medium shot: the kitchen goes still; <Subject 3> in the background drops a spoon; <Subject 2> in front flushes red. | spoon clatter, silence |
| 20 | Daniel | B | 5 | set_terrace, daniel_close, daniel_ref, aria_ref | Medium shot at night: <Subject 2> and <Subject 3> stand at the railing side by side, city lights behind, a tense quiet talk. | night city, faint music from inside |
| 21 | Daniel ⚡ | A | 3 | set_terrace, daniel_close, daniel_ref | Close-up at night: <Subject 2> looks through a lit window, troubled, then looks down. | night city |
| 22 | Daniel | A | 4 | set_terrace, daniel_close, daniel_ref | Medium shot: <Subject 2> stands, avoids eye contact, and walks away along the terrace. | footsteps |
| 23 | Replacement | B | 5 | set_kitchen, vanessa_office_close, vanessa_office_ref | Medium shot: <Subject 2> gestures proudly toward a man in a designer black chef's jacket who stands with his back to the camera. | staff murmuring |
| 24 | Replacement ⚡ | A | 3 | set_kitchen, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2>'s confident smile drains away slowly. | silence |
| 25 | Replacement | A | 3 | set_kitchen, maya_v2_close, maya_v2_ref | Close-up: <Subject 2> looks down at her phone as it buzzes; her eyes widen. Phone screen faces away. | phone buzz |
| 26 | Replacement ⚡ | A | 3 | set_kitchen, vanessa_office_close, vanessa_office_ref | Close-up: <Subject 2> freezes, colour draining from her face. | silence |
| 27 | Replacement | A | 4 | set_kitchen, aria_ref | Wide shot: <Subject 2> walks toward the swing doors and out, never looking back. | footsteps, door swing |
| 28 | Cliffhanger | A | 4 | set_apartment, aria_home_close, aria_home_ref | Close-up: <Subject 2> lifts the lid off a glass jar on the counter; steam rises; a faint smile. | quiet night, lid clink |
| 29 | Cliffhanger | A | 4 | set_office, vanessa_office_close, vanessa_office_ref | Medium shot in a dark office: <Subject 2> sits alone staring at a folded white apron on the desk. | silence, distant clock |

## Stills (under narration and dialogue)
Use the cleaned cast images directly, 3–6s each, slow push-in:
- Aria's lines: `aria_cold`, `aria_unbothered`, `aria_smug`, `aria_power_close`
- Vanessa: `vanessa_smug`, `vanessa_angry`, `vanessa_shock`, `vanessa_office_close`
- Daniel: `daniel_smile` (handover), `daniel_sad` (terrace)
- Maya: `maya_v2_close`, `maya_shock`; Leo: `leo_chef_close`, `leo_smug`
- Sets on their own between scenes (`set_dining`, `set_terrace`…), 2s each.

## Order of work
1. Make the 5 sets and Leo's chef look in Flow.
2. Test **clip 9** first (a single-face ⚡ shot, the most common type). If Vanessa's face holds, run the rest.
3. Clips 19 and 20 have two people. If either duplicates a person, drop to one person and cut between them.
