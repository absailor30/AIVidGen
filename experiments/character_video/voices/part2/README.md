# The Recipe Clause, Part 2: locked voices

25 lines (`line_NN.flac`, 48 kHz mono, matching `PARTS[2]` in `recipe_clause_parts2_4.py`), word timings in `line_NN.words.json`, full preview in `part2_preview.mp3`.

Source takes from Fish Drama 3, "Fish B" settings (temperature 0.95, top_k 50, top_p 0.95). Daniel is voice design d2 (Qwen3 VoiceDesign).
Processing: denoise, room reverb on dialogue (0.18 wet), loudness -21 LUFS, long pauses inside lines trimmed, each line paced to 160-180 wpm.
Takes chosen by ear: 10 s62, 13 s62, 17 s62, 18 s62, 20 s64, 22 s63, 24 s62; Daniel 19, 21, 23 = d2. The rest were picked by voice similarity to the speaker's reference.
Manual speed changes: 21 = 1.4x the raw take; 23 = pitched up 1 semitone, 1.5x; 10, 13, 17, 18, 19, 20, 22, 24 = a further 1.2x after pacing.
Gaps when joined: 0.35 s within a scene, 1.0 s before lines 6, 8, 14, 18, 19, 24.
