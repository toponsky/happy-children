#!/usr/bin/env python3
"""Flux.2-Klein batch txt2img: regenerate 8 source images for Happy Children ep01."""
import json, urllib.request, time, subprocess, os

COMFY_HOST = "192.168.178.104"
SSH_HOST = "liuyi@192.168.178.104"
OUTDIR = "/home/pi5/ai_cartoon/happy_children/05-source"
os.makedirs(OUTDIR, exist_ok=True)

# --- Workflow template ---
WF = {
    "1": {"class_type": "FluxLoader", "inputs": {
        "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
        "weight_dtype": "default",
        "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
        "clip_name2_opt": ".none",
        "vae_name": "Flux\\flux2-vae.safetensors",
        "clip_vision_name": ".none",
        "style_model_name": ".none"
    }},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "PLACEHOLDER_POS", "clip": ["1", 1]}},
    "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "PLACEHOLDER_NEG", "clip": ["1", 1]}},
    "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 1664, "batch_size": 1}},
    "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": 3.5}},
    "6": {"class_type": "KSampler", "inputs": {
        "seed": 42, "steps": 28, "cfg": 1.0,
        "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["5", 0],
        "negative": ["3", 0], "latent_image": ["4", 0]
    }},
    "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
    "8": {"class_type": "SaveImage", "inputs": {"filename_prefix": "PLACEHOLDER_PREFIX", "images": ["7", 0]}}
}

NEG = ("no woman, no girl, no female, no swimsuit, no bikini, no young woman, "
       "no adult woman, no lady, no female character, deformed face, bad anatomy, "
       "blurry, low quality, watermark, text")

# --- Shot definitions ---
shots = [
    (1, "ep01_shot01_v6",
     "Pixar-style 3D animation, sunny morning suburban neighborhood with green lawns and trees, "
     "a young boy with short dark hair wearing a bright red hoodie and carrying a red backpack "
     "running out of a colorful house front door, warm golden sunlight, birds in sky, "
     "cheerful happy atmosphere, clear blue sky, no people other than the boy"),

    (2, "ep01_shot02_v6",
     "Pixar-style 3D animation, medium shot of a young boy with short dark hair in bright red hoodie "
     "and red backpack, happily skipping along a suburban sidewalk, trees and houses in background, "
     "warm morning sunlight, cheerful expression, bouncing backpack, no other people"),

    (5, "ep01_shot05_v6",
     "Pixar-style 3D animation, medium shot of a young boy with short dark hair in bright red hoodie "
     "and red backpack, standing on a sidewalk, head tilted slightly in curiosity, thoughtful expression, "
     "looking at something in the distance, suburban street background, warm morning light, solo character"),

    (6, "ep01_shot06_v6",
     "Pixar-style 3D animation, wide shot of a young boy with short dark hair in bright red hoodie "
     "running with determination toward the camera, suburban street background, "
     "an elderly Asian woman with glasses fallen on the ground in the distance, empty wheelchair tipped nearby, "
     "concerned caring expression on the boy's face, warm morning light, NO young women"),

    (9, "ep01_shot09_v6",
     "Pixar-style 3D animation, wide shot suburban street, a young boy with short dark hair in bright red hoodie "
     "pushing an elderly Asian woman with glasses sitting in a wheelchair along the sidewalk toward a house, "
     "gentle morning light, trees and houses lining the street, caring atmosphere, "
     "NO other people, NO young women"),

    (10, "ep01_shot10_v6",
     "Pixar-style 3D animation, close-up shot at a house doorstep, an elderly Asian woman with glasses "
     "sitting in a wheelchair, reaching her hand to gently pat the head of a young boy with short dark hair "
     "in a red hoodie standing beside her, warm grateful smile on the elderly woman's face, "
     "teary emotional eyes, soft golden sunlight, heartwarming moment, NO other people"),

    (11, "ep01_shot11_v6",
     "Pixar-style 3D animation, medium shot at a house entrance, a young boy with short dark hair "
     "in bright red hoodie and red backpack, waving goodbye with a big happy smile, "
     "elderly Asian woman with glasses in wheelchair visible in background at doorstep, "
     "warm sunny morning, cheerful farewell atmosphere, solo waving boy in foreground"),

    (12, "ep01_shot12_v6",
     "Pixar-style 3D animation, wide establishing shot, a young boy with short dark hair in bright red hoodie "
     "and red backpack, happily skipping and running toward a colorful school building in the far distance, "
     "suburban street with trees, golden warm sunlight filling the entire scene, "
     "heartwarming cheerful ending atmosphere, birds flying, beautiful sky, NO other people, NO women"),
]

# --- Submit all shots ---
pids = {}
for sn, prefix, prompt_text in shots:
    prompt = json.loads(json.dumps(WF))
    prompt["2"]["inputs"]["text"] = prompt_text
    prompt["3"]["inputs"]["text"] = NEG
    prompt["6"]["inputs"]["seed"] = sn * 1000 + 42
    prompt["8"]["inputs"]["filename_prefix"] = prefix

    payload = json.dumps({"prompt": prompt})
    local = f"/tmp/flux_s{sn:02d}.json"
    remote = f"D:/tmp_flux_s{sn:02d}.json"

    with open(local, "w") as f:
        f.write(payload)

    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
         f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)

    result = json.loads(r.stdout)
    pid = result.get("prompt_id", "?")
    errs = result.get("node_errors", {})
    status = "✗ ERR" if any(errs) else "✓"
    pids[sn] = pid
    print(f"Shot {sn:02d}: {pid[:12]}... {status}")
    if errs:
        print(f"  Errors: {errs}")
    time.sleep(2)

print(f"\nSubmitted {len(pids)} shots. PIDs: {pids}")
# Save PIDs for monitor
with open(f"{OUTDIR}/flux_pids.json", "w") as f:
    json.dump(pids, f)
print("PIDs saved. Run monitor script next.")
