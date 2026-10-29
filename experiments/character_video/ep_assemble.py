"""Assemble Parts 2-4 of The Recipe Clause from Fish lines, lip-synced clips and scene beats.

Builds a SEGMENTS list for one part and hands it to recipe_assemble's renderer.
Usage: PART=2 FISH=... CLIPS=... STILLS=... WORK=... OUT=... python3 ep_assemble.py
Expects in FISH: p{N}_{nn}.wav (lines), lip_p{N}_{nn}.mp4 (lip clips), p{N}_<beat>.mp4 (scene beats).
"""
import os, glob
import recipe_assemble as ra
from recipe_clause_parts2_4 import PARTS

PART = int(os.environ.get("PART", "2"))
TITLES = {2: "Part 2: The Critic's Table", 3: "Part 3: The Clause", 4: "Part 4: The Review"}
NARR_STILLS = ["set_kitchen", "set_office", "set_terrace", "set_dining", "set_apartment"]
NEW_FACES = {"LAURENT": ("f", "clip23", 1.0), "ELISE": ("s", "set_dining")}   # no cast images for these two
ra.VOICES.setdefault("LAURENT", ("am_michael", 0.95)); ra.VOICES.setdefault("ELISE", ("bf_emma", 0.9))
ra.COLOURS.update({"LAURENT": "0xC9A0FF", "ELISE": "0x9FE2E0"})


def build(fish_dir, part):
    lines = PARTS[part]
    beats = sorted(glob.glob(f"{fish_dir}/p{part}_[a-z]*.mp4"))
    segs, staged, b = [("", "", [("t", f"THE RECIPE CLAUSE\n{TITLES[part]}", 2.8)])], {}, 0
    for n, (sp, d, tx) in enumerate(lines):
        i = len(segs)
        staged[f"line_{i:02}.wav"] = f"{fish_dir}/p{part}_{n:02}.wav"
        lip = f"{fish_dir}/lip_p{part}_{n:02}.mp4"
        if os.path.exists(lip):
            staged[f"lip_{i:02}.mp4"] = lip
            visuals = [("s", "set_kitchen")]            # replaced by the lip clip in the renderer
        elif sp == "NARR":
            if b < len(beats):                          # narration carries the scene clips
                visuals = [("L", beats[b])]; b += 1
            else:
                visuals = [("s", NARR_STILLS[n % len(NARR_STILLS)])]
        else:
            visuals = [NEW_FACES.get(sp) or ra.SPEAKER_STILL[sp]]
        segs.append((sp, tx, visuals))
    end = {2: "PART 3\nThe Clause", 3: "PART 4\nThe Review", 4: "THE END\nSubscribe for the next story"}[part]
    segs.append(("", "", [("t", end, 3.0)]))
    return segs, staged


if __name__ == "__main__":
    fish = os.environ["FISH"]
    stage = os.path.join(ra.WORK, "fish_stage")
    os.makedirs(stage, exist_ok=True)
    segs, staged = build(fish, PART)
    for f in os.listdir(stage):
        os.remove(os.path.join(stage, f))
    for name, src in staged.items():
        if os.path.exists(src):
            os.symlink(src, os.path.join(stage, name))
    ra.SEGMENTS = segs
    ra.FISH = stage
    ra.main()
