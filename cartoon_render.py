"""Cartoon lane: render a queued story as an animated cartoon Short.

Instead of Pexels stock footage, each beat of the story gets its own scene: a
setting (dining room, bedroom, office...), the characters in it with a facial
expression, and optionally a prop that shows what the narration describes (the
text messages, the incoming call, the document). The scenes are drawn and
animated by cartoon/template.html and rendered to MP4 by HyperFrames (headless
Chrome + ffmpeg), so there is no image generation and no per-video cost.

Pipeline: edge-tts narration with word timings -> story split into beats ->
Groq turns the beats into a scene plan (heuristic fallback when Groq is out of
quota) -> template + plan -> `npx hyperframes render` -> narration and music
muxed on with ffmpeg.

Run directly to render a local preview without touching Supabase:
    python cartoon_render.py story.json out.mp4
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "cartoon")
VOICE = "en-US-JennyNeural"
VOICE_RATE = "+40%"          # the short lane's 1.4x
HYPERFRAMES = os.environ.get("HYPERFRAMES_CMD", "npx --yes hyperframes@0.8.141")

SETTINGS = ["dining", "bedroom", "living", "kitchen", "office", "boardroom",
            "wedding", "hospital", "street", "party", "car", "restaurant"]
ROLES = ["narrator", "mom", "dad", "brother", "sister", "husband", "wife",
         "boyfriend", "girlfriend", "mil", "fil", "grandma", "boss", "friend",
         "lawyer", "cousin", "kid", "stranger"]
MOODS = ["calm", "happy", "shocked", "angry", "sad", "smug"]

# ~3.9 words/sec at 1.4x, so 10-22 words is a 3-6s scene.
BEAT_MIN_WORDS, BEAT_MAX_WORDS = 10, 22
CAPTION_WORDS = 3

# Applied on top of the shared per-track LUFS levelling. The first posted
# cartoon (2026-10-08) had the music too loud under the narration: this mix
# adds edge-tts audio raw, without the voice boost the stock lane gets.
BGM_SCALE = 0.9


# ---------- narration ----------

def synth(text: str, mp3_path: str) -> list[dict]:
    """Narrate text to mp3_path; return [{text, start, end}] per spoken word."""
    import edge_tts

    async def run():
        words = []
        comm = edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, boundary="WordBoundary")
        with open(mp3_path, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 1e7
                    words.append({"text": chunk["text"], "start": start,
                                  "end": start + chunk["duration"] / 1e7})
        return words

    return asyncio.run(run())


def audio_seconds(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


# ---------- beats ----------

def split_beats(story: str) -> list[str]:
    """Sentences, long ones cut at ; or , and short ones merged forward."""
    parts = []
    for sent in re.split(r"(?<=[.!?])\s+", story.strip()):
        words = sent.split()
        while len(words) > BEAT_MAX_WORDS:
            head = " ".join(words[:BEAT_MAX_WORDS + 4])
            cut = max(head.rfind("; "), head.rfind(", "), head.rfind(" while "),
                      head.rfind(" and "))
            n = len(head[:cut + 1].split()) if cut > len(" ".join(words[:BEAT_MIN_WORDS])) else BEAT_MAX_WORDS
            parts.append(" ".join(words[:n]))
            words = words[n:]
        if words:
            parts.append(" ".join(words))
    beats = []
    for p in parts:
        if (beats and len(beats[-1].split()) < BEAT_MIN_WORDS
                and len(beats[-1].split()) + len(p.split()) <= BEAT_MAX_WORDS + 6):
            beats[-1] += " " + p
        else:
            beats.append(p)
    if len(beats) > 1 and len(beats[-1].split()) < BEAT_MIN_WORDS // 2:
        beats[-2] += " " + beats.pop()
    return beats


# ---------- scene plan ----------

PLAN_SYSTEM = f"""You storyboard a cartoon Short. The narrator is a woman telling her own story in first person.
For each numbered beat, choose ONE scene. Reply with JSON only:
{{"scenes":[{{"beat":1,"setting":"...","chars":[{{"role":"narrator","mood":"..."}}],"prop":null,"label":"..."}}]}}
Rules:
- setting: one of {SETTINGS}
- chars: 1 or 2 people visible in that moment. role: one of {ROLES} ("mil"/"fil" = in-laws). Put the narrator first when she is present.
- mood: one of {MOODS} -- what that character feels at that moment.
- prop: null, or what the viewer should SEE on screen when the beat describes it:
  {{"type":"phone","from":"<contact name>","messages":["<=8 words","<=8 words"]}} for texts/chats,
  {{"type":"call","from":"<caller>"}} for a phone call,
  {{"type":"document","title":"<=3 words","line":"<=8 words","stamp":"<=2 words or empty>"}} for letters, wills, contracts, receipts.
  With a prop, list only 1 character. Use props on 2-4 beats, where they make the moment visual.
