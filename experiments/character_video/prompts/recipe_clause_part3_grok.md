# The Recipe Clause — Part 3 "The Clause": script and Grok Imagine shot list

Continues `recipe_clause_parts2_4.py` (branch `claude/short-story-tier-4-aividgen-6ow70v`),
same format as `recipe_clause_part2_grok.md`. Vertical 9:16, about 2:10.

## Script (27 lines)

Changes from `PART3` in `recipe_clause_parts2_4.py`: a cold open before the
recap (lines 0-1 are the two strongest lines of the part, heard again at 6-7),
and the recap cut to one sentence. Episode 1's parts lost most viewers in the
first seconds; "Previously..." is the weakest possible opening for a Short.
Nothing else in the plot changes, so Part 4 still follows as written.

| # | Speaker | Direction | Line |
|---|---|---|---|
| 0 | VANESSA | scoffing | You can't own a short rib. |
| 1 | ARIA | dry, patient | I don't own the cow. I own the recipe. |
| 2 | NARR | calm storyteller | My stepsister cancelled my recipe fee. What she didn't read was clause fourteen. No fee, no licence. No licence, no menu. |
| 3 | NARR | dry | I didn't shout. I didn't post anything. I sent one email. Subject line: Notice of licence termination. |
| 4 | VANESSA | furious, storming in | What is this? |
| 5 | ARIA | calm, polite | It's a letter. Clause fourteen. You should read it. All of it, this time. |
| 6 | VANESSA | scoffing, then uncertain | This is ridiculous. You can't own a short rib. |
| 7 | ARIA | dry, patient | I don't own the cow. I own the recipe. And as of Monday, you're not licensed to serve it. |
| 8 | VANESSA | cold, threatening | I'll call our lawyers. |
| 9 | ARIA | calm | Please do. Ask them about clause fourteen. Dad wrote it. He's very good at contracts. |
| 10 | NARR | amused | She called the lawyers. The lawyers called Dad. Dad called a family dinner. |
| 11 | DANIEL | firm, head of the family | Sit down. Both of you. |
| 12 | VANESSA | outraged | She is holding the business hostage! |
| 13 | DANIEL | quiet, heavy | No, Vanessa. You cut her pay to lease a car, and you forgot to read what you were cutting. That's not a hostage. That's a receipt. |
| 14 | VANESSA | hurt, defensive | You're taking her side? |
| 15 | DANIEL | tired, honest | I'm taking the contract's side. I wrote it for exactly this. I just hoped I'd never need it. |
| 16 | MAYA | urgent, worried | Sorry to interrupt. Elise Marchetti's assistant just called. She's confirming the eighteenth. Party of one. She asked if the short rib is still on. |
| 17 | VANESSA | panicking, quiet | What did you tell her? |
| 18 | MAYA | nervous | I said I'd check with the chef. |
| 19 | NARR | slow, satisfied | For the first time in thirty days, every person in that room looked at me. |
| 20 | VANESSA | swallowing her pride, stiff | What do you want? |
| 21 | ARIA | calm, precise | The recipe fee, back paid. The title Executive Chef. Full control of the kitchen. And a ten percent stake in Harlow and Daughter. |
| 22 | VANESSA | outraged, laughing in disbelief | Ten percent? That's insane. |
| 23 | ARIA | cold, steady | It's cheaper than one bad review. |
| 24 | DANIEL | decisive | Done. And Vanessa, you'll tell the staff yourself. Tomorrow. In person. |
| 25 | NARR | low, triumphant | Vanessa signed with the same pen she'd used to cut my bonus. I watched her hand shake on every letter. |
| 26 | NARR | building tension | Eight days left. One critic. One jar. And a kitchen that finally knew whose food it was cooking. |

Voices: lines 0-1 reuse the takes of 6-7 (cut to the first sentence), so 25
lines to record. Same Fish Drama 3 "Fish B" settings and processing as
`voices/part2/README.md`; Daniel is voice design d2.

## Cast looks

Identical to Part 2 (ARIA, VANESSA, MAYA, DANIEL). Leo and Laurent do not
appear. No new characters.

