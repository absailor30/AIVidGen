# The Stolen Pitch — MiniMax prompts v2 (2 refs per character)

## Settings (every part)
- Model: MiniMax H3 → Ref2VA Pruned 20B → PDD 8-Step
- Text Prompt mode, Reference Images = Use Reference Images, no audio reference
- Resolution 704×1280 (9:16)
- Load references IN THE ORDER LISTED. `<Picture N>` = Nth image.
- Paste prompts exactly, no blank lines inside.

## Reference files
- `X_close` = `{char}_close_front` (Flow)
- `X_ref` = original full-body ref
- Characters facing away from camera get only `X_ref` (face not needed, fewer refs = faster).

## Order of work
Test **1a first**. If the face holds better than before, run the rest. If it looks worse or duplicates the person, tell me — fallback is 1 ref per character (close-up only).

| Part | Length | Frames | References in order |
|---|---|---|---|
| 1a | 7s | ~168 | office_night, maya_close, maya_ref |
| 1b | 6s | ~144 | office_night, vanessa_close, vanessa_ref |
| 2a | 6.5s | ~156 | conference_room, maya_ref, vanessa_close, vanessa_ref, daniel_ref, leo_ref |
| 2b | 4.5s | ~108 | conference_room, maya_close, maya_ref |
| 3a | 4.5s | ~108 | conference_room, vanessa_close, vanessa_ref, daniel_close, daniel_ref |
| 3b | 4.5s | ~108 | conference_room, maya_close, maya_ref, leo_close, leo_ref |
| 4a | 7s | ~168 | office_night, vanessa_close, vanessa_ref |
| 4b | 5s | ~120 | office_night, maya_close, maya_ref |
| 5a | 7.5s | ~180 | conference_room, vanessa_close, vanessa_ref, daniel_close, daniel_ref |
| 5b | 8s | ~192 | conference_room, maya_close, maya_ref, leo_close, leo_ref, vanessa_close, vanessa_ref |
| 6a | 8s | ~192 | corridor, vanessa_ref |
| 6b | 4s | ~96 | corridor, maya_close, maya_ref |

2a: trim first 2s in edit if the wide shot is weak.

---

