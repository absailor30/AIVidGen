"""Assemble "The Recipe Clause — Part 1": Kokoro voices + MiniMax clips + Ken Burns stills.

Runs on CPU (no pod). Inputs, set by env vars:
    CLIPS   folder with clip01.mp4 … clip29.mp4 (MiniMax outputs, renamed)
    STILLS  folders searched for still images, ":"-separated (cast folders, sets)
    KOKORO  folder with kokoro-v1.0.onnx + voices-v1.0.bin
    WORK    scratch folder;  OUT  output .mp4
Each segment = one line (speaker + text, or "" for a silent beat) + the visuals under it:
    ("c", "clip09", start, end)   a clip trimmed to [start, end] (its own audio kept, quiet)
    ("s", "aria_cold")            a still with a slow push-in
    ("f", "clip17", t)            a freeze frame from a clip at time t, with a slow push-in
    ("t", "TITLE\\nSUBTITLE", sec) a title card
Clips keep their length; stills share whatever time the line still needs. If a line is
longer than its clips and there are no stills, the last clip holds its final frame.
"""
import os, subprocess, json, glob
import numpy as np, soundfile as sf

CLIPS = os.environ.get("CLIPS", "clips")
STILLS = os.environ.get("STILLS", "cast").split(":")
KOKORO = os.environ.get("KOKORO", "/workspace/kokoro")
WORK = os.environ.get("WORK", "work")
OUT = os.environ.get("OUT", "recipe_clause_part1.mp4")
W, H, FPS = 1080, 1920, 30
GAP = 0.35            # pause after each line
CLIP_VOL = 0.30       # MiniMax ambience under the voices
VOICES = {            # speaker -> (Kokoro voice, speed)
    "NARR": ("af_heart", 1.0), "ARIA": ("af_heart", 1.0), "VANESSA": ("af_bella", 1.05),
    "DANIEL": ("bm_george", 0.95), "LEO": ("am_adam", 1.05), "MAYA": ("af_sarah", 1.05),
}

