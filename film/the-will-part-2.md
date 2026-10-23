# THE WILL — Part 2: "The Witness"

**Format:** 16:9 (1280×720 at 24 fps), no narrator, dialogue only
**Runtime:** about 3 min 52 s (34 shots) plus a 4-second end card
**Cast:** Maya, Vanessa, Daniel, Leo (the four existing characters, nobody else on screen)
**Place:** Daniel's home study, late at night, rain on the window
**Style:** a quiet legal thriller. Warm lamp light against cold blue window light. Slow, deliberate camera. Every line is short, because short lines survive AI lip-sync better.

---

## 1. What Part 1 must have established

Part 2 starts at the exact moment Part 1 ends. If Part 1 is written differently, adjust the first scene only.

- **Daniel Hale (55)** is the founder of Hale Legal, a law firm. After a heart scare in the spring, he read his will aloud to the family. The real will leaves **Maya 51% of the firm** and the family house to Vanessa, with cash for Leo's studies.
- **Maya (34)**, his eldest daughter, has run the firm's day-to-day for six years.
- **Vanessa (32)**, her younger sister, feels entitled to the firm and has never worked a full year anywhere.
- **Leo (24)** is their younger brother and Daniel's assistant. He handles the firm's documents and computers.
- Last week a **"page 7"** surfaced that hands Vanessa voting control of the firm "in the event of a conflict of interest" involving Maya. It carries Daniel's signature and a notary stamp.
- Part 1 ends in this study. Maya is holding page 7. She has just told Vanessa: "You forged this."

