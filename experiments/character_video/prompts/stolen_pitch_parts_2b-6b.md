# The Stolen Pitch — MiniMax prompts v3 (remaining parts, background test)

Same settings as before (MiniMax H3 → Ref2VA Pruned 20B → PDD 8-Step, Text Prompt, Use Reference Images, no audio ref, 704×1280). Load references IN THE ORDER LISTED.

Every prompt forbids the empty-background opening. From 3b on, every [Shot 1] also says "Nobody looks at the camera." (5b's Vanessa close-up in Shot 2 may face the lens).

Shortcut for 3b/5b: instead of making `conference_room_reverse` in Flow, you can use a frame from the finished 3a as the background image.

## Background test — 3 methods

| Method | What it does | Used in |
|---|---|---|
| **A — Style ref** | Room image is only a style reference; camera angle is free, model invents the rest | 3a, 4a, 5a, 6b |
| **B — Extra angle** | New reverse-angle room image from Flow, used as the background | 3b, 5b |
| **C — No BG ref** | Room described in text only, shallow focus | 2b, 4b |
| Original (exact) | Copies the room image (needed for the elevator) | 6a |

### Make this first in Flow (for method B)
Attach `Meeting room 1`, Portrait 9:16, Nano Banana Pro:
```
The exact same conference room from the reference image, same glass table, same chairs, same materials and daylight, but seen from the reverse angle: camera standing near the presentation screen, looking back toward the glass table and the windows. No people. Photorealistic.
```
Save as `conference_room_reverse`.

| Part | Method | Length | Frames | References in order |
|---|---|---|---|---|
| 2b | C | 4.5s | ~108 | maya_close, maya_ref |
| 3a | A | 4.5s | ~108 | conference_room, vanessa_close, vanessa_ref, daniel_close, daniel_ref |
| 3b | B | 4.5s | ~108 | conference_room_reverse, maya_close, maya_ref, leo_close, leo_ref |
| 4a | A | 7s | ~168 | office_night, vanessa_close, vanessa_ref |
| 4b | C | 5s | ~120 | maya_close, maya_ref |
| 5a | A | 7.5s | ~180 | conference_room, vanessa_close, vanessa_ref, daniel_close, daniel_ref |
| 5b | B | 8s | ~192 | conference_room_reverse, maya_close, maya_ref, leo_close, leo_ref, vanessa_close, vanessa_ref |
| 6a | Original | 8s | ~192 | corridor, vanessa_ref |
| 6b | A | 4s | ~96 | corridor, maya_close, maya_ref |

---

### 2b — Maya close-up, silent (C: no BG ref)
```
subject_definitions:
<Subject 1> is the woman shown in <Picture 1> (face close-up) and <Picture 2> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
summary:
[reference generation] A woman sits silently in a daytime meeting, watching in quiet disbelief.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic close-up inside a bright modern glass-walled conference room in daytime, with large windows and soft daylight, shallow depth of field, the background softly blurred. Exactly one person is visible. From the very first frame, she is already in position; no empty establishing shot, nobody walks into frame.
[Shot 1] Close-up of <Subject 1> sitting still at a glass table, jaw tight, eyes fixed on something in front of her, saying nothing. Her face shows quiet disbelief that slowly hardens into calm resolve. Soft daylight from the window on her face. Slow push-in.
overall_soundscape: quiet meeting room tone, faint air conditioning. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 3a — Daniel approves, Vanessa proud (A: style ref) — DONE, kept
```
subject_definitions:
<Subject 1> is the conference room from <Picture 1>, used only as a style reference for the room's materials, colors and daylight; the room may be seen from any angle, with new parts of the room invented to match.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, black leather jacket and black leather pants.
<Subject 3> is the man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, short silver hair, silver beard, navy blue three-piece suit and burgundy tie.
summary:
[reference generation] A boss approves a presentation while the presenter smiles proudly beside him.
retention_analysis:
<Subject 1> (appears in [Shot 1]): partially_preserved - style, materials and lighting only, camera angle free.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 1]): fully_preserved - face, hair, beard and suit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> in daytime. Exactly two people are visible, each appearing only once, both framed from the waist up with their faces large and clear in the frame. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Medium two-shot, waist up, three-quarter angle. <Subject 3> sits at the head of the glass table, nodding slowly and approvingly with a satisfied expression. <Subject 2> stands close beside him, smiling proudly, one hand resting on the table. The camera slowly arcs a little around them, revealing more of the room behind.
overall_soundscape: quiet meeting room tone, soft air conditioning. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 3b — Leo confused, Maya calm (B: reverse angle)
```
subject_definitions:
<Subject 1> is the conference room from <Picture 1>, preserving the glass table, chairs, windows and daylight from this reverse angle.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
<Subject 3> is the young man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, messy ginger hair, freckles, round black glasses and bright green hoodie with ID lanyard.
summary:
[reference generation] A young man stares in confusion at his silent, calm coworker during a meeting.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - room and daylight.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 1]): fully_preserved - face, hair, glasses and hoodie.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1> in daytime. Exactly two people are visible, each appearing only once, both framed from the chest up with their faces large and clear in the frame. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Medium close two-shot, chest up, of <Subject 3> and <Subject 2> sitting side by side at the glass table, facing the camera, windows behind them. <Subject 3> turns his head to stare at <Subject 2> with raised eyebrows and an open mouth, clearly confused. <Subject 2> keeps looking straight ahead, calm and silent, the faintest hint of a smile. Nobody looks at the camera.
overall_soundscape: quiet meeting room tone, a chair creaking softly. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 4a — Flashback, Vanessa copies files (A: style ref)
```
subject_definitions:
<Subject 1> is the office from <Picture 1>, used only as a style reference for the room's materials, colors and night lighting; the room may be seen from any angle, with new parts of the room invented to match.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, red fingernails, black leather jacket and black leather pants.
summary:
[reference generation] A flashback where a woman secretly copies files from a colleague's laptop at night.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): partially_preserved - style, materials and night lighting only, camera angle free.
<Subject 2> (appears in [Shot 1], [Shot 2]): fully_preserved - face, hair, nails and outfit.
detailed_description:
The target video is a vertical flashback sequence in <Subject 1> at night, with a desaturated cool blue color grade and slight soft focus to feel like a memory. Exactly one person exists in this scene. The laptop screen shows only abstract icons and a progress bar, no readable text, no words, no letters. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Medium shot, waist up, three-quarter angle, face large and clear. <Subject 2> already sits at an empty desk that is not hers, lit by the laptop glow, glancing nervously over her shoulder, then plugs a small USB drive into the open laptop. Handheld camera slowly circling to her side, slightly shaky. Nobody looks at the camera.
[Shot 2] At 00:04.000, cut to a close-up of the laptop screen showing a progress bar filling up, <Subject 2>'s red fingernails tapping impatiently on the desk beside it.
overall_soundscape: silent office at night, soft keyboard clicks, faint computer hum. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 4b — Flashback, Maya watching (C: no BG ref)
```
subject_definitions:
<Subject 1> is the woman shown in <Picture 1> (face close-up) and <Picture 2> (full body), preserving her identity, face, curly shoulder-length black hair and mustard yellow denim jacket.
summary:
[reference generation] A flashback where a woman silently watches from a dark doorway.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - face, hair and jacket.
detailed_description:
The target video is a vertical flashback shot inside a dark modern open-plan office at night, city lights far behind, with a desaturated cool blue color grade, slight soft focus to feel like a memory, and shallow depth of field with the background blurred. Exactly one person exists in this scene. From the very first frame, she is already in position; no empty establishing shot, nobody walks into frame.
[Shot 1] Medium shot, chest up, face large and clear. <Subject 1> stands half in the shadow of a dark doorway, completely still, silently watching something across the room. Her yellow jacket is dimly visible, her face lit faintly by a distant screen glow, her expression calm and knowing. Very slow push-in. Nobody looks at the camera.
overall_soundscape: silent office at night, faint computer hum. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 5a — Wrong number, Daniel stops her (A: style ref)
```
subject_definitions:
<Subject 1> is the conference room from <Picture 1>, used only as a style reference for the room's materials, colors, presentation screen and daylight; the room may be seen from any angle, with new parts of the room invented to match.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, sleek platinum blonde hair, red lipstick, black leather jacket, black leather pants and red stiletto heels.
<Subject 3> is the man shown in <Picture 4> (face close-up) and <Picture 5> (full body), preserving his identity, face, short silver hair, silver beard, navy blue three-piece suit and burgundy tie.
summary:
[reference generation] A confident presenter points at a revenue chart until her boss suspiciously stops her.
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): partially_preserved - style, materials and lighting only, camera angle free.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
<Subject 3> (appears in [Shot 2]): fully_preserved - face, hair, beard and suit.
detailed_description:
The target video is a vertical cinematic sequence in <Subject 1> in daytime. Each person appears only once, framed from the waist up with their face large and clear. The presentation screen shows only colorful abstract bar charts, no readable text, no words, no letters, no numbers. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Medium shot, waist up, three-quarter angle, of <Subject 2> standing at the presentation screen, confidently pointing at a large abstract bar chart, smiling. Slow camera dolly sideways. Only she is visible. Nobody looks at the camera.
[Shot 2] At 00:04.000, cut to a medium close-up of <Subject 3> seated at the head of the table, seen from a low side angle. He raises one hand to stop her and frowns hard at the screen, suspicious. Only he is visible.
overall_soundscape: quiet meeting room tone, a pen set down on glass. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 5b — Maya and Leo stand, Vanessa freezes (B: reverse angle)
```
subject_definitions:
<Subject 1> is the conference room from <Picture 1>, preserving the glass table, chairs, windows and daylight from this reverse angle.
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
The target video is a vertical cinematic sequence in <Subject 1> in daytime. Each person appears only once, with faces large and clear in the frame. The laptop screen shows only an abstract list of colored file icons, no readable text, no words, no letters. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Medium two-shot, waist up, facing the camera with the windows behind them: <Subject 2> calmly stands up from her chair, and <Subject 3> stands up close beside her, holding up an open laptop with its screen facing forward. Only these two people are visible. Nobody looks at the camera.
[Shot 2] At 00:04.000, cut to a close-up of <Subject 4>'s face. Her smile collapses, her eyes widen in shock and her lips part. She is completely frozen. Slow push-in. Only she is visible.
overall_soundscape: tense quiet room, a chair scraping back, a sharp intake of breath. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 6a — Vanessa walks out (original: exact BG)
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
The target video is a vertical cinematic sequence in <Subject 1>. Exactly one person exists in this scene, always seen from behind. From the very first frame, <Subject 2> is already walking mid-corridor, seen from behind; no empty establishing shot, she does not enter the frame.
[Shot 1] <Subject 2> walks quickly away from the camera down the long corridor toward the elevator, her back to us, platinum hair swinging. Static camera, symmetrical framing.
[Shot 2] At 00:04.500, cut to a low close-up at floor level of her glossy red stiletto heels striking the polished floor with each step, walking away.
overall_soundscape: sharp echoing high-heel clicks on a hard floor. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```

