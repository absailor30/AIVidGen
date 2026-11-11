"""Test: image -> video with Wan 2.2 I2V 14B + Lightning LoRA (4 steps) on the WanGP pod.
Usage: python wan22_i2v_test.py IMAGE.jpg "prompt" [out.mp4]
Needs fr_lib.py (WanGP MCP helpers) + mcp.py pointing at the running pod. UNTESTED: model_type/profile names
are guesses (MODEL env overrides); the script prints the available profiles so you can fix them."""
import sys, os, json
sys.path.insert(0, os.environ.get("FR_DIR", "."))
import fr_lib as fr
img, prompt = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else "wan22_test.mp4"
MODEL = os.environ.get("MODEL", "i2v_2_2")
fr.mcp.call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'claude', 'version': '1'}})
base = json.loads(fr.mcp.tool('wangp_model', {'model_type': MODEL, 'action': 'defaults', 'arguments': {}}))
prof = json.loads(fr.mcp.tool('wangp_model', {'model_type': MODEL, 'action': 'profiles', 'arguments': {}}))
print("profiles:", json.dumps(prof)[:1500])          # pick the Lightning / 4-steps one from this list
PROFILE = os.environ.get("PROFILE")                   # e.g. 'accelerator_profile:wan_i2v/Image2Video lightx2v - 4 Steps.json'
if PROFILE:
    base.update(json.loads(fr.mcp.tool('wangp_model', {'model_type': MODEL, 'action': 'profiles',
                'arguments': {'setting_id': PROFILE}}))['content'])
s = dict(base, model_type=MODEL, prompt=prompt, image_start=fr.up(img, os.path.basename(img)),
         image_prompt_type='S', resolution=os.environ.get("RES", "480x854"),
         video_length=int(os.environ.get("FRAMES", "81")),   # 81 frames ~ 5 s at 16 fps
         num_inference_steps=4, seed=7, output_filename="wan22_test")
print(fr.mcp.tool('wangp_validate', {'settings': [s]})[:800])
for it in fr.run([s], "wan22"):
    if it.get('role') == 'intermediate': continue
    fr.fetch(it['media_id'], out); print("saved", out)
