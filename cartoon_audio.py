"""Sound for the cartoon lane: pauses, sound effects and the final mix.

Three rules borrowed from lemo-opuscar's DIRECTOR.md / TECHNIQUE.md
(github.com/lemomo-ai/lemo-opuscar, MIT):

- Every visible action gets a sound. A phone on screen buzzes, a call rings, a
  document lands with a paper slap, a scene change has a soft whoosh, and the
  hook and the turn land on a low hit. The effects are synthesised here with
  numpy, so there are no sample files and nothing to license.
- Real silences before the turn. The narration is cut open just before the
  twist beat (and, shorter, before the last beat) and the music dips under the
  gap, so the line after the silence is the one that lands.
- A checked mix. The voice is compressed, the music is held at least
  VOICE_OVER_MUSIC_DB under it, and the whole mix is loudness-normalised to
  -14 LUFS in two passes, then measured and logged.
"""

import json
import re
import subprocess
import wave

import numpy as np

SR = 48000
TURN_PAUSE = 0.8      # seconds of silence before the twist beat
END_PAUSE = 0.5       # before the last beat
MUSIC_DIP = 0.15      # music gain multiplier inside a pause
VOICE_OVER_MUSIC_DB = 10.0
TARGET_LUFS = -14.0


# ---------- wav helpers ----------

def decode(path: str, out_wav: str):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path,
                    "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", out_wav], check=True)


def read_wav(path: str) -> np.ndarray:
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(path: str, x: np.ndarray):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def lufs(path: str) -> float:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                          "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", err)[-1])


# ---------- pauses ----------

def beat_word_index(beats: list[str], n_words: int) -> list[int]:
    """Index into the edge-tts word list where each beat starts (same scaling
    as cartoon_render.time_scenes: boundaries do not map 1:1 to split())."""
    counts = [len(b.split()) for b in beats]
    total = sum(counts) or 1
    out, acc = [], 0
    for n in counts:
        out.append(min(n_words - 1, round(acc / total * n_words)) if n_words else 0)
        acc += n
    return out


def turn_beat(scenes: list[dict]) -> int | None:
    """The twist: the first shocked/angry or prop beat past ~45% of the story,
    else the beat at 60%. None for stories too short to have a middle."""
    n = len(scenes)
    if n < 4:
        return None
    for i in range(max(2, int(n * 0.45)), n - 1):
        sc = scenes[i]
        if sc.get("prop") or any(c["mood"] in ("shocked", "angry") for c in sc["chars"]):
            return i
    return round(n * 0.6)


def insert_pauses(voice_wav: str, out_wav: str, words: list[dict],
                  cuts: list[tuple[int, float]]):
    """Open silences in the narration before words[idx] for each (idx, secs).

    Returns (shifted words, pause windows [(start, end)] in output time).
    """
    x = read_wav(voice_wav)
    words = [dict(w) for w in words]
    pieces, windows, last, shift = [], [], 0, 0.0
    for idx, secs in sorted(cuts):
        if not 0 < idx < len(words):
            continue
        # Cut in the gap between the previous word and this one.
        at = (words[idx - 1]["end"] + words[idx]["start"]) / 2
        s = int(at * SR)
        pieces += [x[last:s], np.zeros(int(secs * SR), np.float32)]
        windows.append((round(at + shift, 3), round(at + shift + secs, 3)))
        last = s
        for w in words[idx:]:
            w["start"] += secs
            w["end"] += secs
        shift += secs
    pieces.append(x[last:])
    write_wav(out_wav, np.concatenate(pieces))
    return words, windows


# ---------- sound effects ----------

def _env(n, attack, release):
    a, r = int(attack * SR), int(release * SR)
    e = np.ones(n, np.float32)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def _lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same").astype(np.float32)


def _t(secs):
    return np.arange(int(secs * SR)) / SR


def _rng(seed):
    return np.random.default_rng(seed)


def whoosh(seed=1):
    t = _t(0.45)
    x = _lowpass(_rng(seed).standard_normal(len(t)).astype(np.float32), 24)
    return 0.10 * x * _env(len(t), 0.25, 0.2)