Recurring motif for the whole film: **2:47 AM** (the time of Daniel's heart scare). It pays off at the very end of this part.

---

## 2. Voice designs (one frozen reference clip per character)

Generate each voice once from the description, pick a take you like, then reuse that clip as the voice reference for everything. Do not re-design voices between shots.

| Character | Voice description (for a voice-design model) |
|---|---|
| **Maya** | Warm, low-mid female voice, about 34. Calm, measured, American accent. Controlled under pressure; her voice cracks slightly when hurt. Never shouts. |
| **Vanessa** | Smooth, confident female voice, about 32. Slightly nasal, quick, polished American accent. Sarcastic. When angry she drops to a cold whisper before she explodes. |
| **Daniel** | Deep, gravelly male baritone, about 55. Slow and unhurried, a lawyer's precision. Weary and kind, never loud. Long pauses before important words. |
| **Leo** | Lighter male tenor, about 24. Quick, nervous energy, a little stammer when scared. Honest and slightly geeky. |

For a multi-speaker model, tag them **[S1] Maya, [S2] Vanessa, [S3] Daniel, [S4] Leo**.

---

## 3. Shot types (how to run each)

| Code | Meaning | How to make it |
|---|---|---|
| **D1** | One character speaks to camera or slightly off-camera | Still of the character + that line's audio → talking-video model (LongCat-Video-Avatar or InfiniteTalk). One speaker per shot keeps lip-sync clean. |
| **R** | Silent reaction | Still of the character, short image-to-video clip (Wan 2.2 or Bernini-R) with the expression in the prompt. No audio, only room tone. |
| **B** | Silent establishing shot or insert (no face speaking) | Image-to-video or text-to-video with the prompt given. |
| **T** | Title or text card | Make in the editor (HyperFrames or any editing tool). No model needed. |

Conversations are cut as **shot / reverse-shot** (one speaker per shot, then the listener's reaction), not two speakers in one frame. That is on purpose: current open models handle one or two speakers reliably, and cutting between them also hides small identity drift.

**Costumes (use exactly these, every shot):**
- **Maya:** soft cream knit sweater, light-blue jeans, tan heeled mules, hair curly and shoulder-length. Page 7 in her right hand.
- **Vanessa:** black leather biker jacket, black leather pants, platinum-blonde straight hair, red lipstick, silver hoops.
- **Daniel:** navy cable-knit sweater over a white collared shirt, grey trousers, silver watch, short silver hair and trimmed silver beard.
- **Leo:** bright-green hoodie, round black glasses, lanyard with a blank badge, messy ginger hair and freckles, laptop on his knees.

**Reference images to attach** (names as in the Cast Reference Tracker): `<name>_ref` (full body), `<name>_close`, `<name>_34L`, `<name>_medium`, and the expression shots `<name>_smug`, `_angry`, `_shock`, `_sad`, `_smile`. For the "at home" outfits use `<name>_home_ref`, `_home_close`, `_home_medium` (Maya, Daniel) and the base images for Vanessa and Leo.

---

## 4. Shot list

Each shot gives: **duration**, **type**, **in frame**, the **video prompt**, the **dialogue** (with delivery), and **notes**. Durations include a half-second of breathing room.

### Scene A: "The Stamp" (0:00 – 1:40)

**S01 · 4 s · T · Title card**
Black screen, the words **THE WILL** fading in, then smaller beneath: **Part 2 · The Witness**. Low piano note, rain begins.
Notes: no model needed. Hold 1 s of silence before the piano.

**S02 · 6 s · T · "Previously"**
Three quick cuts from Part 1 (reuse existing Part 1 stills or clips): Daniel reading the will, the forged page 7, Maya's face. Small white caption over each: *"A will was read."* → *"Page 7 changed everything."* → *"Maya found the forgery."*
Notes: if Part 1 is not finished, use the character stills with a slow push-in.

**S03 · 6 s · B · Establishing, the study**
Prompt: *"Wide shot of a dark wood-paneled home study at night, rain streaking the tall window behind a heavy desk, a single warm desk lamp, leather chairs, bookshelves full of law books. Maya stands in the center holding a sheet of paper, Vanessa leans against the bookshelf, Leo sits on a leather chair with a laptop. Slow push-in, cinematic, shallow depth of field."*
Audio: rain, distant thunder, lamp hum.
Refs: `maya_home_ref`, `vanessa_ref`, `leo_ref`. Fix the three positions here and reuse them in every later shot.

**S04 · 8 s · D1 · Vanessa, medium**
Prompt: *"Medium shot of Vanessa leaning against a bookshelf with her arms crossed, smirking, warm lamp light on one side of her face, rain-lit window behind her. Subtle head movement, eyes steady on the camera."*
**VANESSA** (amused, silky): "Forged? That's a serious word, Maya. Dad signed that page. There's a notary stamp. Go ahead, call it fake."
Refs: `vanessa_medium`, `vanessa_smug`.

**S05 · 6 s · R · Maya close**
Prompt: *"Close-up of Maya looking down at a sheet of paper, jaw tight, her thumb pressing on a round notary stamp, lamp light on her face. Very slight breathing movement."*
No dialogue. Room tone only.
Refs: `maya_home_close`.

**S06 · 8 s · D1 · Leo, medium (laptop)**
Prompt: *"Medium shot of Leo on a leather chair with a laptop on his knees, round glasses reflecting the screen, nervous, glancing up at the camera."*
**LEO** (nervous, quick): "The stamp says Harold Pryce, March third. But the firm's notary register has no entry that day. Not one. I checked it twice."
Refs: `leo_ref`, `leo_close`.

**S07 · 5 s · R · Vanessa close**
Prompt: *"Close-up of Vanessa; her smirk flickers for a moment and her eyes flick toward the door, then she recovers."*
No dialogue.
Refs: `vanessa_close`, `vanessa_smug`.

**S08 · 9 s · D1 · Vanessa, close**
Prompt: *"Close-up of Vanessa, patient and condescending, slightly tilting her head, lamp light catching the silver hoop earrings."*
**VANESSA** (soft, dismissive, then sharper): "A clerical miss. Dad's office is a mess. Everyone knows he's been slipping. Honestly, Maya, a court might say he wasn't himself."
Refs: `vanessa_close`.

**S09 · 7 s · D1 · Maya, close**
Prompt: *"Close-up of Maya, eyes glassy, trying to stay composed, the page trembling very slightly at the edge of the frame."*
**MAYA** (quiet, voice cracking on "him"): "You'd call him incompetent. To protect a page you wrote."
Refs: `maya_home_close`, `maya_sad`.

**S10 · 6 s · D1 · Vanessa, extreme close**
Prompt: *"Extreme close-up of Vanessa's face, cold stare, barely moving."*
**VANESSA** (cold whisper): "I'd call him tired. And you, a daughter who wanted the firm badly enough to stage this."
Refs: `vanessa_close`, `vanessa_angry`.

**S11 · 5 s · D1 · Leo hears something**
Prompt: *"Medium shot of Leo suddenly looking toward the study door off-camera, eyes widening behind his glasses."*
**LEO** (barely audible): "Maya... someone's at the door."
Sound: floorboard creak.
Refs: `leo_ref`, `leo_shock`.

### Scene B: "The Man Who Signed It" (1:40 – 3:00)

**S12 · 6 s · B · The door**
Prompt: *"Dark hallway seen from inside the study, the heavy wooden door slowly opening, the silhouette of an older man in a sweater backlit by a hallway light, rain sound, no face visible yet."*
Audio: slow footsteps, door hinge.

**S13 · 8 s · D1 · Daniel, medium, in the doorway**
Prompt: *"Medium shot of Daniel in the doorway, navy cable-knit sweater, silver beard, calm and tired eyes, hallway light behind him, very slow push-in."*
**DANIEL** (low, slow, unhurried): "A court would want to hear from the man who signed it, Vanessa. I happen to be standing right here."
Refs: `daniel_home_ref`, `daniel_home_medium`.

**S14 · 5 s · R · Vanessa, color drains**
Prompt: *"Close-up of Vanessa as her face freezes, eyes wide, the smirk dissolving, breathing quickens."*
Refs: `vanessa_shock`.

**S15 · 9 s · D1 · Vanessa, caught**
Prompt: *"Medium close-up of Vanessa, fumbling, one hand rising as if to explain, voice unsteady."*
**VANESSA** (stammering, too fast): "Dad. I... we were just... Maya is accusing me of something insane. You know how she gets."
Refs: `vanessa_medium`, `vanessa_shock`.

**S16 · 8 s · D1 · Daniel walks to the desk**
Prompt: *"Medium shot of Daniel crossing the study and sitting down heavily behind the desk, lamp light on his face, hands folded on the desk."*
**DANIEL** (even, tired): "I heard. Sit down, please. Leo, you can close the laptop. Not because you're wrong, son. Because I never signed page seven."
Refs: `daniel_home_medium`.

**S17 · 8 s · D1 · Daniel opens the drawer**
Prompt: *"Close-up on Daniel's hands opening a desk drawer and lifting out a single sheet of paper, then a slow tilt up to his face, serious."*
**DANIEL** (quiet, deliberate): "I know what page seven really says. And I know who wrote this one. I left a draft in a folder on my desk for four months. The folder said, 'Do not open.'"
Refs: `daniel_home_close`.

**S18 · 6 s · B · Insert, the forged page**
Prompt: *"Extreme close-up of a typed legal page on a dark wooden desk, a red pen circling one line that reads 'Section 11-B', a hand holding the pen steady, lamp light, shallow depth of field."*
Audio: pen tapping twice.
Notes: have the typed line read exactly "Section 11-B". If the model garbles text, add the words in the editor.

**S19 · 9 s · D1 · Daniel, the trap**
Prompt: *"Close-up of Daniel, calm, almost sad, a very slight shake of the head, lamp light flickering faintly."*
**DANIEL** (measured): "I put one mistake in that draft. A reference to a section that doesn't exist. Only someone who copied my draft would repeat it. Look at your page, Maya. Line four."
Refs: `daniel_home_close`.

**S20 · 5 s · R · Maya reads**
Prompt: *"Close-up of Maya's eyes moving along the page, then widening as she finds the line."*
Refs: `maya_home_close`, `maya_shock`.

**S21 · 6 s · D1 · Maya, whisper**
Prompt: *"Close-up of Maya, stunned, voice barely above a whisper, the page lowering slowly."*
**MAYA** (whisper): "Section eleven-B." (a beat) "It doesn't exist."
Refs: `maya_home_close`, `maya_shock`.

**S22 · 6 s · R · Vanessa, crumples then hardens**
Prompt: *"Close-up of Vanessa's face crumpling for a second, tears starting, then her jaw setting hard and her eyes turning cold."*
Refs: `vanessa_sad`, `vanessa_angry`.

**S23 · 9 s · D1 · Vanessa explodes**
Prompt: *"Medium close-up of Vanessa furious and teary, pointing at Daniel, rain-lit window behind her."*
**VANESSA** (rising to a shout): "You set me up? You left it there like bait? What kind of father does that?"
Refs: `vanessa_angry`, `vanessa_medium`.

**S24 · 10 s · D1 · Daniel, the heart of it**
Prompt: *"Close-up of Daniel, eyes wet but steady, completely still, lamp light on one side of his face."*
**DANIEL** (very quiet, long pauses): "The kind who spent four months hoping you wouldn't touch it. You could have asked me for anything, Vanessa. Anything. You chose a pen."
Refs: `daniel_home_close`, `daniel_sad`.
Notes: the emotional peak. Cut the music to near silence here.

### Scene C: "The Choice" (3:00 – 3:52)

**S25 · 5 s · B · Beat of silence**
Prompt: *"Wide shot of the study, nobody moving, rain on the window, a distant rumble of thunder, the lamp slowly flickering."*
Audio: rain, thunder; no music.

**S26 · 9 s · D1 · Daniel states terms**
Prompt: *"Medium shot of Daniel behind the desk, hands folded, steady and formal, a lawyer's voice."*
**DANIEL** (formal, steady): "Here is what happens. You resign from the firm tonight. You sign a statement, in front of a witness, that you altered the will. It goes in the vault. Contest anything, and it goes to the police."
Refs: `daniel_home_medium`.

**S27 · 7 s · D1 · Vanessa, defiant**
Prompt: *"Close-up of Vanessa, tears running, chin raised, defiant."*
**VANESSA** (bitter, wavering): "And if I don't sign?"
Refs: `vanessa_close`, `vanessa_sad`.

**S28 · 7 s · D1 · Daniel**
Prompt: *"Close-up of Daniel, tired, resigned, not cruel."*
**DANIEL** (flat, regretful): "Then Leo's register, the file history, and your fingerprints on that folder go to the prosecutor in the morning. I would rather they didn't."
Refs: `daniel_home_close`.

**S29 · 5 s · D1 · Leo, a breath of humor**
Prompt: *"Medium shot of Leo hugging his laptop, nervous half-smile, glancing between the others."*
**LEO** (quick, sheepish): "It's backed up. Three places. One of them is my sock."
Refs: `leo_ref`, `leo_smile`.
Notes: the one light moment. Keep the beat short.

**S30 · 6 s · D1 · Vanessa at the door**
Prompt: *"Medium shot of Vanessa pulling on her black leather jacket and stopping with one hand on the door, then turning with a bitter half-laugh."*
**VANESSA** (bitter laugh, then cold): "Fine. But you think I could get into your files, Dad? I can't even guess your password."
Refs: `vanessa_ref`, `vanessa_smug`.

**S31 · 6 s · R · Daniel freezes**
Prompt: *"Close-up of Daniel; his face goes still and his eyes slowly lift as if he has just understood something terrible."*
Refs: `daniel_home_close`, `daniel_shock`.

**S32 · 8 s · D1 · Leo, the log**
Prompt: *"Close-up of Leo, face lit blue by the laptop screen, pale, reading the screen with disbelief."*
**LEO** (low, shaky): "Maya... the draft wasn't opened from the folder. It was opened from Dad's own login. At two forty-seven in the morning. The night of his heart scare."
Refs: `leo_close`, `leo_shock`.

**S33 · 8 s · D1 · Daniel, the password**
Prompt: *"Medium close-up of Daniel looking slowly across the room at Maya, a long silence, rain in the background."*
**DANIEL** (very quiet, each word heavy): "Only two people know that password. Me." (long pause) "And Maya."
Refs: `daniel_home_medium`.

**S34 · 6 s · R · The sting**
Prompt: *"Close-up of Maya, shocked, the page slipping from her fingers; behind her in soft focus Vanessa smiles in the doorway. Slow push-in on Maya."*
Audio: single low string note, rain cuts out.
Then fade to black and an end card (below).

**End card · 4 s · T**
White text on black: **"THE WILL"** then **"Part 3 · The Password"**. Subtitle: *"Who opened the file?"*

---

## 5. Dialogue script for text-to-speech

Use this block if your voice model takes a whole script with speaker tags. Cut per shot afterwards; the shot IDs in brackets match section 4.

```
[S2] Forged? That's a serious word, Maya. Dad signed that page. There's a notary stamp. Go ahead, call it fake.            (S04)
[S4] The stamp says Harold Pryce, March third. But the firm's notary register has no entry that day. Not one. I checked it twice.   (S06)
[S2] A clerical miss. Dad's office is a mess. Everyone knows he's been slipping. Honestly, Maya, a court might say he wasn't himself.   (S08)
[S1] You'd call him incompetent. To protect a page you wrote.                                                              (S09)
[S2] I'd call him tired. And you, a daughter who wanted the firm badly enough to stage this.                               (S10)
[S4] Maya... someone's at the door.                                                                                       (S11)
[S3] A court would want to hear from the man who signed it, Vanessa. I happen to be standing right here.                   (S13)
[S2] Dad. I... we were just... Maya is accusing me of something insane. You know how she gets.                             (S15)
[S3] I heard. Sit down, please. Leo, you can close the laptop. Not because you're wrong, son. Because I never signed page seven.   (S16)
[S3] I know what page seven really says. And I know who wrote this one. I left a draft in a folder on my desk for four months. The folder said, "Do not open."   (S17)
[S3] I put one mistake in that draft. A reference to a section that doesn't exist. Only someone who copied my draft would repeat it. Look at your page, Maya. Line four.   (S19)
[S1] Section eleven-B. ... It doesn't exist.                                                                              (S21)
[S2] You set me up? You left it there like bait? What kind of father does that?                                            (S23)
[S3] The kind who spent four months hoping you wouldn't touch it. You could have asked me for anything, Vanessa. Anything. You chose a pen.   (S24)
[S3] Here is what happens. You resign from the firm tonight. You sign a statement, in front of a witness, that you altered the will. It goes in the vault. Contest anything, and it goes to the police.   (S26)
[S2] And if I don't sign?                                                                                                  (S27)
[S3] Then Leo's register, the file history, and your fingerprints on that folder go to the prosecutor in the morning. I would rather they didn't.   (S28)
[S4] It's backed up. Three places. One of them is my sock.                                                                 (S29)
[S2] Fine. But you think I could get into your files, Dad? I can't even guess your password.                               (S30)
[S4] Maya... the draft wasn't opened from the folder. It was opened from Dad's own login. At two forty-seven in the morning. The night of his heart scare.   (S32)
[S3] Only two people know that password. Me. ... And Maya.                                                                 (S33)
```

About 520 spoken words in total.

---

## 6. Sound and music

- **Room bed (all scenes):** steady rain on glass, faint desk-lamp hum, a distant clock. Keep it low and continuous so cuts between shots do not jump.
- **Music:** a sparse, low piano and cello thriller bed under Scene A (very quiet). Let it swell slightly at the door opening (S12). **Cut the music almost entirely under S24**, the emotional peak. A single low string sting at S34.
- **Effects:** floorboard creak (S11), door hinge and footsteps (S12), pen tap twice (S18), thunder rumble (S25), laptop keys (S06, S32).
- **Loudness:** dialogue peaks around -6 dB, music about -24 dB under speech.
- **Safe music sources:** use a track you have the license to use (the YouTube Audio Library tracks already in the repo work), or generate one with an openly licensed music model.

## 7. Editing and captions

- Cut straight, no flashy transitions. Hold reaction shots 4–6 seconds; they carry the acting.
- Hard captions, bottom third, white text with a thin dark outline, lines of at most 7 words, no word-by-word highlight (this is a drama, not a Short).
- Add a 1-second fade from black at the start and out to black at the end.
- **Chapters** (for the YouTube description):
  - 0:00 The Stamp
  - 1:40 The Man Who Signed It
  - 3:00 The Choice
- Disclosure: set the "altered or synthetic content" label in YouTube Studio, since the people and voices are realistic AI-generated.

## 8. Quality checks before publishing

1. **Faces:** compare each shot against the reference still. If a face drifts, regenerate from `<name>_ref` and shorten the clip rather than lengthening it.
2. **Voices:** play all of one character's lines back to back. They must sound like one person.
3. **Lips:** watch each D1 shot with the sound off, then on. Re-run any shot where the mouth shapes are wrong.
4. **Costumes and set:** the same sweater, the same bookshelf, the same lamp. Mismatches show up fast when cutting.
5. **The Section 11-B line** in S18 and the password line in S33 are the two plot-critical beats. If either is unclear, redo it before anything else.

## 9. Suggested RunPod order of work

1. Design the four voices and save one reference clip each.
2. Generate each dialogue line (section 5) as its own audio file, named by shot ID (`S04.wav`).
3. Run the D1 shots: reference still + that shot's audio → talking video. Do the easy ones first (Daniel, Maya), then Vanessa, then Leo.
4. Run the R and B shots (silent clips).
5. Assemble in order, add the room bed, music and captions, then export 1280×720 at 24 fps.
6. Watch it once straight through and fix the weakest three shots first.

Settings such as step counts, resolution and memory depend on the model and GPU you rent. Benchmark one shot first and note the time per second of video before queuing the rest.

---

**Part 3 teaser (for the next script):** the password was known only to Daniel and Maya. Who used it at 2:47 AM, and why is Vanessa smiling?
