#!/usr/bin/env python3
"""Fix shots 06 (direction) and 08 (clothing color) - Flux only, submit for review."""
import json, subprocess, time, urllib.request, os

SSH_HOST = "liuyi@192.168.178.104"
COMFY_HOST = "192.168.178.104"
SRC = "/home/pi5/ai_cartoon/happy_children/05-source"

flux_base = {
    "1": {"class_type": "FluxLoader", "inputs": {
        "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
        "weight_dtype": "default",
        "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
        "clip_name2_opt": ".none",
        "vae_name": "Flux\\flux2-vae.safetensors",
        "clip_vision_name": ".none", "style_model_name": ".none"
    }},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["1", 1]}},
    "3": {"class_type": "CLIPTextEncode", "inputs": {"text": (
        "no woman, no girl, no female, no swimsuit, no bikini, no feminine figure, "
        "white hoodie, white sweater, white jacket, white clothing on boy, "
        "boy running away, boy facing away, back to camera, "
        "blurred, low quality, bad anatomy, distorted, watermark, static pose"
    ), "clip": ["1", 1]}},
    "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 1664, "batch_size": 1}},
    "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": 3.5}},
    "6": {"class_type": "KSampler", "inputs": {
        "seed": 42, "steps": 28, "cfg": 1.0,
        "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["5", 0],
        "negative": ["3", 0], "latent_image": ["4", 0]
    }},
    "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
    "8": {"class_type": "SaveImage", "inputs": {"filename_prefix": "", "images": ["7", 0]}}
}

shots = {
    "06": ("ep01_shot06_v9",
        "Pixar-style 3D animation, dynamic wide shot, "
        "a young boy with short dark hair wearing a BRIGHT RED HOODIE and RED BACKPACK, "
        "RUNNING DIRECTLY TOWARD THE CAMERA with determination and caring expression, "
        "running FORWARD along a suburban sidewalk, trees in background, "
        "in the DISTANT BACKGROUND behind him (small, far away): "
        "an elderly Asian woman SITTING IN A WHEELCHAIR reaching for glasses on the ground, "
        "he is running TO HER, toward the viewer, motion blur on legs, "
        "warm morning light, RED hoodie clearly visible, "
        "NO other people, NO young women, NO girls, NOT running away"
    ),
    "08": ("ep01_shot08_v9",
        "Pixar-style 3D animation, medium shot, "
        "an elderly Asian woman SITTING IN A WHEELCHAIR, "
        "she has just PUT ON her eyeglasses (glasses now on her face), "
        "surprised happy grateful warm smile, looking slightly to her side, "
        "sunlight on her face, emotional warm moment, "
        "ONLY the grandmother in frame, NO boy, NO Michael, NO other characters, "
        "NO young women, NO girls, NO swimsuits, NO children"
    ),
}

print("Submitting Flux fixes...")
for sn, (pfx, prompt_text) in sorted(shots.items()):
    wf = json.loads(json.dumps(flux_base))
    wf["2"]["inputs"]["text"] = prompt_text
    wf["6"]["inputs"]["seed"] = int(sn) * 2000 + 99
    wf["8"]["inputs"]["filename_prefix"] = pfx
    
    local = f"/tmp/flux_v9_s{sn}.json"
    remote = f"D:/tmp_flux_v9_s{sn}.json"
    with open(local, "w") as f:
        json.dump({"prompt": wf}, f)
    
    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
         f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)
    result = json.loads(r.stdout)
    pid = result.get("prompt_id", "?")
    print(f"Flux {sn}: {pid[:12]}...")

# Wait
print("Waiting...")
for sn in sorted(shots.keys()):
    while True:
        try:
            h = json.loads(urllib.request.urlopen(f"http://{COMFY_HOST}:8188/history", timeout=10).read())
            for pid, e in h.items():
                out_files = []
                for n, o in e.get("outputs", {}).items():
                    for g in o.get("images", []):
                        out_files.append(g.get("filename", ""))
                prefix = shots[sn][0]
                for fn in out_files:
                    if fn.startswith(prefix):
                        ss = e["status"]["status_str"]
                        print(f"  Shot {sn}: {ss} → {fn}")
                        # Download
                        subprocess.run(["scp", "-q",
                            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/{fn}",
                            f"{SRC}/ep01_shot{sn}_v9.png"], check=True)
                        break
                else:
                    continue
                break
            else:
                time.sleep(5)
                continue
            break
        except:
            time.sleep(5)

# Resize and report
print("\nDone. Resizing...")
for sn in sorted(shots.keys()):
    subprocess.run(["ffmpeg", "-y", "-i", f"{SRC}/ep01_shot{sn}_v9.png",
        "-vf", "scale=640:832", "-q:v", "3", f"{SRC}/ep01_shot{sn}_v9_sm.jpg"],
        capture_output=True, stderr=subprocess.DEVNULL)
    print(f"Shot {sn}: {SRC}/ep01_shot{sn}_v9_sm.jpg")

print("\nReady for review.")
