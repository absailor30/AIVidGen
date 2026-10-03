"""Assemble "The Stolen Pitch": edge-tts narration + ffmpeg edit.

Run on the pod:
    python /workspace/story1/assemble.py

Expects the 12 keeper clips in /workspace/story1/clips named gen1a.mp4 ... gen6b.mp4.
Writes /workspace/story1/out/stolen_pitch.mp4 (1080x1920).

Each segment = one narration chunk + the clip pieces shown under it.
Clip pieces are speed-adjusted together so the visuals end exactly when that
segment's narration ends. Tweak the (start, end) trim points after a first watch.
"""
import asyncio
import json
import os
import subprocess

import edge_tts

BASE = "/workspace/story1"
CLIPS = f"{BASE}/clips"
WORK = "/root/story1_work"   # local disk: faster, no volume permission issues
OUT = f"{BASE}/out"

VOICE = "en-US-JennyNeural"   # same voice as render_from_supabase.py
RATE = "+20%"                 # repo uses ~1.4x for shorts; slower here for a drama
GAP = 0.25                    # silence after each segment (seconds)
FPS = 24
W, H = 704, 1280              # MiniMax output size
OUT_W, OUT_H = 1080, 1920

# Edits we agreed on
FLASHBACK = "eq=saturation=0.45:contrast=1.05:brightness=-0.03,colorbalance=rs=-0.06:bs=0.12,vignette=PI/5"
SPARKLE_BLUR = f"delogo=x={W-64}:y={H-64}:w=56:h=56"   # Flow ✦ watermark, bottom-right
HEEL_SPEED = 1.3                                         # 6a heel close-up felt slow

