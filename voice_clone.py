"""Narrate in a cloned voice with Chatterbox (Resemble AI, MIT licence).

The reference recording never lives in the repo, which is public: it is kept
in the private Supabase bucket at rendered-videos/voice/ and downloaded at run
time. Chatterbox clones from that one sample (zero-shot, no training).

Word timings for the captions come from faster-whisper run over the result,
since Chatterbox does not report them.

    python voice_clone.py "Some text to read." out.wav   # needs SUPABASE_* env
"""

import os
import re
import subprocess
import sys
import tempfile

VOICE_BUCKET = "rendered-videos"
VOICE_PREFIX = "voice"
# Chatterbox degrades on long inputs, so the story is read in sentence groups
# of at most this many characters and joined.
MAX_CHUNK_CHARS = 280
EXAGGERATION = 0.6   # 0.5 is neutral; higher reads more dramatically
CFG_WEIGHT = 0.5

_model = None


def fetch_reference(sb, out_dir: str) -> str:
    """Download the newest file in voice/ and convert it to 24kHz mono wav."""
    files = [f for f in sb.storage.from_(VOICE_BUCKET).list(VOICE_PREFIX)
             if f.get("name") and not f["name"].startswith(".")]
    if not files:
        raise RuntimeError(f"no voice sample in {VOICE_BUCKET}/{VOICE_PREFIX}/")
    files.sort(key=lambda f: f.get("updated_at") or "", reverse=True)
    name = files[0]["name"]
    raw = os.path.join(out_dir, "ref_raw" + os.path.splitext(name)[1])
    with open(raw, "wb") as f:
        f.write(sb.storage.from_(VOICE_BUCKET).download(f"{VOICE_PREFIX}/{name}"))
    ref = os.path.join(out_dir, "ref.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw,
                    "-ac", "1", "-ar", "24000", ref], check=True)
    print(f"[voice] Reference sample: {name}")
    return ref


def _chunks(text: str) -> list[str]:
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        if cur and len(cur) + len(sent) + 1 > MAX_CHUNK_CHARS:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out


def synth_clone(text: str, ref_wav: str, out_wav: str):
    global _model
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    if _model is None:
        _model = ChatterboxTTS.from_pretrained(device="cpu")
    pieces = []
    gap = torch.zeros(1, int(_model.sr * 0.25))
    for i, chunk in enumerate(_chunks(text)):
        wav = _model.generate(chunk, audio_prompt_path=ref_wav,
                              exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
        pieces += [wav, gap]
        print(f"[voice] Chunk {i + 1}: {len(chunk)} chars -> {wav.shape[1] / _model.sr:.1f}s")
    torchaudio.save(out_wav, torch.cat(pieces[:-1], dim=1), _model.sr)


def word_timings(audio_path: str) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True, language="en")
    return [{"text": w.word.strip(), "start": w.start, "end": w.end}
            for seg in segments for w in seg.words if w.word.strip()]


def narrate(text: str, mp3_path: str, sb) -> list[dict]:
    """Cloned-voice drop-in for cartoon_render.synth()."""
    work = tempfile.mkdtemp(prefix="voice_")
    ref = fetch_reference(sb, work)
    wav = os.path.join(work, "clone.wav")
    synth_clone(text, ref, wav)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav,
                    "-b:a", "192k", mp3_path], check=True)
    return word_timings(mp3_path)


if __name__ == "__main__":
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    words = narrate(sys.argv[1], sys.argv[2], sb)
    print(f"[voice] {len(words)} timed words")
