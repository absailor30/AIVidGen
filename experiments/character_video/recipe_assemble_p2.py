"""The Recipe Clause, Part 2: assemble Grok shots, lip-sync clips and the locked voices into the episode.

Every line is one segment whose length is exact in frames (25 fps) and samples (48 kHz), so picture and
sound are joined separately and never drift. Each scene has its own room-sound bed (the scene's Grok audio,
quiet), voices sit on top, and subtitles are burned in at the end.

Env: GROK (shot_NN.mp4), LIP (lip_NN.mp4), VOICES (line_NN.wav + .words.json), WORK, OUT, FONT (Anton).
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf

GROK = os.environ.get("GROK", "grok2")
LIP = os.environ.get("LIP", "lip2")
VOICES = os.environ.get("VOICES", "ep2v3")
WORK = os.environ.get("WORK", "work_p2")
OUT = os.environ.get("OUT", "recipe_clause_ep2.mp4")
FONT = os.environ.get("FONT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Anton-Regular.ttf"))
W, H, FPS, SR = 1080, 1920, 25, 48000
GAP, LEAD = 0.35, 0.6          # pause after a line; pause before the first line of a new scene
BED_VOL = 0.18                 # scene room sound under the voices
PART, NEXT = 2, 3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recipe_clause_parts2_4 import PARTS
LINES = PARTS[PART]

COLOURS = {"NARR": "FFFFFF", "ARIA": "F2C46D", "VANESSA": "FF6B6B", "DANIEL": "7FB0E0",
           "LEO": "7CD67C", "MAYA": "FFA94D", "LAURENT": "C9A2FF"}
TAGS = {   # first appearance in this episode: line -> (name, role, seconds into the line)
    0: ("ARIA", "Kitchen Operations Manager. Our narrator.", 5.5),
    1: ("LAURENT", "Celebrity chef. Vanessa's hire.", 0.4),
    3: ("LEO", "Sous-chef. Aria's ally.", 0.2),
    6: ("MAYA", "Front of house. Aria's friend.", 0.6),
    7: ("VANESSA", "The stepsister. New CEO.", 0.1),
    19: ("DANIEL", "Founder. Aria's stepdad.", 0.3),
}
# scene = (room-sound source, first line)
SCENES = [("shot_02", 0), ("shot_05", 6), ("shot_06", 8), ("shot_09", 14), ("shot_10", 18), ("shot_11", 19), ("shot_13", 24)]
SCENE_START = {first for _, first in SCENES}
# Visuals per line, in order. ("c", shot, start) plays a Grok shot from `start` for as long as needed;
# ("L", n) is line n's lip-sync clip; ("c", shot, start, secs) gives a fixed length. A pre-roll before a
# lip clip is played first and the voice waits for it.
PLAN = {
    0: [("c", "shot_01", 0.0, None, 0.88)],            # 10 s recap shot slowed a little to cover 11.3 s
    1: [("c", "shot_02", 0.0)],
    2: [("c", "shot_02", 5.0, 2.0), ("L", 2)],
    3: [("L", 3)],
    4: [("L", 4)],
    5: [("c", "shot_04", 6.0)],
    6: [("L", 6)],
    7: [("c", "shot_05", 5.5)],
    8: [("c", "shot_06", 0.0, 3.0), ("L", 8)],
    9: [("L", 9)], 10: [("L", 10)], 11: [("L", 11)], 12: [("L", 12)], 13: [("L", 13)],
    14: [("c", "shot_09", 0.0)],
    15: [("c", "shot_09", 9.0, 2.5), ("L", 15)], 16: [("L", 16)], 17: [("L", 17)],
    18: [("c", "shot_10", 0.5)],
    19: [("c", "shot_11", 0.0, 2.5), ("L", 19)], 20: [("L", 20)],
    21: [("L", 21, 4.0), ("c", "shot_12", 2.0)],      # cut to the contract insert while he reads
    22: [("L", 22)], 23: [("L", 23)],
    24: [("c", "shot_13", 7.0)],
}
FREEZE_AFTER = {11: 0.7, 13: 0.7, 22: 0.8}            # punchline freezes
TITLE_AFTER = {0: ("THE RECIPE CLAUSE", "PART 2: THE CRITIC'S TABLE", 2.6)}
END_SECS = 3.0


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd)}\n{r.stderr[-1500:]}")


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


SCALE = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
VENC = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def frames(sec):
    return max(1, round(sec * FPS))


def vclip(src, start, sec, out, speed=1.0, fade_in=False):
    """`sec` seconds of picture from `src` at `start`; holds the last frame if the source runs out."""
    n = frames(sec)
    avail = (dur(src) - start - 0.05) / speed
    hold = max(0.0, sec - avail) + 0.2
    vf = f"trim=start={start},setpts=(PTS-STARTPTS)/{speed},{SCALE},tpad=stop_mode=clone:stop_duration={hold:.3f}"
    if fade_in:
        vf += ",fade=t=in:st=0:d=0.3"
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-frames:v", str(n), *VENC, out])
    return n


def last_frame(src, png):
    run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.1", "-i", src, "-frames:v", "1", "-update", "1", png])


def zoom_still(png, sec, out, z1=1.06, extra=""):
    n = frames(sec)
    vf = (f"scale={int(W*1.2)}:{int(H*1.2)},zoompan=z='1+({z1}-1)*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={n}:s={W}x{H}:fps={FPS},setsar=1{extra}")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", png, "-vf", vf, "-frames:v", str(n), *VENC, out])
    return n


def esc(t):
    return t.replace("'", "’").replace(":", "\\:")


def text_card(title, sub, sec, out):
    n = frames(sec)
    vf = (f"color=c=black:s={W}x{H}:r={FPS}:d={sec},"
          f"drawtext=fontfile={FONT}:text='{esc(title)}':fontcolor=white:fontsize=120:x=(w-text_w)/2:y=h/2-150:borderw=6:bordercolor=black,"
          f"drawtext=fontfile={FONT}:text='{esc(sub)}':fontcolor=0xFFD21F:fontsize=72:x=(w-text_w)/2:y=h/2+20:borderw=5:bordercolor=black,"
          f"fade=t=in:st=0:d=0.35,fade=t=out:st={sec-0.35}:d=0.35")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", vf, "-frames:v", str(n), *VENC, out])
    return n


def end_card(png, sec, out):
    a = lambda t0: f"alpha='if(lt(t,{t0}),0,min(1,(t-{t0})/0.2))'"
    extra = (",eq=brightness=-0.12:saturation=0.8,vignette=PI/3,"
             f"drawbox=y=ih*0.36:w=iw:h=ih*0.30:color=black@0.55:t=fill:enable='gte(t,0.15)',"
             f"drawtext=fontfile={FONT}:text='TO BE CONTINUED':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=h*0.38:borderw=4:bordercolor=black:{a(0.2)},"
             f"drawtext=fontfile={FONT}:text='FOLLOW FOR':fontcolor=0xFFD21F:fontsize=110:x=(w-text_w)/2:y=h*0.43:borderw=7:bordercolor=black:{a(0.5)},"
             f"drawtext=fontfile={FONT}:text='PART {NEXT}':fontcolor=0xFFD21F:fontsize=230:x=(w-text_w)/2:y=h*0.50:borderw=10:bordercolor=black:shadowx=8:shadowy=8:shadowcolor=black@0.7:{a(0.8)}")
    return zoom_still(png, sec, out, z1=1.08, extra=extra)


def hit(sec):
    """Low thump + short noise swell for freezes, as a float array."""
    t = np.arange(int(sec * SR)) / SR
    thump = 0.9 * np.sin(2 * np.pi * (70 - 30 * t) * t) * np.exp(-7 * t)
    noise = np.random.default_rng(1).normal(0, 1, len(t)) * np.exp(-12 * t) * 0.15
    return (thump + noise).astype("float32") * 0.5


def bed(shot, n_samples):
    """The scene's Grok audio, looped to length, quiet."""
    tmp = f"{WORK}/bed_{shot}.wav"
    if not os.path.exists(tmp):
        run(["ffmpeg", "-y", "-v", "error", "-i", f"{GROK}/{shot}.mp4", "-vn", "-ac", "1", "-ar", str(SR), tmp])
    a, _ = sf.read(tmp, dtype="float32")
    if len(a) == 0:
        return np.zeros(n_samples, "float32")
    reps = int(np.ceil(n_samples / len(a)))
    return np.tile(a, reps)[:n_samples] * BED_VOL