# (text, [(clip, start, end, extra_filter, own_speed), ...], optional_gap). end=None -> clip end.
SEGMENTS = [
    ("I spent three weeks building that pitch. Every slide, every number, every late night.",
     [("gen1a", 0.0, 4.5, None, 1.0)]),
    ("Vanessa watched me the whole time from across the office, smiling like she already knew how this would end.",
     [("gen1b", 1.5, None, None, 1.0)]),            # trim empty-desk opening
    ("Monday morning, Daniel called the meeting. Vanessa stood up first. My title slide appeared on the screen.",
     [("gen2a", 1.0, None, None, 1.0)]),            # keep ~1s of the wide shot
    ("My charts. My words. She didn't even change the font.",
     [("gen2b", 0.0, None, None, 1.0)]),
    ("Daniel nodded along. \"Impressive work, Vanessa.\"",
     [("gen3a", 0.0, None, None, 1.0)]),
    ("I sat there and said nothing. Leo looked at me like I'd lost my mind.",
     [("gen3b", 0.0, None, None, 1.0)]),
    ("What Vanessa didn't know was that I'd seen her at my desk the Friday before.",
     [("gen4a", 0.5, 3.0, FLASHBACK, 1.0),
      ("gen4b", 1.0, 3.5, FLASHBACK, 1.0)]),        # trim empty-doorway frames
    ("So I changed one number. Slide nine. Our projected revenue, off by exactly one zero. Anyone who built that deck would catch it instantly.",
     [("gen4b", 3.5, None, FLASHBACK, 1.0),
      ("gen1a", 4.5, None, None, 1.0),
      ("gen4a", 4.0, None, FLASHBACK, 1.0)]),
    ("She presented it with total confidence. Ten times the real figure.",
     [("gen5a", 0.0, 4.0, None, 1.0)]),
    ("Daniel stopped her. \"Walk me through this number.\"",
     [("gen5a", 4.0, None, None, 1.0)]),
    ("She froze.",
     [("gen5b", 4.0, None, None, 1.0)], 1.6),       # hold on the shock

    ("I stood up with the real number. And Leo had the version history to prove it.",
     [("gen5b", 0.0, 4.0, None, 1.0)]),
    ("Vanessa's heels clicked all the way to the elevator.",
     [("gen6a", 1.0, 3.5, None, 1.0),
      ("gen6a", 4.5, 6.5, None, HEEL_SPEED)], 0.8),
    ("I got the project. And now I always leave one wrong number, just to see who's reading over my shoulder.",
     [("gen6b", 0.0, None, None, 1.0)]),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
        check=True, capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def chunks(text, n=5):
    words = text.split()
    return [" ".join(words[i:i + n]) for i in range(0, len(words), n)]


def main():
    for d in (WORK, OUT):
        os.makedirs(d, exist_ok=True)

    seg_videos, seg_audios, subs = [], [], []
    t0 = 0.0
    for i, seg in enumerate(SEGMENTS):
        text, pieces = seg[0], seg[1]
        gap = seg[2] if len(seg) > 2 else GAP
        mp3 = f"{WORK}/seg{i:02}.mp3"
        asyncio.run(tts(text, mp3))
        wav = f"{WORK}/seg{i:02}.wav"
        run(["ffmpeg", "-y", "-i", mp3, "-af", f"apad=pad_dur={gap}", "-ar", "48000", "-ac", "2", wav])
        target = duration(wav)

        # Cut each piece (trim + own speed + effects), no audio
        piece_files, total = [], 0.0
        for j, (clip, start, end, extra, speed) in enumerate(pieces):
            src = f"{CLIPS}/{clip}.mp4"
            end = duration(src) if end is None else end
            length = (end - start) / speed
            vf = [f"trim=start={start}:end={end}", "setpts=PTS-STARTPTS",
                  f"setpts=PTS/{speed}", f"fps={FPS}", f"scale={W}:{H}", SPARKLE_BLUR]
            if extra:
                vf.append(extra)
            pf = f"{WORK}/seg{i:02}_{j}.mp4"
            run(["ffmpeg", "-y", "-i", src, "-vf", ",".join(vf), "-an",
                 "-c:v", "libx264", "-crf", "16", "-preset", "fast", pf])
            piece_files.append(pf)
            total += length

        # Stretch/squeeze the segment's visuals to match the narration
        factor = target / total
        if not 0.7 <= factor <= 1.4:
            print(f"[warn] segment {i}: visuals {total:.1f}s vs narration {target:.1f}s "
                  f"(x{factor:.2f}) - adjust trims")
        listfile = f"{WORK}/seg{i:02}_list.txt"
        with open(listfile, "w") as f:
            f.writelines(f"file '{p}'\n" for p in piece_files)
        sv = f"{WORK}/seg{i:02}_video.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
             "-vf", f"setpts={factor}*PTS,fps={FPS}", "-t", f"{target}", "-an",
             "-c:v", "libx264", "-crf", "16", "-preset", "fast", sv])
        seg_videos.append(sv)
        seg_audios.append(wav)

        # Subtitles: split the segment text, time proportional to length
        speech = target - gap
        parts = chunks(text)
        weights = [len(p) for p in parts]
        t = t0
        for p, w in zip(parts, weights):
            d = speech * w / sum(weights)
            subs.append((t, t + d, p))
            t += d
        print(f"[seg {i:02}] {target:.2f}s (visual x{factor:.2f})")
        t0 += target

    with open(f"{WORK}/subs.srt", "w") as f:
        for k, (a, b, p) in enumerate(subs, 1):
            f.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{p}\n\n")

    for name, files in (("video", seg_videos), ("audio", seg_audios)):
        with open(f"{WORK}/{name}_list.txt", "w") as f:
            f.writelines(f"file '{p}'\n" for p in files)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/video_list.txt",
         "-c", "copy", f"{WORK}/video_all.mp4"])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/audio_list.txt",
         "-c", "copy", f"{WORK}/audio_all.wav"])

    style = ("FontName=DejaVu Sans,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=60")
    final = f"{OUT}/stolen_pitch.mp4"
    run(["ffmpeg", "-y", "-i", f"{WORK}/video_all.mp4", "-i", f"{WORK}/audio_all.wav",
         "-vf", f"scale={OUT_W}:{OUT_H}:flags=lanczos,subtitles={WORK}/subs.srt:force_style='{style}'",
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
         "-movflags", "+faststart", final])
    print(f"[done] {final} ({duration(final):.1f}s)")


if __name__ == "__main__":
    main()
