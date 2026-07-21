#!/usr/bin/env python3
"""Regenerate shot 01 only: Michael running OUT of house, not into it."""
import json, subprocess, time, os

SSH_HOST = "liuyi@192.168.178.104"
COMFY_HOST = "192.168.178.104"
OUT_SRC = "/home/pi5/ai_cartoon/happy_children/05-source"
OUT_VID = "/home/pi5/ai_cartoon/happy_children/06-video"

# ==== STEP 1: Flux txt2img for corrected shot 01 ====
print("=== STEP 1: Flux 2-Klein txt2img ===")

flux_wf = {
    "1": {"class_type": "FluxLoader", "inputs": {
        "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
        "weight_dtype": "default",
        "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
        "clip_name2_opt": ".none",
        "vae_name": "Flux\\flux2-vae.safetensors",
        "clip_vision_name": ".none",
        "style_model_name": ".none"
    }},
    "2": {"class_type": "CLIPTextEncode", "inputs": {
        "text": (
            "Pixar-style 3D animation, exterior view of a colorful suburban house front door "
            "swinging OPEN outward, a young boy with short dark hair wearing a bright red hoodie "
            "and carrying a red backpack is RUNNING OUT through the doorway toward the camera, "
            "stepping OUTSIDE onto the front porch, his back is to the house interior, "
            "he is EXITING the house heading to the street, sunny morning, warm golden sunlight, "
            "blue sky with birds, green lawn, cheerful happy expression on the boy's face, "
            "the door is behind him, he is moving FORWARD out of the house, "
            "NO other people, NO women, NO girls"
        ),
        "clip": ["1", 1]
    }},
    "3": {"class_type": "CLIPTextEncode", "inputs": {
        "text": ("no woman, no girl, no female, no swimsuit, no bikini, no adult woman, "
                 "no lady, no feminine figure, blurred, low quality, bad anatomy, deformed face, "
                 "watermark, text, distorted, ugly, extra limbs, missing limbs, bad hands, "
                 "boy walking into house, boy entering door, back to camera, door closing, "
                 "static pose, motionless"),
        "clip": ["1", 1]
    }},
    "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 1664, "batch_size": 1}},
    "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": 3.5}},
    "6": {"class_type": "KSampler", "inputs": {
        "seed": 42, "steps": 28, "cfg": 1.0,
        "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["5", 0],
        "negative": ["3", 0], "latent_image": ["4", 0]
    }},
    "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
    "8": {"class_type": "SaveImage", "inputs": {"filename_prefix": "ep01_shot01_v7b", "images": ["7", 0]}}
}

payload = json.dumps({"prompt": flux_wf})
with open("/tmp/flux_s01_v7b.json", "w") as f:
    f.write(payload)

subprocess.run(["scp", "-q", "/tmp/flux_s01_v7b.json",
    f"{SSH_HOST}:D:/tmp_flux_s01_v7b.json"], check=True)
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
     "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @D:/tmp_flux_s01_v7b.json"],
    capture_output=True, text=True, timeout=15)
result = json.loads(r.stdout)
flux_pid = result.get("prompt_id", "?")
print(f"Flux: {flux_pid}")

# Wait for Flux
import urllib.request
while True:
    try:
        h = json.loads(urllib.request.urlopen(f"http://{COMFY_HOST}:8188/history/{flux_pid}", timeout=10).read())
        if flux_pid in h and h[flux_pid].get("status", {}).get("completed"):
            print(f"Flux done: {h[flux_pid]['status']['status_str']}")
            break
    except:
        pass
    time.sleep(5)

# Download
r2 = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
     "cmd /c \"dir /b D:\\ComfyUI_Mie_2026_V8.0\\ComfyUI\\output\\ep01_shot01_v7b*.png 2>nul\""],
    capture_output=True, text=True, timeout=10)
flux_fn = r2.stdout.strip()
if flux_fn:
    subprocess.run(["scp", "-q",
        f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/{flux_fn}",
        f"{OUT_SRC}/ep01_shot01_v7b.png"], check=True)
    print(f"Flux output: {flux_fn}")
else:
    print("ERROR: Flux output not found")
    exit(1)

# ==== STEP 2: Wan 2.2 I2V ====
print("\n=== STEP 2: Wan 2.2 I2V ===")

with open("/tmp/wan22_flat_api.json") as f:
    wan_wf = json.load(f)

prompt = json.loads(json.dumps(wan_wf["prompt"]))
prompt["37"]["inputs"]["image"] = "ep01_shot01_v7b.png"
prompt["36"]["inputs"]["text"] = (
    "Pixar animation, exterior shot, young boy in red hoodie with red backpack "
    "RUNNING OUT of house front door toward street, door swinging open behind him, "
    "he is EXITING the house, moving forward out of doorway onto porch, "
    "sunny morning, birds, warm golden light, smooth motion, no women, no female, 16fps"
)
prompt["36"]["inputs"]["value"] = "81"
prompt["17"]["inputs"]["value"] = "81"
prompt["33"]["inputs"]["text"] = prompt["33"]["inputs"]["text"] + (
    ", no woman, no girl, no female, no swimsuit, no bikini, "
    "boy walking INTO house, boy entering door, backward motion"
)
prompt["24"]["inputs"]["value"] = "a+1"

# Upload image
subprocess.run(["scp", "-q",
    f"{OUT_SRC}/ep01_shot01_v7b.png",
    f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/ep01_shot01_v7b.png"], check=True)

payload = json.dumps({"prompt": prompt})
with open("/tmp/wan_s01_v7b.json", "w") as f:
    f.write(payload)
subprocess.run(["scp", "-q", "/tmp/wan_s01_v7b.json",
    f"{SSH_HOST}:D:/tmp_wan_s01_v7b.json"], check=True)
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
     "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @D:/tmp_wan_s01_v7b.json"],
    capture_output=True, text=True, timeout=15)
wan_result = json.loads(r.stdout)
wan_pid = wan_result.get("prompt_id", "?")
errs = wan_result.get("node_errors", {})
print(f"Wan: {wan_pid} {'✓' if not errs else f'✗ {errs}'}")

# Wait for Wan
while True:
    try:
        h = json.loads(urllib.request.urlopen(f"http://{COMFY_HOST}:8188/history/{wan_pid}", timeout=10).read())
        if wan_pid in h and h[wan_pid].get("status", {}).get("completed"):
            ss = h[wan_pid]["status"]["status_str"]
            print(f"Wan done: {ss}")
            if ss == "success":
                for n, o in h[wan_pid].get("outputs", {}).items():
                    for g in o.get("gifs", []):
                        fn = g["filename"]
                        print(f"Output: {fn}")
                        subprocess.run(["scp", "-q",
                            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/{fn}",
                            f"{OUT_VID}/ep01_shot01_v7b.mp4"], check=True)
                        print(f"Downloaded → {OUT_VID}/ep01_shot01_v7b.mp4")
            break
    except:
        pass
    time.sleep(10)

print("\nDone! Shot 01 regenerated: ep01_shot01_v7b.mp4")
print("Now re-merge to create ep01_v7b.mp4")