# Vanessa's cast stills wear the leather jacket; in this episode she wears the blazer
# dress, so her "stills" are freeze frames from her clips.
SEGMENTS = [
 # Cold open
 ("NARR", "Eight years. Forty-one recipes. Three restaurants built on my food.", [("c", "clip01", 0.3, 4.4)]),
 ("NARR", "And it took my stepsister exactly four minutes to decide I was overpaid.", [("c", "clip02", 0.4, 4.4)]),
 ("", "", [("t", "THE RECIPE CLAUSE\nPart 1: Not Your Job", 2.8)]),
 # The handover
 ("DANIEL", "Thirty years ago, I opened one little kitchen with a borrowed oven. Today, Harlow and Daughter has three locations and a waiting list. And from Monday... my daughter Vanessa runs it.",
  [("s", "set_dining"), ("c", "clip03", 0.0, 4.4), ("s", "daniel_smile")]),
 ("NARR", "Daughter. Singular.", [("c", "clip04", 1.6, 4.4)]),
 ("NARR", "I've been in this family since I was eleven. I've been in this kitchen since I was twenty-one. I'm still the stepdaughter who cooks.",
  [("c", "clip05", 0.2, 4.4), ("s", "aria_unbothered")]),
 ("VANESSA", "Thank you, Dad. I promise you, Harlow and Daughter is about to get a lot more... efficient.", [("f", "clip04", 4.3)]),
 ("", "", [("c", "clip06", 1.0, 3.6)]),
 # The cut
 ("VANESSA", "I went through the payroll last night. Interesting reading. Recipe development bonus. Two thousand a month. Since when?",
  [("c", "clip07", 0.0, 4.4), ("f", "clip07", 4.3)]),
 ("ARIA", "Since your dad tasted my short rib and tore up the old menu. Eight years ago.", [("s", "aria_cold")]),
 ("VANESSA", "Cute. But your contract says Kitchen Operations Manager. Rotas, ordering, health inspections. Nothing about inventing. So your recipe bonus is cancelled. You were hired to manage shifts, not play chef.",
  [("f", "clip07", 2.5), ("s", "aria_close"), ("f", "clip09", 0.4)]),
 ("ARIA", "Bold move, cutting the only person here who can cook. Fine. I'll manage shifts. You manage the menu. Good luck reading it.",
  [("c", "clip08", 0.2, 4.4), ("s", "aria_smug")]),
 ("", "", [("c", "clip09", 0.6, 3.6)]),
 ("VANESSA", "Relax. Anyone can follow a recipe.", [("f", "clip09", 3.8)]),
 ("ARIA", "Anyone can follow one. Somebody had to write it. You weren't hired for that either, remember?", [("s", "aria_unbothered")]),
 ("", "", [("c", "clip10", 1.4, 4.4)]),
 ("VANESSA", "Close the door on your way out.", [("f", "clip10", 0.6)]),
 ("ARIA", "It's a kitchen, Vanessa. The door stays open. Heat has to go somewhere.", [("c", "clip11", 2.2, 4.4), ("s", "aria_cold")]),
 ("", "", [("c", "clip12", 2.3, 4.4)]),
 # The rule
 ("LEO", "You're actually doing this.", [("c", "clip13", 0.4, 4.0)]),
 ("ARIA", "I'm doing my job. Exactly my job.", [("s", "aria_close")]),
 ("LEO", "And the fermented base? The one in every sauce? You make that every Sunday.", [("s", "leo_chef_close")]),
 ("ARIA", "At home. On my own time. With my own recipe. Sundays aren't on the rota, Leo.", [("s", "aria_smug")]),
 ("", "", [("c", "clip14", 1.4, 4.4)]),
 ("NARR", "Here's what nobody in that office understood. My dishes weren't recipes. They were a system. And the heart of that system lived in a jar on my kitchen counter. Not theirs.",
  [("s", "set_kitchen"), ("s", "set_apartment")]),
 # Day three
 ("NARR", "Day three.", [("c", "clip15", 0.5, 4.4)]),
 ("MAYA", "Table six says the short rib tastes like a different restaurant. Table nine just asked if we changed owners. I didn't know what to tell them.",
  [("c", "clip16", 0.3, 4.4), ("s", "maya_v2_close")]),
 ("VANESSA", "Aria. Fix this. Now.", [("c", "clip17", 0.3, 3.5)]),
 ("ARIA", "Not in my job description. You laminated it. It's on the fridge.", [("s", "aria_unbothered")]),
 ("", "", [("c", "clip18", 0.8, 4.4)]),
 ("VANESSA", "You're being petty.", [("f", "clip17", 3.0)]),
 ("ARIA", "No. Petty is cutting my pay to lease yourself a new car. I'm being accurate.", [("s", "aria_cold")]),
 ("", "", [("c", "clip19", 0.0, 2.3)]),
 ("VANESSA", "That's company business.", [("f", "clip18", 3.0)]),
 ("ARIA", "So is the food. Funny how you only read half the file.", [("s", "aria_smug")]),
 # Daniel
 ("DANIEL", "Reviews dropped half a star in three days. Vanessa says you're sabotaging her.", [("s", "set_terrace"), ("c", "clip20", 0.0, 4.4)]),
 ("ARIA", "I'm doing exactly what she asked. To the letter.", [("s", "aria_close")]),
 ("DANIEL", "Aria... come on. It's family.", [("s", "daniel_sad")]),
 ("ARIA", "Then family can pay me like staff. Or lose me like staff.", [("s", "aria_cold")]),
 ("", "", [("c", "clip21", 1.0, 4.4)]),
 ("DANIEL", "I signed something, years ago. About the recipes.", [("s", "daniel_close")]),
 ("ARIA", "What did you sign?", [("s", "aria_shock")]),
 ("DANIEL", "Ask me when this is over.", [("c", "clip22", 0.0, 4.4)]),
 ("NARR", "He walked away before I could ask again. Daniel has never once walked away from a conversation. That's when I knew the paper mattered.",
  [("s", "set_terrace")]),
 # The replacement
 ("VANESSA", "Everyone, meet Chef Laurent. Two TV shows. A cookbook. A real chef. He'll be modernising our menu.",
  [("c", "clip23", 0.0, 2.3), ("f", "clip04", 4.3)]),
 ("VANESSA", "You're replaceable, Aria. Everyone is.", [("f", "clip07", 4.3)]),
 ("ARIA", "Everyone's replaceable. Ask him who wrote the recipes he's about to ruin.", [("c", "clip27", 0.0, 4.4)]),
 ("", "", [("c", "clip24", 0.6, 4.0)]),
 ("MAYA", "Vanessa... the booking system. Party of one. Saturday the eighteenth. The name is... Elise Marchetti.", [("c", "clip25", 0.0, 4.4)]),
 ("", "", [("c", "clip26", 0.8, 4.4)]),
 ("LEO", "The critic? The one who closed Bianco's with one review?", [("s", "leo_chef_close")]),
 ("ARIA", "She ordered my short rib last time. Three years ago. Called it the reason to visit the city.", [("s", "aria_unbothered")]),
 # Cliffhanger
 ("NARR", "Fourteen days until the most important table in our history. A TV chef with no recipe. A CEO with no idea. And a jar on my counter that nobody at Harlow and Daughter even knew existed.",
  [("c", "clip28", 0.0, 4.4), ("s", "set_apartment")]),
 ("NARR", "She wanted efficient. She's about to get it.", [("c", "clip29", 0.0, 4.4)]),
 ("", "", [("t", "PART 2\nThe Critic's Table", 3.0)]),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(cmd) + "\n" + r.stderr[-1500:])


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def find_still(name):
    for d in STILLS:
        hits = glob.glob(f"{d}/**/{name}.jpg", recursive=True)
        if hits:
            return hits[0]
    raise FileNotFoundError(name)


