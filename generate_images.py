"""
Illustrated backdrops: one generated image per beat instead of stock footage.

The renderer already knows how to use images -- video.py turns any local image
into a clip with a slow zoom (100% -> 120%), which is the Ken Burns look these
stories want. All that was missing was something to produce the images, so this
module makes them and hands back file paths for video_materials.

Design choices that matter more than the code:

* No people, no faces, no recurring characters. Text-to-image cannot hold a
  person consistent across fifteen frames, and a near-miss face reads as
  uncanny in a way stock footage never does. These are anonymous first-person
  stories, so the imagery is deliberately environmental and symbolic -- rooms,
  objects, weather, light. That also sidesteps likeness problems entirely.
* One fixed style suffix on every prompt, and one seed per story, so the frames
  of a single video look like they belong together.
* Failure is never fatal. If image generation does not produce enough usable
  frames the caller falls back to Pexels, because a video that posts with stock
  footage beats a lane that silently stops publishing.

Provider is Pollinations: a plain GET, no API key, no account. That makes this
cheap to try and easy to swap -- everything provider-specific lives in
_fetch_one(). It is a free community service, so treat availability as
best-effort; that is exactly why the fallback exists.
"""
import hashlib
import os
import time
import urllib.parse

import requests

ENDPOINT = "https://image.pollinations.ai/prompt/"

# Appended to every prompt so a story's frames share a look.
STYLE = (
    "cinematic still, moody natural light, shallow depth of field, "
    "muted desaturated colour, film grain, no people, no faces, no text"
)

# What each beat of a story tends to be about, in order. The story text is not
# sent to the image model -- these are deliberately generic scene cues, which
# keeps prompts short, avoids leaking narrative detail into an external
# service, and stops the model trying to literally illustrate dialogue.
SCENE_CUES = [
    "an empty living room in late afternoon light",
    "a kitchen table with two cups, one untouched",
    "a hallway with a door ajar",
    "rain on a window at dusk",
    "a staircase in a quiet house",
    "an envelope on a wooden desk",
    "car headlights on a wet suburban street",
    "a cluttered garage with boxes",
    "a dining room set for a meal nobody came to",
    "a bedroom with an unmade bed and morning light",
    "a garden gone slightly wild",
    "a hospital corridor, out of focus",
    "an office at night, one lamp on",
    "a suitcase by a front door",
    "a mantelpiece with photo frames turned face down",
    "keys left on a kitchen counter",
    "a bench in an empty park",
    "a phone face down on a table",
]

TIMEOUT = 90
MAX_ATTEMPTS = 2


def _dimensions(aspect: str) -> tuple[int, int]:
    # Match what the renderer composites onto so nothing is upscaled.
    return (1080, 1920) if aspect == "9:16" else (1920, 1080)


def _story_seed(story: dict) -> int:
    """A stable per-story seed, so re-running a story reproduces its frames."""
    key = f"{story.get('title','')}|{story.get('tracking_tag','')}"
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def build_prompts(story: dict, count: int) -> list[str]:
    """One prompt per frame: a scene cue plus the fixed style."""
    theme = (story.get("theme") or "").split("/")[0].strip().lower()
    prompts = []
    for i in range(count):
        cue = SCENE_CUES[i % len(SCENE_CUES)]
        # The theme only nudges mood; it is not a subject instruction.
        prompts.append(f"{cue}, atmosphere of {theme or 'quiet tension'}, {STYLE}")
    return prompts


def _fetch_one(prompt: str, width: int, height: int, seed: int, dest: str) -> bool:
    """Everything provider-specific lives here. True if a usable file landed."""
    url = ENDPOINT + urllib.parse.quote(prompt, safe="")
    params = {"width": width, "height": height, "seed": seed,
              "model": "flux", "nologo": "true"}
    for attempt in range(MAX_ATTEMPTS):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            if resp.ok and resp.content and len(resp.content) > 10_000:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                return True
            detail = f"HTTP {resp.status_code}, {len(resp.content or b'')} bytes"
        except Exception as e:
            detail = str(e)[:120]
        if attempt < MAX_ATTEMPTS - 1:
            time.sleep(3)
    print(f"[images] gave up on a frame ({detail})")
    return False


def image_count(story: dict, voice_rate: float, clip_duration: int) -> int:
    """How many frames this story needs, from its word count.

    Narration runs ~2.85 words/sec at 1.0x, so the spoken length is known
    before anything is rendered. One extra frame covers rounding and any
    overshoot in the narration.
    """
    words = len(story.get("story", "").split())
    seconds = words / (2.85 * voice_rate)
    return max(1, int(seconds / clip_duration) + 1)


def generate_images(story: dict, count: int, out_dir: str, aspect: str) -> list[str]:
    """Generate `count` frames; return the paths that actually landed.

    Returns whatever succeeded rather than raising -- the caller decides
    whether it got enough to be worth using.
    """
    os.makedirs(out_dir, exist_ok=True)
    width, height = _dimensions(aspect)
    seed = _story_seed(story)
    prompts = build_prompts(story, count)

    paths = []
    started = time.monotonic()
    for i, prompt in enumerate(prompts):
        dest = os.path.join(out_dir, f"frame-{i:03d}.jpg")
        # Vary the seed per frame so the images differ, but derive it from the
        # story seed so the whole set is reproducible.
        if _fetch_one(prompt, width, height, seed + i, dest):
            paths.append(dest)
    elapsed = time.monotonic() - started
    print(f"[images] {len(paths)}/{count} frames in {elapsed:.0f}s "
          f"({width}x{height}, seed {seed})")
    return paths
