"""Build a WanGP headless batch (settings JSON list) from clip prompts.

Settings are copied from a working clip (clip 9, MiniMax H3 Ref2VA PDD 8-step).
Run here, upload the JSON to /workspace/batch/, then on the pod:
    cd /root/Wan2GP && source /root/venv/bin/activate
    python wgp.py --process /workspace/batch/<name>.json --output-dir /workspace/outputs/<name>
"""
import json, sys

CAST = "/workspace/cast"
BASE = {
    "image_mode": 0, "resolution": "704x1280", "video_length": 107, "seed": -1,
    "num_inference_steps": 8, "guidance_phases": 1, "flow_shift": 12, "sample_solver": "euler",
    "repeat_generation": 1, "multi_prompts_gen_type": "PG", "activated_loras": [],
    "image_prompt_type": "", "video_prompt_type": "I", "audio_prompt_type": "",
    "image_refs_relative_size": 100, "remove_background_images_ref": 0,
    "custom_settings": {"h3_mask_mode": "grouped_rows"},
    "model_type": "minimax_h3_ref2va_pruned_pdd", "video_quality": "libx264_8",
}

def ref(name):
    actor = name.split("_")[0].capitalize()
    return f"{CAST}/{actor}/{name}.jpg"

def build(clips, out):
    tasks = []
    for c in clips:
        t = dict(BASE, prompt=c["prompt"].strip(), image_refs=[ref(r) for r in c["refs"]],
                 output_filename=c["name"])
        tasks.append(t)
    json.dump(tasks, open(out, "w"), indent=1)
    print(f"{out}: {len(tasks)} clips")

if __name__ == "__main__":
    from clips_part1 import CLIPS
    build(CLIPS, sys.argv[1] if len(sys.argv) > 1 else "part1_batch1.json")
