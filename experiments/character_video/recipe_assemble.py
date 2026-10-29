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
import os, re, subprocess, json, glob, hashlib
import numpy as np, soundfile as sf

CLIPS = os.environ.get("CLIPS", "clips")
STILLS = os.environ.get("STILLS", "cast").split(":")
KOKORO = os.environ.get("KOKORO", "/workspace/kokoro")
FISH = os.environ.get("FISH", "")   # folder with line_NN.wav (Fish voices) and lip_NN.mp4 (lip-synced clips)
WORK = os.environ.get("WORK", "work")
OUT = os.environ.get("OUT", "recipe_clause_part1.mp4")
W, H, FPS = 1080, 1920, 30
GAP = 0.55            # pause after each line
CLIP_VOL = 0.30       # MiniMax ambience under the voices
# what to cut to when a line outlasts its lip-synced clip (Vanessa's stills wear the wrong outfit,
# so hers is a freeze frame from one of her clips)
SPEAKER_STILL = {"ARIA": ("s", "aria_unbothered"), "VANESSA": ("f", "clip07", 4.3), "DANIEL": ("s", "daniel_close"),
                 "LEO": ("s", "leo_chef_close"), "MAYA": ("s", "maya_v2_close")}
INTRO = 1.8           # seconds for a character's first-appearance card
COLOURS = {"NARR": "white", "ARIA": "0xF2C46D", "VANESSA": "0xFF6B6B", "DANIEL": "0x7FB0E0",
           "LEO": "0x7CD67C", "MAYA": "0xFFA94D"}
THOUGHTS = {"Daughter. Not daughters.": "ARIA"}   # narration lines that are a character thinking
VOICES = {            # speaker -> (Kokoro voice, speed)
    "NARR": ("af_heart", 0.9), "ARIA": ("af_heart", 0.9), "VANESSA": ("af_bella", 0.95),
    "DANIEL": ("bm_george", 0.85), "LEO": ("am_adam", 0.95), "MAYA": ("af_sarah", 0.95),
}

# Vanessa's cast stills wear the leather jacket; in this episode she wears the blazer
# dress, so her "stills" are freeze frames from her clips.
SEGMENTS = [
 # Cold open
 ("NARR", "Eight years. Forty-one recipes. Three restaurants built on my food.", [("i", "aria_close", "ARIA", "Kitchen Operations Manager. Our narrator."), ("c", "clip01", 0.3, 4.4)]),
 ("NARR", "And it took my stepsister exactly four minutes to decide I was overpaid.", [("i", "vanessa_office_close", "VANESSA", "The stepsister. New CEO."), ("c", "clip02", 0.4, 4.4)]),
 ("", "", [("t", "THE RECIPE CLAUSE\nPart 1: Not Your Job", 2.8)]),
 # The handover
 ("DANIEL", "Thirty years ago, I opened one little kitchen with a borrowed oven. Today, Harlow and Daughter has three locations and a waiting list. And from Monday... my daughter Vanessa runs it.",
  [("i", "daniel_close", "DANIEL", "Founder. Aria's stepdad."), ("c", "clip03", 0.0, 4.4), ("s", "daniel_smile")]),
 ("NARR", "Daughter. Not daughters.", [("f", "clip05", 0.5)]),   # Aria's thought, on Aria's face
 ("NARR", "I've been in this family since I was eleven. I've been in this kitchen since I was twenty-one. I'm still the stepdaughter who cooks.",
  [("c", "clip05", 0.2, 4.4), ("s", "aria_unbothered")]),
 ("VANESSA", "Thank you, Dad. I promise you, Harlow and Daughter is about to get a lot more... efficient.", [("f", "clip04", 4.3)]),
 ("", "", [("i", "leo_chef_close", "LEO", "Sous-chef. Aria's ally."), ("c", "clip06", 1.0, 3.6)]),
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
  [("i", "maya_v2_close", "MAYA", "Front of house. Aria's friend."), ("c", "clip16", 0.3, 4.4)]),
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
SENT_PAUSE = 0.18     # pause between sentences inside one line
def speak(speaker, text, path):
    """Voice one line sentence by sentence; return [(start, end, sentence)] for exact captions."""
    global _tts
    if _tts is None:
        from kokoro_onnx import Kokoro
        _tts = Kokoro(f"{KOKORO}/kokoro-v1.0.onnx", f"{KOKORO}/voices-v1.0.bin")
    voice, speed = VOICES[speaker]
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    parts, timing, t, sr = [], [], 0.0, 24000
    for k, sent in enumerate(sents):
        audio, sr = _tts.create(sent, voice=voice, speed=speed, lang="en-us")
        timing.append((t, t + len(audio) / sr, sent))
        t += len(audio) / sr
        parts.append(audio)
        if k < len(sents) - 1:
            parts.append(np.zeros(int(sr * SENT_PAUSE), dtype=audio.dtype)); t += SENT_PAUSE
    parts.append(np.zeros(int(sr * GAP), dtype=parts[0].dtype))
    sf.write(path, np.concatenate(parts), sr)
    json.dump(timing, open(path + ".json", "w"))
    return timing