### 6b — Maya satisfied (A: style ref)
```
subject_definitions:
<Subject 1> is the office corridor from <Picture 1>, used only as a style reference for the materials, colors, cool white lighting and elevator; the corridor may be seen from any angle, with new parts invented to match.
<Subject 2> is the woman shown in <Picture 2> (face close-up) and <Picture 3> (full body), preserving her identity, face, curly shoulder-length black hair, mustard yellow denim jacket and white t-shirt.
summary:
[reference generation] A woman stands calmly in a corridor with a satisfied smile as elevator doors close behind her.
retention_analysis:
<Subject 1> (appears in [Shot 1]): partially_preserved - style, materials and lighting only, camera angle free.
<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic shot in <Subject 1>. Exactly one person is visible. From the very first frame, every person in this shot is already in position; no empty establishing shot of the background, nobody walks into frame.
[Shot 1] Medium shot, chest up, three-quarter angle, face large and clear. <Subject 2> stands in the corridor, arms crossed, a calm satisfied smile. Far behind her, out of focus, elevator doors slide closed. The camera slowly arcs around her toward the front. Nobody looks at the camera.
overall_soundscape: soft elevator chime, doors sliding shut, quiet corridor tone. No one speaks, no dialogue, no voices.
non_diegetic_music: none.
```