def ass_time(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02}:{x % 60:05.2f}"


def main():
    os.makedirs(WORK, exist_ok=True)
    vids, audio, subs = [], [], []
    t_frames = 0
    scene_of = {}
    cur = None
    for n in range(len(LINES)):
        for shot, first in SCENES:
            if n == first:
                cur = shot
        scene_of[n] = cur

    def add_audio(arr):
        audio.append(arr)

    for n, (sp, _, text) in enumerate(LINES):
        voice, _ = sf.read(f"{VOICES}/line_{n:02}.wav", dtype="float32")
        words = json.load(open(f"{VOICES}/line_{n:02}.wav.words.json"))
        vsec = len(voice) / SR
        plan = PLAN[n]
        lead = LEAD if n in SCENE_START and n else 0.0
        # pre-roll: fixed-length shots before the first lip clip
        pre = 0.0
        for v in plan:
            if v[0] == "L":
                break
            if v[0] == "c" and len(v) > 3 and v[3]:
                pre += v[3]
        lead = max(lead, pre)
        total = lead + vsec + GAP
        lips = [v for v in plan if v[0] == "L"]
        if lips and len(lips[0]) == 2:   # a lip clip carries the line: its own length sets the minimum
            total = max(total, pre + dur(f"{LIP}/lip_{lips[0][1]:02}.mp4"))
        nseg = frames(total)
        total = nseg / FPS
        # picture
        parts, used = [], 0
        for k, v in enumerate(plan):
            p = f"{WORK}/l{n:02}_{k}.mp4"
            left = nseg - used
            last = k == len(plan) - 1
            if v[0] == "c":
                speed = v[4] if len(v) > 4 else 1.0
                sec = v[3] if (len(v) > 3 and v[3] and not last) else left / FPS
                used += vclip(f"{GROK}/{v[1]}.mp4", v[2], sec, p, speed, fade_in=(k == 0 and n in SCENE_START))
            else:
                src = f"{LIP}/lip_{v[1]:02}.mp4"
                sec = v[2] if len(v) > 2 else (left / FPS if last else dur(src))
                used += vclip(src, 0.0, sec, p, fade_in=(k == 0 and n in SCENE_START))
            parts.append(p)
        assert used == nseg, (n, used, nseg)
        vids += parts
        # sound: room bed + voice
        ns = round(total * SR)
        mix = bed(scene_of[n], ns)
        s0 = round(lead * SR)
        mix[s0:s0 + len(voice)] += voice[:ns - s0]
        add_audio(mix)
        # subtitles: the script's words in 6-word chunks, timed from the heard words (mapped by position)
        t0 = t_frames / FPS + lead
        sw, nh = text.split(), len(words)
        for c in range(0, len(sw), 6):
            a = min(round(c * nh / len(sw)), nh - 1)
            b = min(max(round(min(c + 6, len(sw)) * nh / len(sw)) - 1, a), nh - 1)
            line = " ".join(sw[c:c + 6])
            if c == 0 and sp != "NARR":
                line = f"{{\\b1}}{sp}:{{\\b0}} " + line
            subs.append((t0 + words[a][0], t0 + words[b][1] + 0.15, line, sp))
        if n in TAGS:
            name, role, at = TAGS[n]
            a = t_frames / FPS + at
            subs.append((a, a + 3.2, f"{{\\an8\\pos(540,170)\\fs92\\b1}}{name}\\N{{\\fs48\\b0\\c&HFFFFFF&}}{role}", name))
        t_frames += nseg
        # extras after the line
        if n in FREEZE_AFTER or n == len(LINES) - 1:
            png = f"{WORK}/last_{n:02}.png"
            last_frame(parts[-1], png)
            if n == len(LINES) - 1:
                k = end_card(png, END_SECS, f"{WORK}/end.mp4"); vids.append(f"{WORK}/end.mp4")
                h = np.zeros(round(k / FPS * SR), "float32"); h[:len(hit(1.2))] += hit(1.2)
                add_audio(h + bed(scene_of[n], len(h)) * 0.6)
            else:
                k = zoom_still(png, FREEZE_AFTER[n], f"{WORK}/fz_{n:02}.mp4", extra=",eq=saturation=0.6:contrast=1.08")
                vids.append(f"{WORK}/fz_{n:02}.mp4")
                h = np.zeros(round(k / FPS * SR), "float32"); hh = hit(k / FPS); h[:len(hh)] += hh
                add_audio(h + bed(scene_of[n], len(h)) * 0.5)
            t_frames += k
        if n in TITLE_AFTER:
            ti, su, sec = TITLE_AFTER[n]
            k = text_card(ti, su, sec, f"{WORK}/title.mp4"); vids.append(f"{WORK}/title.mp4")
            add_audio(np.zeros(round(k / FPS * SR), "float32")); t_frames += k
        print(f"{n:02} {sp:8} {total:5.2f}s  at {t_frames / FPS:6.1f}s", flush=True)

    # join picture (stream copy) and sound (PCM) separately, then mux
    lst = f"{WORK}/v.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(v)}'\n" for v in vids))
    vjoin = f"{WORK}/joined_v.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vjoin])
    a = np.concatenate(audio)
    a = a / max(1.0, np.abs(a).max() / 0.95)
    sf.write(f"{WORK}/joined_a.wav", np.stack([a, a], 1), SR)
    # subtitles
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginV\n")
    for name, rgb in COLOURS.items():
        bgr = rgb[4:6] + rgb[2:4] + rgb[0:2]
        head += f"Style: {name},DejaVu Sans,64,&H00{bgr},&H00000000,&H64000000,1,5,0,2,330\n"
    head += "\n[Events]\nFormat: Layer, Start, End, Style, Text\n"
    ass = f"{WORK}/subs.ass"
    open(ass, "w").write(head + "".join(f"Dialogue: 0,{ass_time(a0)},{ass_time(b0)},{sp},{c}\n" for a0, b0, c, sp in subs))
    run(["ffmpeg", "-y", "-v", "error", "-i", vjoin, "-i", f"{WORK}/joined_a.wav", "-vf", f"subtitles={ass}",
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", OUT])
    print("wrote", OUT, f"{dur(OUT):.1f}s  (picture {t_frames / FPS:.1f}s, sound {len(a) / SR:.1f}s)")


if __name__ == "__main__":
    main()
