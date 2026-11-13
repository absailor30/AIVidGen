# The Recipe Clause — Part 3 "The Clause": Grok Imagine shot list

Vertical 9:16, 15 s per clip from a start image (cast still or set image). Same rules as Part 2:
end every prompt with **"no one speaks, no dialogue, ambient sound only"**, mouths closed, faces clear;
talking close-ups are lip-synced afterwards from a clean frame (single-face crop).
Cast looks: same as `recipe_clause_part2_grok.md` (ARIA, VANESSA, DANIEL; LEO/MAYA background only).

## Assets
Reuse: `set_kitchen`, `set_office`, Aria/Vanessa/Daniel stills. **New:**

| Asset | Prompt |
|---|---|
| `set_dining` | Warm family dining room in an older suburban house, long wooden table set for dinner, three places, soft pendant light, framed family photos on the wall, evening window |
| `set_apt_night` | Small apartment kitchen table at night, a laptop glowing, a glass jar of dark sauce base beside it, one warm lamp, city lights in the window |

## Shots (14 spoken lines, indices 0-13; ~75-90 s of picture)

| # | Lines | Set | Prompt (picture) | Priority |
|---|---|---|---|---|
| 1 | 0 recap | kitchen | **Reuse Part 2 shot 1** (busy kitchen, Aria plating) — no new credits | free |
| 2 | 1 | apt night | ARIA alone at the table, calm, types one short email and presses send; the laptop light on her face; she closes the lid slowly. Slow push-in. | A |
| 3 | 2-7 | kitchen pass | VANESSA storms up to ARIA at the pass holding a printed letter; ARIA calmly slides her a second copy; cooks pretend not to watch. Medium two-shot, slow orbit. Master for the whole exchange. | A |
| 4 | 3,5,7 | kitchen | Close-up ARIA, calm, dry half-smile, patient eye contact off-camera. (lip-sync) | A |
| 5 | 2,4,6 | kitchen | Close-up VANESSA, furious, scoffing, a flicker of doubt behind the anger. (lip-sync) | A |
| 6 | 8 | office | VANESSA pacing her glass office on the phone, then cut to DANIEL at home putting a landline down slowly, then lifting a dinner reservation card. One fluid move each. | B |
| 7 | 9-13 | dining | DANIEL at the head of the table, ARIA left, VANESSA right; Vanessa leans forward angry, Aria sits very still. Static three-shot, slow push-in. Master. | A |
| 8 | 11,13 | dining | Close-up DANIEL, tired, heavy, honest. (lip-sync) | A |
| 9 | 10,12 | dining | Close-up VANESSA, hurt and defensive, eyes bright. (lip-sync) | B |
| 10 | end | dining | Insert: the old contract on the table between the plates, Daniel's hand resting on it; ARIA's hand slides in beside it. Slow push-in. Ominous quiet. | B |

Credit order if limits run out: 3, 7, 4, 5, 8, 2, 9, 10, 6.

## Open before voicing
- Part 3 script is only 14 lines (~75 s). Part 2 was 2:00. Consider 4-6 extra lines or a closing hook.
- Voice engine for Aria: Fish v4 (locked, used in Part 2) vs Qwen3-TTS clone of the Grok reference.

---
# Grok-voice route (decided 2026-11-13): Grok speaks the lines itself

One clip **per speaking turn**, one person speaking, the other silent or off-frame, so each clip's audio is
one clean voice. We cut between clips; no InfiniteTalk lip-sync, no Fish. Start image = that character's
cast still in the right set (Grok derives the voice from the face, so use the **same still every time**).

Prompt template (paste, fill the bracket):
`[Shot description, one person on camera, close-up, static camera]. The woman speaks this line in one take, clearly, [voice]: "[LINE]". She stops speaking and holds the look for a second. No music, no other voices, no other dialogue.`

Voice tags (keep identical every time): ARIA `calm, dry, low-mid pitch, controlled, never raises her voice`;
VANESSA `smug, sharp, clipped, polished, slightly nasal`; DANIEL (man) `warm, deep, slight gravel, measured, tired`.

| Clip | Line # | On camera | Line (exact) |
|---|---|---|---|
| g01 | 2 | Vanessa, kitchen, holding a letter | What is this? |
| g02 | 3 | Aria, kitchen pass | It's a letter. Clause fourteen. You should read it. All of it, this time. |
| g03 | 4 | Vanessa | This is ridiculous. You can't own a short rib. |
| g04 | 5 | Aria | I don't own the cow. I own the recipe. And as of Monday, you're not licensed to serve it. |
| g05 | 6 | Vanessa | I'll call our lawyers. |
| g06 | 7 | Aria | Please do. Ask them about clause fourteen. Dad wrote it. He's very good at contracts. |
| g07 | 9 | Daniel, dining head of table | Sit down. Both of you. |
| g08 | 10 | Vanessa, dining | She is holding the business hostage! |
| g09 | 11 | Daniel | No, Vanessa. You cut her pay to lease a car, and you forgot to read what you were cutting. That's not a hostage. That's a receipt. |
| g10 | 12 | Vanessa | You're taking her side? |
| g11 | 13 | Daniel | I'm taking the contract's side. I wrote it for exactly this. I just hoped I'd never need it. |

Narrator lines (0, 1, 8 and any closing hook) stay on the locked Fish narrator so Parts 1-3 match.
Plus the silent b-roll shots (2, 3, 6, 7, 10 above) for cutaways.

Then I will: extract each clip's audio, check the words with Whisper (reject a take that changed the
wording), trim silence, speed to 160-180 wpm, and assemble with the Part 2 assembler (Grok audio in place
of the Fish lines, no lip-sync pass).

Check first: generate g02 and g09 and see whether Aria and Daniel sound the same in two different clips.
If a character's voice drifts between clips, we fix it by cloning one good take, not by re-rolling.