def fish_voice(text, src, path, lead=0.0, gap=GAP):
    """Use a Fish line: pad it (lead silence before a lip clip, GAP after) and estimate sentence timing."""
    audio, sr = sf.read(src, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    speech = len(audio) / sr
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    total_chars = sum(len(x) for x in sents)
    timing, t = [], lead
    words = json.load(open(src + ".words.json")) if os.path.exists(src + ".words.json") else []
    if words:   # real word times (faster-whisper); map each sentence onto them by word position
        n_script, n_heard, k = sum(len(s.split()) for s in sents), len(words), 0
        for sent in sents:
            a = min(int(k * n_heard / n_script), n_heard - 1)
            k += len(sent.split())
            b = min(max(int(k * n_heard / n_script) - 1, a), n_heard - 1)
            timing.append((lead + words[a][0], lead + words[b][1], sent))
    else:
        for sent in sents:
            d = speech * len(sent) / total_chars
            timing.append((t, t + d, sent)); t += d
    fade = min(len(audio), int(sr * 0.06))           # no click where the line is cut
    audio = audio.astype("float32"); audio[len(audio) - fade:] *= np.linspace(1, 0, fade, dtype="float32")
    out = np.concatenate([np.zeros(int(sr * lead), dtype="float32"), audio, np.zeros(int(sr * gap), dtype="float32")])
    sf.write(path, out, sr)
    json.dump(timing, open(path + ".json", "w"))


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
    elif kind == "L":   # lip-synced clip: picture only, the clean voice is laid over it
        src = v[1]
        hold = max(0.0, seconds - dur(src))
        vf = f"{SCALE},tpad=stop_mode=clone:stop_duration={hold:.3f}"
        run(["ffmpeg", "-y", "-i", src, *SILENT, "-vf", vf, "-map", "0:v", "-map", "1:a",
             "-t", f"{seconds:.3f}", *ENC, out])
    elif kind == "s":
        kenburns(find_still(v[1]), seconds, out, zoom_in=idx % 2 == 0)
    elif kind == "f":
        _, clip, t = v
        frame = f"{WORK}/frame_{clip}_{t}.png"
        run(["ffmpeg", "-y", "-ss", str(t), "-i", f"{CLIPS}/{clip}.mp4", "-frames:v", "1", frame])
        kenburns(frame, seconds, out, zoom_in=idx % 2 == 1)
    elif kind == "i":
        _, still, name, role = v
        tmp = out + ".kb.mp4"
        kenburns(find_still(still), seconds, tmp, zoom_in=True)
        nf, rf = out + ".name.txt", out + ".role.txt"
        open(nf, "w").write(name); open(rf, "w").write(role)
        col = COLOURS.get(name, "white")
        vf = (f"drawbox=x=0:y=ih*0.70:w=iw:h=ih*0.14:color=black@0.55:t=fill,"
              f"drawtext=textfile={nf}:fontcolor={col}:fontsize=96:x=(w-text_w)/2:y=h*0.715,"
              f"drawtext=textfile={rf}:fontcolor=white:fontsize=46:x=(w-text_w)/2:y=h*0.785")
        run(["ffmpeg", "-y", "-i", tmp, "-vf", vf, *ENC, out])
        os.remove(tmp)
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
        # a character's first appearance is a name tag over the scene, not a card that stops it
        tags = [v for v in visuals if v[0] == "i"]
        visuals = [v for v in visuals if v[0] != "i"]
        lip = f"{FISH}/lip_{i:02}.mp4" if FISH else ""
        if lip and speaker != "NARR" and os.path.exists(lip):
            visuals = [("L", lip)]
            fish = f"{FISH}/line_{i:02}.wav"
            if os.path.exists(fish) and sf.info(fish).duration > dur(lip) + 0.8:
                visuals.append(SPEAKER_STILL[speaker])   # cut away instead of freezing the face
        if text:
            voice = f"{WORK}/v{i:02}.wav"
            fish = f"{FISH}/line_{i:02}.wav" if FISH else ""
            if fish and os.path.exists(fish):
                # on a lip-synced shot, end the pause where the clip ends so the face never freezes
                gap = max(0.1, dur(lip) - sf.info(fish).duration) if any(v[0] == "L" for v in visuals) else GAP
                fish_voice(text, fish, voice, gap=gap)
            elif not os.path.exists(voice + ".json"):      # resumable: reuse finished work
                speak(speaker, text, voice)
            need = sf.info(voice).duration
        else:
            need = 0.0
        fixed = sum(min(v[3], 4.45) - v[2] for v in visuals if v[0] == "c") + sum(v[2] for v in visuals if v[0] == "t") + sum(dur(v[1]) for v in visuals if v[0] == "L") + INTRO * sum(v[0] == "i" for v in visuals)
        flex = [v for v in visuals if v[0] in "sf"]
        total = max(need, fixed + (1.6 * len(flex) if flex else 0))
        each = (total - fixed) / len(flex) if flex else 0
        parts = []
        for j, v in enumerate(visuals):
            if v[0] == "c":
                s = min(v[3], 4.45) - v[2]
                if not flex and j == len(visuals) - 1:
                    s += total - fixed      # hold the last frame if the line runs long
            elif v[0] == "L":
                s = dur(v[1]) + (total - fixed if not flex and j == len(visuals) - 1 else 0)
            else:
                s = v[2] if v[0] == "t" else INTRO if v[0] == "i" else each
            key = hashlib.md5(repr((v, round(s, 2), i + j)).encode()).hexdigest()[:10]
            p = f"{WORK}/p_{key}.mp4"
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
            timing = json.load(open(voice + ".json"))
            first = True
            for a0, b0, sent in timing:
                words = sent.split()
                chunks = [" ".join(words[k:k + 6]) for k in range(0, len(words), 6)]
                for k, ch in enumerate(chunks):
                    a = t0 + a0 + (b0 - a0) * k / len(chunks); b = t0 + a0 + (b0 - a0) * (k + 1) / len(chunks)
                    style = speaker
                    if first and text in THOUGHTS:
                        style = THOUGHTS[text]
                        ch = f"{{\\b1\\i1}}{style} (thinking):{{\\b0}} " + ch
                    elif first and speaker != "NARR":
                        ch = f"{{\\b1}}{speaker}:{{\\b0}} " + ch
                    first = False
                    subs.append((a, b, ch, style))
        else:
            seg = body
        for _, _, name, role in tags:
            subs.append((t0 + 0.3, t0 + 3.8, f"{{\\an8\\pos(540,180)\\fs84\\b1}}{name}\\N{{\\fs46\\b0\\c&HFFFFFF&}}{role}", name))
        seg_files.append(seg)
        t0 += dur(seg)
        print(f"{i:02} {speaker or '-':8} {dur(seg):5.1f}s  total {t0:6.1f}s", flush=True)
    # Join picture and sound separately: each segment's AAC track runs a few ms short of its video,
    # and stream-copying the segments together lets that add up to a second of drift by the end.
    # So every segment's sound is cut or padded to exactly its video length as PCM first.
    # The concat demuxer steps by each file's container length, so the picture is joined from
    # video-only copies; otherwise a longer audio track would push the next segment later.
    lst, alst = f"{WORK}/all.txt", f"{WORK}/all_a.txt"
    vids, wavs = [], []
    for k, s in enumerate(seg_files):
        v = f"{WORK}/sv{k:02}.mp4"
        run(["ffmpeg", "-y", "-i", s, "-an", "-c:v", "copy", v])
        vlen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", v], capture_output=True, text=True).stdout)
        w = f"{WORK}/sa{k:02}.wav"
        run(["ffmpeg", "-y", "-i", s, "-vn", "-af", f"aresample=48000,apad,atrim=end_sample={round(vlen * 48000)}",
             "-ac", "2", "-c:a", "pcm_s16le", w])
        vids.append(v); wavs.append(w)
    open(lst, "w").write("".join(f"file '{os.path.abspath(v)}'\n" for v in vids))
    open(alst, "w").write("".join(f"file '{os.path.abspath(w)}'\n" for w in wavs))
    vjoin, ajoin, joined = f"{WORK}/joined_v.mp4", f"{WORK}/joined_a.wav", f"{WORK}/joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-an", "-c", "copy", vjoin])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alst, "-c", "copy", ajoin])
    run(["ffmpeg", "-y", "-i", vjoin, "-i", ajoin, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-ar", "48000", joined])
    ass = f"{WORK}/subs.ass"
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginV\n")
    for name, col in COLOURS.items():
        rgb = "FFFFFF" if col == "white" else col[2:]
        bgr = rgb[4:6] + rgb[2:4] + rgb[0:2]
        head += f"Style: {name},DejaVu Sans,64,&H00{bgr},&H00000000,&H64000000,1,5,0,2,330\n"
    head += "\n[Events]\nFormat: Layer, Start, End, Style, Text\n"
    t = lambda x: f"{int(x//3600)}:{int(x%3600//60):02}:{x%60:05.2f}"
    open(ass, "w").write(head + "".join(f"Dialogue: 0,{t(a)},{t(b)},{sp},{c}\n" for a, b, c, sp in subs))
    run(["ffmpeg", "-y", "-i", joined, "-vf", f"subtitles={ass}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", OUT])
    print("wrote", OUT, f"{dur(OUT):.1f}s")


if __name__ == "__main__":
    main()