## New assets needed before generating

| Asset | Why | Prompt |
|---|---|---|
| `set_dining_room` | Daniel's family dinner | Formal family dining room at night: long dark wood table set for three, warm pendant lamp, framed photo of a small old restaurant on the wall, half-drawn curtains, nobody in the room |
| `prop_letter` | The termination notice | Close-up of a single printed letter on a dark desk beside a tablet, text blurred and unreadable, a red manicured hand flattening it |
| `prop_contract_pen` | The signing | Close-up of a fountain pen and a contract page on a dark wood table, warm lamp, text blurred and unreadable |

Existing sets reused: `set_office`, `set_kitchen`.

## Shots

| # | Lines covered | Set | Length | Prompt (picture) |
|---|---|---|---|---|
| 1 | 0–1 (cold open) | office | 15 s | Tight two-shot across a desk: VANESSA leaning forward, scornful, a printed letter crushed in her fist; ARIA standing opposite, completely calm, hands loosely clasped. Static, shallow focus. Use the first 5 s only. |
| 2 | 2 (recap) | office | 15 s | Insert: a yellowed contract page on a desk, a finger resting on one paragraph, lamp light (text blurred, unreadable). Slow push-in. |
| 3 | 3 | Aria's apartment kitchen | 15 s | ARIA at her small kitchen counter at night, laptop open, the jar beside it; she reads the screen once, then presses a key and closes the laptop. Calm, final. |
| 4 | 4–9 | office | 15 s → 45 s | VANESSA bursts through the office door holding a printed letter, heels loud; ARIA is at the filing shelf with a clipboard and turns without hurry. Medium two-shot, slow orbit. Master under the whole exchange; cut to close-ups for each line. |
| 5 | 5, 7, 9 | office | 15 s | Close-up ARIA, calm, patient, the faintest half-smile, steady eye contact off-camera. (Talking close-up.) |
| 6 | 4, 6, 8 | office | 15 s | Close-up VANESSA, furious, then a flicker of doubt, then a cold stare. (Talking close-up.) |
| 7 | 10 | office → dining room | 15 s | VANESSA alone at the desk, phone to her ear, pacing, her face falling as she listens. Then cut: DANIEL's hand setting a phone face-down on a dining table. |
| 8 | 11–15 | dining room (new) | 15 s → 45 s | DANIEL at the head of the table, hands flat on the wood; VANESSA and ARIA on opposite sides, untouched plates. Wide master, slow push-in on Daniel. |
| 9 | 11, 13, 15 | dining room | 15 s | Close-up DANIEL, tired, heavy, looking from one side of the table to the other. (Talking close-up.) |
| 10 | 12, 14 | dining room | 15 s | Close-up VANESSA, outraged, then hurt, eyes shining. (Talking close-up.) |
| 11 | 16, 18 | dining room doorway | 15 s | MAYA in the doorway, coat still on, phone in her hand, apologetic and urgent. (Talking close-up.) |
| 12 | 17, 19 | dining room | 15 s | Slow pan across the table: VANESSA, DANIEL and MAYA all turn their heads toward ARIA, who sits perfectly still. End on Aria. |
| 13 | 20–23 | dining room | 15 s | Close-up ARIA, calm and precise, counting nothing on her fingers, never blinking first. (Talking close-up.) Cut away to shot 10 for Vanessa's lines. |
| 14 | 24–25 | dining room | 15 s | Insert: VANESSA's red-nailed hand signing a contract page with a fountain pen, the hand trembling slightly; DANIEL's hand resting on the table beside it. |
| 15 | 26 (ending) | kitchen, night | 15 s | Empty restaurant kitchen after close, one light on; ARIA sets a white apron on the pass, unfolds it and ties it on. Slow push-in, her back to camera. |

Talking close-ups (5, 6, 9, 10, 11, 13): take a clean frame from the Grok clip
as the InfiniteTalk start image. Every other prompt ends with "no one speaks,
no dialogue, ambient sound only".

Total: 15 shots, about 4.5 min of footage for a ~2:10 episode.

End card: **PART 4 — "THE REVIEW"**.
