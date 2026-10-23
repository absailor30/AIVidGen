"""Build a 1280x720 YouTube thumbnail for a long-form story and set it.

    python thumbnail.py "The Night the Photo Album Fell Apart" out.jpg

A character cut-out from characters/ is used when one exists (see its README);
otherwise a simple cartoon face is drawn, so this works before any art is made.
thumbnails.set needs a phone-verified channel; images must be under 2 MB.
"""

import glob
import hashlib
import io
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cartoon", "fredoka-700.ttf")
CHAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "characters")
PALETTES = [((255, 94, 98), (60, 20, 90)), ((255, 190, 11), (120, 20, 40)),
            ((0, 180, 216), (20, 20, 70)), ((255, 75, 145), (40, 15, 80))]
MOODS = {"shocked": r"stole|fraud|secret|exposed|caught|forged|fake|hidden|discover",
         "angry": r"betray|lie|revenge|cheat|sabotage|ruin",
         "sad": r"lost|fell|apart|alone|gone|cry|funeral|died",
         "smug": r"won|turn|comeback|glow|justice|payoff"}
STOP = {"the", "a", "an", "of", "that", "how", "my", "his", "her", "their", "our", "when", "i",
        "to", "and", "in", "on", "for", "was", "were", "by", "with", "friend's"}


def hook_text(title: str, limit: int = 4) -> str:
    """Short, loud version of the title: filler words dropped, then the first
    `limit` words that remain (so it never ends on a dangling 'MY')."""
    words = re.findall(r"[\w'’-]+", title)
    keep = [w for w in words if w.lower() not in STOP]
    if len(keep) < 3:
        keep = words
    return " ".join(keep[:limit]).upper()


def mood_for(title: str) -> str:
    for mood, pat in MOODS.items():
        if re.search(pat, title, re.I):
            return mood
    return "shocked"


def _character(mood: str, rng: random.Random):
    files = glob.glob(os.path.join(CHAR_DIR, "*.png"))
    if not files:
        return None
    match = [f for f in files if f.endswith(f"_{mood}.png")] or \
            [f for f in files if "_" not in os.path.basename(f)] or files
    return Image.open(rng.choice(sorted(match))).convert("RGBA")


def _draw_face(size: int, mood: str) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size // 2
    d.ellipse([8, 8, size - 8, size - 8], fill=(255, 214, 170), outline=(40, 20, 20), width=10)
    ey, ex = int(size * .42), int(size * .2)
    for sx in (-1, 1):
        x = c + sx * ex
        r = int(size * (.1 if mood == "shocked" else .07))
        d.ellipse([x - r, ey - r, x + r, ey + r], fill="white", outline=(40, 20, 20), width=6)
        d.ellipse([x - r // 3, ey - r // 3, x + r // 3, ey + r // 3], fill=(40, 20, 20))
        tilt = {"angry": sx * -1, "sad": sx, "smug": 0, "shocked": 0}[mood] * 28
        d.line([x - 45, ey - r - 25 + (tilt if sx < 0 else -tilt) * .0 - tilt,
                x + 45, ey - r - 25 + tilt], fill=(40, 20, 20), width=14)
    my = int(size * .72)
    if mood == "shocked":
        d.ellipse([c - 45, my - 55, c + 45, my + 55], fill=(90, 20, 30), outline=(40, 20, 20), width=8)
    elif mood == "sad":
        d.arc([c - 70, my - 20, c + 70, my + 70], 200, 340, fill=(40, 20, 20), width=12)
    else:
        d.arc([c - 80, my - 60, c + 80, my + 40], 20, 160, fill=(40, 20, 20), width=12)
    return img


def _fit_text(d, text, max_w, max_h):
    """Largest font that fits when the words are split over 1-3 lines."""
    words = text.split()
    best = None
    for n in (1, 2, 3):
        per = -(-len(words) // n)
        chunks = [" ".join(words[i:i + per]) for i in range(0, len(words), per)]
        for size in range(230, 59, -6):
            f = ImageFont.truetype(FONT, size)
            if (max(d.textlength(c, font=f) for c in chunks) <= max_w
                    and len(chunks) * size * 1.05 <= max_h):
                if not best or size > best[2]:
                    best = (f, chunks, size)
                break
    return best or (ImageFont.truetype(FONT, 60), words, 60)


def make_thumbnail(title: str, out_path: str) -> str:
    rng = random.Random(int(hashlib.md5(title.encode()).hexdigest()[:8], 16))
    mood = mood_for(title)
    top, bot = rng.choice(PALETTES)
    img = Image.new("RGB", (W, H))
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))

    face = _character(mood, rng) or _draw_face(520, mood)
    scale = min(560 / face.width, 640 / face.height) if face.height > 640 else 1
    face = face.resize((int(face.width * scale), int(face.height * scale)))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glow.paste(face, (W - face.width - 20, H - face.height - 10), face)
    shadow = glow.filter(ImageFilter.GaussianBlur(18))
    img.paste((255, 255, 255), (0, 0), shadow.split()[3].point(lambda a: a // 2))
    img.paste(glow, (0, 0), glow)

    d = ImageDraw.Draw(img)
    font, lines, size = _fit_text(d, hook_text(title), 690, 600)
    y = (H - len(lines) * size * 1.05) / 2
    for line in lines:
        for dx, dy in [(-6, -6), (6, -6), (-6, 6), (6, 6), (0, 9)]:
            d.text((50 + dx, y + dy), line, font=font, fill=(20, 10, 30))
        d.text((50, y), line, font=font, fill=(255, 245, 120))
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
    print(make_thumbnail(sys.argv[1], sys.argv[2]))