_tts = None
def speak(speaker, text, path):
    global _tts
    if _tts is None:
        from kokoro_onnx import Kokoro
        _tts = Kokoro(f"{KOKORO}/kokoro-v1.0.onnx", f"{KOKORO}/voices-v1.0.bin")
    voice, speed = VOICES[speaker]
    audio, sr = _tts.create(text, voice=voice, speed=speed, lang="en-us")
    pad = np.zeros(int(sr * GAP), dtype=audio.dtype)
    sf.write(path, np.concatenate([audio, pad]), sr)


SCALE = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
SILENT = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-ar", "48000", "-ac", "2"]


def kenburns(img, seconds, out, zoom_in=True):
    n = max(1, int(round(seconds * FPS)))
    z = f"min(1+0.10*on/{n},1.10)" if zoom_in else f"max(1.10-0.10*on/{n},1.0)"
    vf = (f"scale={int(W*1.25)}:{int(H*1.25)}:force_original_aspect_ratio=increase,crop={int(W*1.25)}:{int(H*1.25)},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1")
    run(["ffmpeg", "-y", "-loop", "1", "-i", img, *SILENT, "-vf", vf, "-t", f"{seconds:.3f}",
         "-map", "0:v", "-map", "1:a", *ENC, out])


def piece(v, seconds, out, idx):
    kind = v[0]
    if kind == "c":
        _, clip, a, b = v
        src = f"{CLIPS}/{clip}.mp4"
        b = min(b, dur(src) - 0.05)
        hold = max(0.0, seconds - (b - a))
        vf = f"trim={a}:{b},setpts=PTS-STARTPTS,{SCALE},tpad=stop_mode=clone:stop_duration={hold:.3f}"
        af = f"atrim={a}:{b},asetpts=PTS-STARTPTS,volume={CLIP_VOL},aresample=48000,apad"
        run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-af", af, "-t", f"{seconds:.3f}", *ENC, out])
    elif kind == "s":
        kenburns(find_still(v[1]), seconds, out, zoom_in=idx % 2 == 0)
    elif kind == "f":
        _, clip, t = v
        frame = f"{WORK}/frame_{clip}_{t}.png"
        run(["ffmpeg", "-y", "-ss", str(t), "-i", f"{CLIPS}/{clip}.mp4", "-frames:v", "1", frame])
        kenburns(frame, seconds, out, zoom_in=idx % 2 == 1)
    elif kind == "t":
        title, sub = v[1].split("\n")
        tf, sf_ = f"{WORK}/title_{idx}_a.txt", f"{WORK}/title_{idx}_b.txt"
        open(tf, "w").write(title); open(sf_, "w").write(sub)
        vf = (f"color=c=black:s={W}x{H}:r={FPS}:d={seconds},"
              f"drawtext=textfile={tf}:fontcolor=white:fontsize=78:x=(w-text_w)/2:y=h/2-90,"
              f"drawtext=textfile={sf_}:fontcolor=0xE8C27A:fontsize=52:x=(w-text_w)/2:y=h/2+20,"
              f"fade=t=in:st=0:d=0.4,fade=t=out:st={seconds-0.4}:d=0.4")
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", vf, *SILENT,
             "-t", f"{seconds:.3f}", "-map", "0:v", "-map", "1:a", *ENC, out])


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    os.makedirs(WORK, exist_ok=True)
    seg_files, subs, t0 = [], [], 0.0
    for i, (speaker, text, visuals) in enumerate(SEGMENTS):
        voice = None
        if text:
            voice = f"{WORK}/v{i:02}.wav"
            if not os.path.exists(voice):      # resumable: reuse finished work
                speak(speaker, text, voice)
            need = sf.info(voice).duration
        else:
            need = 0.0
        fixed = sum(min(v[3], 4.45) - v[2] for v in visuals if v[0] == "c") + sum(v[2] for v in visuals if v[0] == "t")
        flex = [v for v in visuals if v[0] in "sf"]
        total = max(need, fixed + (1.6 * len(flex) if flex else 0))
        each = (total - fixed) / len(flex) if flex else 0
        parts = []
        for j, v in enumerate(visuals):
            if v[0] == "c":
                s = min(v[3], 4.45) - v[2]
                if not flex and j == len(visuals) - 1:
                    s += total - fixed      # hold the last frame if the line runs long
            else:
                s = v[2] if v[0] == "t" else each
            p = f"{WORK}/p{i:02}_{j}.mp4"
            if not os.path.exists(p):
                piece(v, s, p, i + j)
            parts.append(p)
        lst = f"{WORK}/l{i:02}.txt"
        open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
        body = f"{WORK}/b{i:02}.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", body])
        seg = f"{WORK}/s{i:02}.mp4"
        if voice:
            run(["ffmpeg", "-y", "-i", body, "-i", voice, "-filter_complex",
                 "[1:a]aresample=48000,apad[v];[0:a][v]amix=inputs=2:duration=first:normalize=0[a]",
                 "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-ar", "48000", seg])
            words = text.split()
            chunks = [" ".join(words[k:k + 5]) for k in range(0, len(words), 5)]
            speech = need - GAP
            for k, ch in enumerate(chunks):
                a = t0 + speech * k / len(chunks); b = t0 + speech * (k + 1) / len(chunks)
                subs.append((a, b, ch))
        else:
            seg = body
        seg_files.append(seg)
        t0 += dur(seg)
        print(f"{i:02} {speaker or '-':8} {dur(seg):5.1f}s  total {t0:6.1f}s", flush=True)
    lst = f"{WORK}/all.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in seg_files))
    joined = f"{WORK}/joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    srt = f"{WORK}/subs.srt"
    open(srt, "w").write("".join(f"{n+1}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n\n" for n, (a, b, c) in enumerate(subs)))
    style = "FontName=DejaVu Sans,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=0,Alignment=2,MarginV=70"
    run(["ffmpeg", "-y", "-i", joined, "-vf", f"subtitles={srt}:force_style='{style}'",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", OUT])
    print("wrote", OUT, f"{dur(OUT):.1f}s")


if __name__ == "__main__":
    main()