- label: a punchy on-screen caption for the beat, max 5 words (e.g. "2 AM. Mom calls.", "He took the credit").
- Vary settings and moods so consecutive scenes look different. Never invent events not in the beat."""


def plan_with_groq(beats: list[str]) -> list[dict]:
    from generate_stories_cloud import call_groq
    user = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(beats))
    return call_groq(PLAN_SYSTEM, user)["scenes"]


KEYWORD_ROLES = [
    ("mother-in-law", "mil"), ("father-in-law", "fil"), ("in-laws", "mil"),
    ("grandma", "grandma"), ("grandmother", "grandma"), ("mother", "mom"),
    ("mom", "mom"), ("father", "dad"), ("dad", "dad"), ("brother", "brother"),
    ("sister", "sister"), ("husband", "husband"), ("fiancé", "boyfriend"),
    ("fiance", "boyfriend"), ("boyfriend", "boyfriend"), ("wife", "wife"),
    ("boss", "boss"), ("manager", "boss"), ("lawyer", "lawyer"),
    ("attorney", "lawyer"), ("friend", "friend"), ("cousin", "cousin"),
    ("son", "kid"), ("daughter", "kid"),
]
KEYWORD_SETTINGS = [
    ("dinner", "dining"), ("table", "dining"), ("wedding", "wedding"),
    ("hospital", "hospital"), ("office", "office"), ("board", "boardroom"),
    ("meeting", "boardroom"), ("court", "boardroom"), ("kitchen", "kitchen"),
    ("bed", "bedroom"), ("night", "bedroom"), ("party", "party"),
    ("birthday", "party"), ("car", "car"), ("restaurant", "restaurant"),
    ("street", "street"), ("living room", "living"),
]
KEYWORD_MOODS = [
    ("shock", "shocked"), ("froze", "shocked"), ("gasp", "shocked"),
    ("stunned", "shocked"), ("furious", "angry"), ("anger", "angry"),
    ("yell", "angry"), ("shout", "angry"), ("cried", "sad"), ("tears", "sad"),
    ("humiliat", "sad"), ("invisible", "sad"), ("smirk", "smug"),
    ("laugh", "happy"), ("relief", "happy"), ("finally", "happy"),
    ("apolog", "happy"), ("proud", "happy"),
]


def plan_heuristic(beats: list[str]) -> list[dict]:
    scenes, last_setting = [], "living"
    for i, b in enumerate(beats):
        low = b.lower()
        setting = next((s for k, s in KEYWORD_SETTINGS if k in low), last_setting)
        last_setting = setting
        other = next((r for k, r in KEYWORD_ROLES if k in low), None)
        mood = next((m for k, m in KEYWORD_MOODS if k in low), "calm")
        prop = None
        if re.search(r"\b(text|texts|message|messages|chat)\b", low):
            prop = {"type": "phone", "from": "Unknown", "messages": [" ".join(b.split()[:7]) + "…"]}
        elif re.search(r"\b(call|called|calling|phone)\b", low):
            prop = {"type": "call", "from": (other or "Unknown").title()}
        elif re.search(r"\b(document|contract|will|letter|paperwork|receipt|affidavit|trademark)\b", low):
            prop = {"type": "document", "title": "DOCUMENT", "line": " ".join(b.split()[:6]), "stamp": ""}
        chars = [{"role": "narrator", "mood": mood}]
        if other and not prop:
            chars.append({"role": other, "mood": "smug" if mood in ("sad", "shocked") else "calm"})
        scenes.append({"beat": i + 1, "setting": setting, "chars": chars, "prop": prop,
                       "label": " ".join(b.split()[:4]) if i == 0 else ""})
    return scenes


def _clip(s, n):
    return " ".join(str(s or "").split()[:n])


def sanitize(scenes: list[dict], n_beats: int) -> list[dict]:
    """Coerce whatever the model returned into exactly one valid scene per beat."""
    by_beat = {}
    for sc in scenes or []:
        try:
            by_beat[int(sc.get("beat"))] = sc
        except (TypeError, ValueError):
            continue
    out, prev = [], None
    for i in range(1, n_beats + 1):
        sc = by_beat.get(i) or prev or {"setting": "living", "chars": [{"role": "narrator", "mood": "calm"}]}
        setting = sc.get("setting") if sc.get("setting") in SETTINGS else (prev or {}).get("setting", "living")
        chars = []
        for c in (sc.get("chars") or [])[:2]:
            if isinstance(c, dict):
                chars.append({"role": c.get("role") if c.get("role") in ROLES else "stranger",
                              "mood": c.get("mood") if c.get("mood") in MOODS else "calm"})
        if not chars:
            chars = [{"role": "narrator", "mood": "calm"}]
        prop = sc.get("prop") if isinstance(sc.get("prop"), dict) else None
        if prop:
            t = prop.get("type")
            if t == "phone":
                msgs = [_clip(m, 8) for m in (prop.get("messages") or []) if str(m).strip()][:3]
                prop = {"type": "phone", "from": _clip(prop.get("from"), 3) or "Unknown",
                        "messages": msgs or ["…"]}
            elif t == "call":
                prop = {"type": "call", "from": _clip(prop.get("from"), 3) or "Unknown"}
            elif t == "document":
                prop = {"type": "document", "title": _clip(prop.get("title"), 3).upper() or "DOCUMENT",
                        "line": _clip(prop.get("line"), 8), "stamp": _clip(prop.get("stamp"), 2).upper()}
            else:
                prop = None
        cur = {"setting": setting, "chars": chars, "prop": prop, "label": _clip(sc.get("label"), 5)}
        out.append(cur)
        prev = cur
    return out


def make_plan(beats: list[str]) -> list[dict]:
    if os.environ.get("GROQ_API_KEY"):
        try:
            scenes = sanitize(plan_with_groq(beats), len(beats))
            print(f"[cartoon] Scene plan from Groq: {len(scenes)} scenes")
            return scenes
        except Exception as e:
            print(f"[cartoon] Groq scene plan failed ({str(e)[:160]}); using keyword plan.")
    scenes = sanitize(plan_heuristic(beats), len(beats))
    print(f"[cartoon] Keyword scene plan: {len(scenes)} scenes")
    return scenes


# ---------- timing ----------

def time_scenes(scenes, beats, words, duration):
    """Start each scene at the spoken time of its beat's first word.

    edge-tts word boundaries do not map 1:1 to str.split() tokens (numbers,
    hyphens, punctuation), so beat offsets are scaled onto the boundary list.
    """
    counts = [len(b.split()) for b in beats]
    total = sum(counts) or 1
    acc = 0
    for sc, n in zip(scenes, counts):
        idx = min(len(words) - 1, round(acc / total * len(words))) if words else 0
        sc["start"] = 0.0 if acc == 0 or not words else round(words[idx]["start"], 3)
        acc += n
    for a, b in zip(scenes, scenes[1:]):
        a["end"] = b["start"]
    scenes[-1]["end"] = duration
    return scenes


def caption_groups(words, duration):
    groups = []
    for i in range(0, len(words), CAPTION_WORDS):
        g = words[i:i + CAPTION_WORDS]
        groups.append({"words": [{"text": w["text"], "start": round(w["start"], 3)} for w in g],
                       "start": round(g[0]["start"], 3)})
    for a, b in zip(groups, groups[1:]):
        a["end"] = b["start"]
    if groups:
        groups[-1]["end"] = duration
    return groups


# ---------- render ----------

def build_project(plan: dict, out_dir: str):
    for f in ("gsap.min.js", "fredoka-500.ttf", "fredoka-700.ttf"):
        shutil.copy(os.path.join(ASSETS, f), out_dir)
    with open(os.path.join(ASSETS, "template.html"), encoding="utf-8") as f:
        html = f.read()
    html = (html.replace("__DURATION__", f"{plan['duration']:.2f}")
                .replace("__PLAN__", json.dumps(plan, ensure_ascii=False)))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(out_dir, "hyperframes.json"), "w") as f:
        json.dump({"paths": {"blocks": "compositions", "components": "compositions/components",
                             "assets": "assets"}}, f)
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump({"id": "cartoon", "name": "cartoon"}, f)


def render(story: dict, out_path: str, bgm: tuple[str, float] | None = None) -> str:
    work = tempfile.mkdtemp(prefix="cartoon_")
    proj = os.path.join(work, "proj")
    os.makedirs(proj)
    narration = os.path.join(work, "voice.mp3")

    text = story["story"]
    words = synth(text, narration)
    voice_len = audio_seconds(narration)
    duration = round(voice_len + 0.8, 2)
    print(f"[cartoon] Narration {voice_len:.1f}s, {len(words)} timed words")

    beats = split_beats(text)
    scenes = time_scenes(make_plan(beats), beats, words, duration)
    plan = {"duration": duration, "scenes": scenes, "captions": caption_groups(words, duration)}
    with open(os.path.join(work, "plan.json"), "w") as f:
        json.dump(plan, f, indent=1)
    build_project(plan, proj)

    silent = os.path.join(work, "silent.mp4")
    cmd = HYPERFRAMES.split() + ["render", proj, "-o", silent, "-q", "standard", "-f", "30"]
    print(f"[cartoon] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    inputs = ["-i", silent, "-i", narration]
    if bgm:
        path, gain = bgm
        gain *= BGM_SCALE
        inputs += ["-stream_loop", "-1", "-i", path]
        mix = (f"[2:a]volume={gain},afade=t=out:st={max(0, duration - 1.5)}:d=1.5[m];"
               f"[1:a][m]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        mix = "[1:a]anull[a]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", mix,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{duration}", "-movflags", "+faststart", out_path], check=True)
    print(f"[cartoon] Rendered {out_path}")
    return out_path


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        st = json.load(f)
    render(st.get("payload", st), sys.argv[2] if len(sys.argv) > 2 else "cartoon.mp4")
