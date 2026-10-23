"""Build a 1280x720 YouTube thumbnail for a long-form story and set it.

    python thumbnail.py video.mp4 out.jpg "THE TEXT"

The picture is one scene from the video itself (the sharpest, best-lit of a
dozen sampled frames), darkened at the bottom with a short line of text over
it. The text comes from the story (see story_text). thumbnails.set needs a
phone-verified channel; images must be under 2 MB.
"""

import io
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

W, H = 1280, 720
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cartoon", "fredoka-700.ttf")
SAMPLES = 12
STOP = {"the", "a", "an", "of", "that", "how", "my", "his", "her", "their", "our", "when", "i",
        "to", "and", "in", "on", "for", "was", "were", "by", "with"}


def _duration(video: str) -> float:
    """Length in seconds, read from ffmpeg's banner so ffprobe is not needed."""
    err = subprocess.run(["ffmpeg", "-i", video], capture_output=True, text=True).stderr
    h, m, sec = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(sec)


def best_frame(video: str) -> Image.Image:
    """Sample frames between 8% and 60% of the video (past the intro, before
    the payoff) and keep the one with the most detail and a usable brightness."""
    dur = _duration(video)
    best, best_score = None, -1.0
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(SAMPLES):
            t = dur * (0.08 + 0.52 * i / (SAMPLES - 1))
            path = os.path.join(tmp, f"f{i}.jpg")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", video,
                            "-frames:v", "1", "-q:v", "2", path], check=True)
            if not os.path.exists(path):
                continue
            img = Image.open(path).convert("RGB")
            small = img.resize((320, 180)).convert("L")
            detail = ImageStat.Stat(small.filter(ImageFilter.FIND_EDGES)).mean[0]
            light = ImageStat.Stat(small).mean[0]
            score = detail - abs(light - 110) * 0.15
            if score > best_score:
                best, best_score = img.copy(), score
    if best is None:
        raise RuntimeError("no frame could be extracted")
    return best


def hook_text(title: str, limit: int = 4) -> str:
    """Fallback text: the title's first few content words."""
    words = re.findall(r"[\w'’-]+", title)
    keep = [w for w in words if w.lower() not in STOP]
    if len(keep) < 3:
        keep = words
    return " ".join(keep[:limit]).upper()


def story_text(story: dict) -> str:
    """3-5 words of curiosity-gap text drawn from the story itself, written by
    Groq; falls back to the title's key words if Groq is unavailable."""
    title = story.get("title", "")
    if os.environ.get("GROQ_API_KEY"):
        try:
            from generate_stories_cloud import call_groq
            dna = story.get("dna", {})
            reply = call_groq(
                "You write YouTube thumbnail text. Reply with JSON {\"text\": \"...\"}: 3 to 5 words, "
                "ALL CAPS, no punctuation except ? or !, naming the betrayal or twist of this story "
                "so a stranger wants to know what happens. Never reuse the title wording wholesale.",
                f"Title: {title}\nConflict: {dna.get('conflict', '')}\nHook: {dna.get('hook', '')}")
            text = re.sub(r"[^A-Za-z0-9?! ']", "", str(reply.get("text", ""))).upper().split()
            if 2 <= len(text) <= 6:
                return " ".join(text)
        except Exception as e:
            print(f"[thumbnail] Groq text failed, using title words: {e}")
    return hook_text(title)


def _fit_text(d, text, max_w, max_h):
    words = text.split()
    best = None
    for n in (1, 2, 3):
        per = -(-len(words) // n)
        chunks = [" ".join(words[i:i + per]) for i in range(0, len(words), per)]
        for size in range(220, 59, -6):
            f = ImageFont.truetype(FONT, size)
            if (max(d.textlength(c, font=f) for c in chunks) <= max_w
                    and len(chunks) * size * 1.05 <= max_h):
                if not best or size > best[2]:
                    best = (f, chunks, size)
                break
    return best or (ImageFont.truetype(FONT, 60), words, 60)


def make_thumbnail(video: str, text: str, out_path: str) -> str:
    img = best_frame(video)
    scale = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
    img = img.crop(((img.width - W) // 2, (img.height - H) // 2,
                    (img.width - W) // 2 + W, (img.height - H) // 2 + H))

    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        sd.line([(0, y), (W, y)], fill=int(200 * max(0, (y / H - 0.25) / 0.75) ** 1.2))
    img.paste((0, 0, 0), (0, 0), shade)

    d = ImageDraw.Draw(img)
    font, lines, size = _fit_text(d, text, W - 120, 300)
    y = H - 40 - len(lines) * size * 1.05
    for line in lines:
        for dx, dy in [(-6, -6), (6, -6), (-6, 6), (6, 6), (0, 9)]:
            d.text((60 + dx, y + dy), line, font=font, fill=(20, 10, 30))
        d.text((60, y), line, font=font, fill=(255, 245, 120))
        y += size * 1.05

    for q in (88, 80, 70, 60):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q)
        if buf.tell() < 1_900_000:
            break
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    return out_path


def set_thumbnail(youtube, video_id: str, path: str):
    from googleapiclient.http import MediaFileUpload
    youtube.thumbnails().set(
        videoId=video_id, media_body=MediaFileUpload(path, mimetype="image/jpeg")).execute()


if __name__ == "__main__":
    print(make_thumbnail(sys.argv[1], sys.argv[3], sys.argv[2]))
