"""MiniMax-H3 + Turbo LoRA on a 100 GB-RAM pod, two phases so only one 62 GB
half is in RAM at a time: (1) Qwen3-VL conditioner encodes every job,
(2) the generator denoises. Weights stream to cuda:0 block by block.
    python run_h3.py jobs.json   # [{"id","prompt","seconds","seed","canvas":[h,w],"image"?}]
"""
import gc, json, os, sys, time
import torch
sys.path.insert(0, "/workspace/h3/sp")
os.environ.setdefault("H3_LIGHTX", "off"); os.environ["H3_MYSTIC"] = "off"
from diffusers.hooks import apply_group_offloading
from diffusers.utils import encode_video
from PIL import Image, ImageOps
from h3_split_blocks import MiniMaxH3ConditionerBlocks, MiniMaxH3GeneratorBlocks

REPO, OUT = "/workspace/h3/model", "/workspace/out"
os.makedirs(OUT, exist_ok=True)
jobs = json.load(open(sys.argv[1]))
dev = torch.device("cuda:0")

def frames(sec):
    f = max(1, round(sec * 24))
    while f % 17 != 5: f += 1
    return f

def stream(m, level="block_level"):
    kw = {"num_blocks_per_group": 1} if level == "block_level" else {}
    apply_group_offloading(m, onload_device=dev, offload_type=level, use_stream=True, low_cpu_mem_usage=True, **kw)

def img(j):
    return ImageOps.exif_transpose(Image.open(j["image"])).convert("RGB") if j.get("image") else None

t0 = time.time()
need = [j for j in jobs if not os.path.exists(f"{OUT}/{j['id']}.enc.pt")]
cond = None
if need:
    cond = MiniMaxH3ConditionerBlocks().init_pipeline(REPO)
    cond.load_components(dtype=torch.bfloat16)
    cond.text_encoder.to(dev)
enc = {}
for j in jobs:
    h, w = j.get("canvas", [960, 544])
    if os.path.exists(f"{OUT}/{j['id']}.enc.pt"):
        enc[j["id"]] = torch.load(f"{OUT}/{j['id']}.enc.pt"); continue
    st = cond(prompt=j["prompt"], image=img(j), height=h, width=w, num_frames=frames(j.get("seconds", 5)))
    enc[j["id"]] = {"prompt_embeds": st.get("prompt_embeds").cpu(), "text_token_tags": st.get("text_token_tags"),
                    "height": st.get("height") or h, "width": st.get("width") or w,
                    "num_frames": frames(j.get("seconds", 5))}
    torch.save(enc[j["id"]], f"{OUT}/{j['id']}.enc.pt")
    print(f"[h3] encoded {j['id']} {tuple(enc[j['id']]['prompt_embeds'].shape)}", flush=True)
cond = st = None; gc.collect(); torch.cuda.empty_cache()
print(f"[h3] phase 1 done {time.time()-t0:.0f}s", flush=True)

import h3_lora
gen = MiniMaxH3GeneratorBlocks().init_pipeline(REPO)
gen.load_components(dtype=torch.bfloat16)
print("[h3]", h3_lora.apply_lora(gen.transformer), flush=True)
gen.transformer.to(dev)
gen.vae.to(dev); gen.audio_vae.to(dev)
print(f"[h3] generator on GPU {torch.cuda.memory_allocated(0)/2**30:.1f} GiB", flush=True)
for j in jobs:
    e = enc[j["id"]]; s = time.time()
    st = gen(prompt_embeds=e["prompt_embeds"].to(dev), text_token_tags=e["text_token_tags"], image=img(j),
             height=e["height"], width=e["width"], num_frames=e["num_frames"],
             num_inference_steps=j.get("steps", 6),
             generator=torch.Generator("cpu").manual_seed(j.get("seed", 42)))
    p = f"{OUT}/{j['id']}.mp4"
    encode_video(st.get("videos")[0], fps=24, output_path=p,
                 audio=st.get("audio")[0].cpu(), audio_sample_rate=st.get("sampling_rate"))
    print(f"[h3] {j['id']} {e['num_frames']} frames in {time.time()-s:.0f}s -> {p}", flush=True)
print("[h3] ALL DONE", flush=True)
