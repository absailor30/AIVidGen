"""Qwen-Image-Edit-2509 + Lightning 8-step LoRA on one 48 GB GPU with a 50 GB RAM cap.
Phase 1: text encoder (Qwen2.5-VL) on GPU encodes every job (prompt + two images), then freed.
Phase 2: transformer + VAE on GPU denoise each job."""
import gc, json, glob, os, sys, time, torch
from PIL import Image
from diffusers import QwenImageEditPlusPipeline, QwenImageTransformer2DModel, AutoencoderKLQwenImage
from transformers import Qwen2_5_VLForConditionalGeneration
from diffusers.pipelines.qwenimage.pipeline_qwenimage_edit_plus import calculate_dimensions, CONDITION_IMAGE_SIZE
M="/workspace/q/model"; dev="cuda"
jobs=json.load(open(sys.argv[1])); os.makedirs("/workspace/q/out",exist_ok=True)
imgs=lambda j:[Image.open(f"/workspace/q/cast/{n}.jpg").convert("RGB") for n in j["images"]]
t=time.time()
te=Qwen2_5_VLForConditionalGeneration.from_pretrained(f"{M}/text_encoder",torch_dtype=torch.bfloat16,device_map=dev)
pipe=QwenImageEditPlusPipeline.from_pretrained(M,transformer=None,vae=None,text_encoder=te,torch_dtype=torch.bfloat16)
enc={}
with torch.no_grad():
    for j in jobs:
        cond=[]
        for im in imgs(j):
            w,h=calculate_dimensions(CONDITION_IMAGE_SIZE, im.width/im.height)
            cond.append(pipe.image_processor.resize(im,h,w))
        pe,pm=pipe.encode_prompt(image=cond,prompt=j["prompt"],device=dev)
        ne,nm=pipe.encode_prompt(image=cond,prompt=" ",device=dev)
        enc[j["id"]]=(pe.cpu(),pm.cpu() if pm is not None else None,ne.cpu(),nm.cpu() if nm is not None else None)
        print("[q] encoded",j["id"],flush=True)
sched=pipe.scheduler; proc=pipe.processor; tok=pipe.tokenizer
del pipe,te; gc.collect(); torch.cuda.empty_cache()
print(f"[q] phase 1 {time.time()-t:.0f}s",flush=True)
tr=QwenImageTransformer2DModel.from_pretrained(f"{M}/transformer",torch_dtype=torch.bfloat16,device_map=dev)
vae=AutoencoderKLQwenImage.from_pretrained(f"{M}/vae",torch_dtype=torch.bfloat16).to(dev)
pipe=QwenImageEditPlusPipeline(transformer=tr,vae=vae,text_encoder=None,tokenizer=tok,processor=proc,scheduler=sched)
lora=glob.glob("/workspace/q/lora/**/*.safetensors",recursive=True)
if lora:
    pipe.load_lora_weights(lora[0]); pipe.fuse_lora(); print("[q] lora",os.path.basename(lora[0]),flush=True)
steps=8 if lora else 30
for j in jobs:
    pe,pm,ne,nm=enc[j["id"]]; s=time.time()
    out=pipe(image=imgs(j),prompt_embeds=pe.to(dev),prompt_embeds_mask=None if pm is None else pm.to(dev),
             negative_prompt_embeds=ne.to(dev),negative_prompt_embeds_mask=None if nm is None else nm.to(dev),
             true_cfg_scale=1.0 if lora else 4.0,num_inference_steps=steps,height=1344,width=768,
             generator=torch.Generator(dev).manual_seed(j.get("seed",7))).images[0]
    out.save(f"/workspace/q/out/{j['id']}.png"); print(f"[q] {j['id']} {time.time()-s:.0f}s",flush=True)
print("[q] ALL DONE",flush=True)