### 1a — Maya working late
```
subject_definitions:
<Subject 1> is the dark open-plan office at night from <Picture 1>, preserving the desks, desk lamp, city skyline window and dim blue light.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
summary:
[reference generation] A tired woman works alone late at night in a dark office.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - office, lamp, skyline and night lighting.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> late at night. Exactly one person exists in this scene. The laptop screen faces away from the camera.
[Shot 1] Medium close-up, chest up, face large and clear. <Subject 2> sits alone at a desk typing on a laptop, the screen glow lighting her tired but focused face. She pauses, rubs her eyes, then keeps typing. City lights glow softly through the window behind her. Slow camera push-in toward her face.
overall_soundscape: quiet empty office at night, soft laptop keyboard typing, faint air conditioning hum, distant city traffic. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 1b — Vanessa watching from the shadows
```
subject_definitions:
<Subject 1> is the dark open-plan office at night from <Picture 1>, preserving the desks, desk lamp and dim blue light.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, black leather jacket and black leather pants.
summary:
[reference generation] A rival silently watches from the shadows of a dark office at night.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - office and night lighting.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> late at night. Exactly one person exists in this scene.
[Shot 1] Medium shot, waist up, face large and clear. <Subject 2> leans against a desk in the shadows with arms crossed, silently watching something across the room. A desk lamp lights one side of her face. A thin, knowing smirk slowly spreads across her red lips. The camera holds still on her.
overall_soundscape: quiet empty office at night, faint distant keyboard typing, air conditioning hum. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 2a — Meeting wide, Vanessa presents
```
subject_definitions:
<Subject 1> is the bright modern conference room from <Picture 1>, preserving the glass table, wall-mounted presentation screen and daylight windows.
<Subject 2> is the woman from <Picture 2>, preserving her curly shoulder-length black hair and mustard yellow denim jacket.
<Subject 3> is the woman shown in <Picture 3> (face close-up) and <Picture 4> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, black leather jacket, black leather pants and red stiletto heels.
<Subject 4> is the man from <Picture 5>, preserving his short silver hair and navy blue three-piece suit.
<Subject 5> is the young man from <Picture 6>, preserving his messy ginger hair and bright green hoodie.
summary:
[reference generation] An office meeting where a woman confidently presents a pitch to her team.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - room layout and daylight.
<Subject 2> (appears in [Shot 1]): partially_preserved - seen from behind, curly black hair and yellow jacket.
<Subject 3> (appears in [Shot 1], [Shot 2]): fully_preserved - face, hair and outfit.
<Subject 4> (appears in [Shot 1]): partially_preserved - seen from behind, silver hair and navy suit.
<Subject 5> (appears in [Shot 1]): partially_preserved - seen from behind, ginger hair and green hoodie.
detailed_description:
The target video is a vertical cinematic sequence in <Subject 1> in daytime. Exactly four people are in the room, each appearing only once. The presentation screen shows abstract charts and colored shapes only, no readable text, no words, no letters.
[Shot 1] Brief wide establishing shot from behind the glass table. <Subject 2>, <Subject 4> and <Subject 5> sit at the table with their backs to the camera, seen from behind: curly black hair and yellow jacket, silver hair and navy suit, ginger hair and green hoodie. At the far end of the room, <Subject 3> stands confidently beside the presentation screen, facing the team. Static camera.
[Shot 2] At 00:02.000, cut to a medium shot, waist up, of <Subject 3> presenting at the screen, clicking a small remote with a proud smile, gesturing at the abstract bar charts behind her. Only she is visible.
overall_soundscape: quiet meeting room tone, a remote control click, soft air conditioning. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 2b — Maya close-up, silent
```
subject_definitions:
<Subject 1> is the bright modern conference room from <Picture 1>, preserving the glass table and daylight windows.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
summary:
[reference generation] A woman sits silently in a meeting, watching in quiet disbelief.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - room and daylight.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic close-up in <Subject 1> in daytime. Exactly one person is visible.
[Shot 1] Close-up of <Subject 2> sitting still at the glass table, jaw tight, eyes fixed on something in front of her, saying nothing. Her face shows quiet disbelief that slowly hardens into calm resolve. Soft daylight from the window on her face, blurred room behind her. Slow push-in.
overall_soundscape: quiet meeting room tone, faint air conditioning. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 3a — Daniel approves, Vanessa proud
```
subject_definitions:
<Subject 1> is the bright modern conference room from <Picture 1>, preserving the glass table and daylight windows.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, black leather jacket and black leather pants.
<Subject 3> is the man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, short silver hair, silver beard, navy blue three-piece suit and burgundy tie.
summary:
[reference generation] A boss approves a presentation while the presenter smiles proudly beside him.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - room and daylight.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 1]): fully_preserved - face, hair, beard and suit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> in daytime. Exactly two people are visible, each appearing only once, both framed from the waist up with their faces large and clear in the frame.
[Shot 1] Medium two-shot, waist up. <Subject 3> sits at the head of the glass table, nodding slowly and approvingly with a satisfied expression. <Subject 2> stands close beside him, smiling proudly, one hand resting on the table. Static camera.
overall_soundscape: quiet meeting room tone, soft air conditioning. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 3b — Leo confused, Maya calm
```
subject_definitions:
<Subject 1> is the bright modern conference room from <Picture 1>, preserving the glass table and daylight windows.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
<Subject 3> is the young man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, messy ginger hair, freckles, round black glasses and bright green hoodie with ID lanyard.
summary:
[reference generation] A young man stares in confusion at his silent, calm coworker during a meeting.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - room and daylight.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 1]): fully_preserved - face, hair, glasses and hoodie.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> in daytime. Exactly two people are visible, each appearing only once, both framed from the chest up with their faces large and clear in the frame.
[Shot 1] Medium close two-shot, chest up, of <Subject 3> and <Subject 2> sitting side by side at the glass table. <Subject 3> turns his head to stare at <Subject 2> with raised eyebrows and an open mouth, clearly confused. <Subject 2> keeps looking straight ahead, calm and silent, the faintest hint of a smile.
overall_soundscape: quiet meeting room tone, a chair creaking softly. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 4a — Flashback, Vanessa copies files
```
subject_definitions:
<Subject 1> is the dark open-plan office at night from <Picture 1>, preserving the desks, desk lamp, city skyline window and dim light.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, red fingernails, black leather jacket and black leather pants.
summary:
[reference generation] A flashback where a woman secretly copies files from a colleague's laptop at night.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - office and night lighting.
<Subject 2> (appears in [Shot 1], [Shot 2]): fully_preserved - face, hair, nails and outfit.
detailed_description:
The target video is a vertical flashback sequence in <Subject 1> at night, with a desaturated cool blue color grade and slight soft focus to feel like a memory. Exactly one person exists in this scene. The laptop screen shows only abstract icons and a progress bar, no readable text, no words, no letters.
[Shot 1] Medium shot, waist up, face large and clear. <Subject 2> sits at an empty desk that is not hers, lit by the laptop glow, glancing nervously over her shoulder, then plugs a small USB drive into the open laptop. Handheld camera, slightly shaky.
[Shot 2] At 00:04.000, cut to a close-up of the laptop screen showing a progress bar filling up, <Subject 2>'s red fingernails tapping impatiently on the desk beside it.
overall_soundscape: silent office at night, soft keyboard clicks, faint computer hum. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 4b — Flashback, Maya watching
```
subject_definitions:
<Subject 1> is the dark open-plan office at night from <Picture 1>, preserving the desks, dim light and city skyline window.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair and mustard yellow denim jacket.
summary:
[reference generation] A flashback where a woman silently watches from a dark doorway.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - office and night lighting.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and jacket.
detailed_description:
The target video is a vertical flashback shot in <Subject 1> at night, with a desaturated cool blue color grade and slight soft focus to feel like a memory. Exactly one person exists in this scene.
[Shot 1] Medium shot, chest up, face large and clear. <Subject 2> stands half in the shadow of a dark doorway, completely still, silently watching something across the room. Her yellow jacket is dimly visible, her face lit faintly by a distant screen glow, her expression calm and knowing. Very slow push-in.
overall_soundscape: silent office at night, faint computer hum. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 5a — Wrong number, Daniel stops her
```
subject_definitions:
<Subject 1> is the bright modern conference room from <Picture 1>, preserving the glass table, presentation screen and daylight windows.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, black leather jacket, black leather pants and red stiletto heels.
<Subject 3> is the man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, short silver hair, silver beard, navy blue three-piece suit and burgundy tie.
summary:
[reference generation] A confident presenter points at a revenue chart until her boss suspiciously stops her.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - room and daylight.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 2]): fully_preserved - face, hair, beard and suit.
detailed_description:
The target video is a vertical cinematic sequence in <Subject 1> in daytime. Each person appears only once, framed from the waist up with their face large and clear. The presentation screen shows only colorful abstract bar charts, no readable text, no words, no letters, no numbers.
[Shot 1] Medium shot, waist up, of <Subject 2> standing at the presentation screen, confidently pointing at a large abstract bar chart, smiling. Only she is visible.
[Shot 2] At 00:04.000, cut to a medium close-up of <Subject 3> seated at the head of the table. He raises one hand to stop her and frowns hard at the screen, suspicious. Only he is visible.
overall_soundscape: quiet meeting room tone, a pen set down on glass. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 5b — Maya and Leo stand, Vanessa freezes
```
subject_definitions:
<Subject 1> is the bright modern conference room from <Picture 1>, preserving the glass table and daylight windows.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket, white t-shirt and dark blue jeans.
<Subject 3> is the young man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, messy ginger hair, freckles, round black glasses and bright green hoodie with ID lanyard.
<Subject 4> is the woman shown in <Picture 6> (face close-up) and <Picture 7> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick and black leather jacket.
summary:
[reference generation] Two colleagues stand up to reveal the truth while the guilty presenter freezes in shock.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - room and daylight.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 1]): fully_preserved - face, hair, glasses and hoodie.
<Subject 4> (appears in [Shot 2]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic sequence in <Subject 1> in daytime. Each person appears only once, with faces large and clear in the frame. The laptop screen shows only an abstract list of colored file icons, no readable text, no words, no letters.
[Shot 1] Medium two-shot, waist up: <Subject 2> calmly stands up from her chair, and <Subject 3> stands up close beside her, holding up an open laptop with its screen facing forward. Only these two people are visible.
[Shot 2] At 00:04.000, cut to a close-up of <Subject 4>'s face. Her smile collapses, her eyes widen in shock and her lips part. She is completely frozen. Slow push-in. Only she is visible.
overall_soundscape: tense quiet room, a chair scraping back, a sharp intake of breath. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 6a — Vanessa walks out
```
subject_definitions:
<Subject 1> is the modern office corridor from <Picture 1>, preserving the polished floor, glass wall, cool white lighting and elevator doors at the far end.
<Subject 2> is the woman from <Picture 2>, preserving her sleek platinum blonde hair, black leather jacket, black leather pants and glossy red stiletto heels.
summary:
[reference generation] A disgraced woman walks away down a corridor toward an elevator.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - corridor, floor, lighting and elevator.
<Subject 2> (appears in [Shot 1], [Shot 2]): partially_preserved - seen from behind, hair, outfit and red heels.
detailed_description:
The target video is a vertical cinematic sequence in <Subject 1>. Exactly one person exists in this scene, always seen from behind.
[Shot 1] <Subject 2> walks quickly away from the camera down the long corridor toward the elevator, her back to us, platinum hair swinging. Static camera, symmetrical framing.
[Shot 2] At 00:04.500, cut to a low close-up at floor level of her glossy red stiletto heels striking the polished floor with each step, walking away.
overall_soundscape: sharp echoing high-heel clicks on a hard floor. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 6b — Maya satisfied
```
subject_definitions:
<Subject 1> is the modern office corridor from <Picture 1>, preserving the polished floor, glass wall, cool white lighting and elevator doors at the far end.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
summary:
[reference generation] A woman stands calmly in a corridor with a satisfied smile as elevator doors close behind her.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - corridor and elevator.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1>. Exactly one person is visible.
[Shot 1] Medium shot, chest up, face large and clear. <Subject 2> stands at the near end of the corridor, arms crossed, a calm satisfied smile. Far behind her, out of focus, the elevator doors slide closed. Slow push-in.
overall_soundscape: soft elevator chime, doors sliding shut, quiet corridor tone. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```