def buzz():
    t = _t(0.18)
    burst = np.sign(np.sin(2 * np.pi * 170 * t)) * 0.5 + np.sin(2 * np.pi * 340 * t) * 0.3
    burst = _lowpass(burst.astype(np.float32), 6) * _env(len(t), 0.005, 0.03)
    gap = np.zeros(int(0.1 * SR), np.float32)
    return 0.22 * np.concatenate([burst, gap, burst])


def ring():
    t = _t(0.9)
    f = np.where(np.sin(2 * np.pi * 18 * t) > 0, 1320, 1660)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
    return 0.10 * x * _env(len(t), 0.01, 0.15)


def paper(seed=2):
    t = _t(0.14)
    x = np.diff(_rng(seed).standard_normal(len(t) + 1)).astype(np.float32)
    return 0.20 * x * np.exp(-t * 30).astype(np.float32)


def hit(seed=3):
    t = _t(0.7)
    f = 95 * np.exp(-t * 3) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    click = _rng(seed).standard_normal(len(t)) * np.exp(-t * 120) * 0.3
    return (0.55 * (body + click)).astype(np.float32)


PROP_SFX = {"phone": buzz, "call": ring, "document": paper}


def sfx_events(scenes: list[dict], turn: int | None) -> list[tuple[float, np.ndarray]]:
    events = [(0.0, hit())]  # the hook lands on a hit
    for i, sc in enumerate(scenes):
        if i:
            events.append((max(0.0, sc["start"] - 0.2), whoosh(i)))
        prop = (sc.get("prop") or {}).get("type")
        if prop in PROP_SFX:
            events.append((sc["start"] + 0.15, PROP_SFX[prop]()))
        if i == turn:
            events.append((sc["start"], hit(i)))
    return events


def sfx_track(events, duration: float, out_wav: str):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    for at, snd in events:
        s = int(at * SR)
        e = min(len(track), s + len(snd))
        track[s:e] += snd[:e - s]
    write_wav(out_wav, track[:int(duration * SR)])


# ---------- final mix ----------

def mix(video: str, voice_wav: str, sfx_wav: str, out_path: str, duration: float,
        bgm: tuple[str, float] | None, pauses: list[tuple[float, float]]):
    voice_lufs = lufs(voice_wav)
    inputs = ["-i", video, "-i", voice_wav, "-i", sfx_wav]
    # Compress the voice first: TTS peaks are high against its average level,
    # which makes it sound quieter than it measures next to music.
    chain = ["[1:a]acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2[v]"]
    labels = "[v][2:a]"
    n = 2
    if bgm:
        path, gain = bgm
        music_lufs = lufs(path) + 20 * np.log10(max(gain, 1e-6))
        gap = voice_lufs - music_lufs
        if gap < VOICE_OVER_MUSIC_DB:
            gain *= 10 ** ((gap - VOICE_OVER_MUSIC_DB) / 20)
            print(f"[cartoon] Music lowered to keep it {VOICE_OVER_MUSIC_DB:.0f} dB under the voice")
            gap = VOICE_OVER_MUSIC_DB
        print(f"[cartoon] Voice {voice_lufs:.1f} LUFS, music {gap:.1f} dB under it")
        dips = "".join(f",volume=enable='between(t,{a},{b})':volume={MUSIC_DIP}" for a, b in pauses)
        inputs += ["-stream_loop", "-1", "-i", path]
        chain.append(f"[3:a]volume={gain:.5f}{dips},"
                     f"afade=t=out:st={max(0, duration - 1.5)}:d=1.5[m]")
        labels += "[m]"
        n = 3
    chain.append(f"{labels}amix=inputs={n}:duration=first:normalize=0[pre]")
    graph = ";".join(chain)

    # Two-pass loudnorm: measure, then apply with the measured values so the
    # result is a linear gain to -14 LUFS rather than dynamic pumping.
    first = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", *inputs, "-filter_complex",
         graph + f";[pre]loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:print_format=json[a]",
         "-map", "[a]", "-t", f"{duration}", "-f", "null", "-"],
        capture_output=True, text=True, check=True).stderr
    m = json.loads(first[first.rindex("{"):first.rindex("}") + 1])
    norm = (f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:"
            f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
            f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex",
                    graph + f";[pre]{norm},aresample=48000[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{duration}", "-movflags", "+faststart", out_path], check=True)
    print(f"[cartoon] Final mix {lufs(out_path):.1f} LUFS (target {TARGET_LUFS:.0f})")
