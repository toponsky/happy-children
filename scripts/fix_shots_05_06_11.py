#!/usr/bin/env python3
"""Fix shots 05 (facing grandma), 06 (running TOWARD grandma), 11 (facing grandma goodbye)."""
import json, subprocess, time, urllib.request

SSH_HOST = "liuyi@192.168.178.104"
COMFY_HOST = "192.168.178.104"
SRC = "/home/pi5/ai_cartoon/happy_children/05-source"
VID = "/home/pi5/ai_cartoon/happy_children/06-video"

# ===== STEP 1: Flux txt2img for 3 shots =====
print("=== STEP 1: Flux 2-Klein txt2img (shots 05, 06, 11) ===")

flux_template = {
    "1": {"class_type": "FluxLoader", "inputs": {
        "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
        "weight_dtype": "default",
        "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
        "clip_name2_opt": ".none",
        "vae_name": "Flux\\flux2-vae.safetensors",
        "clip_vision_name": ".none", "style_model_name": ".none"
    }},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "PLACEHOLDER", "clip": ["1", 1]}},
    "3": {"class_type": "CLIPTextEncode", "inputs": {"text": (
        "no woman, no girl, no female, no swimsuit, no bikini, no feminine figure, "
        "blurred, low quality, bad anatomy, deformed, watermark, static pose"
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
    "8": {"class_type": "SaveImage", "inputs": {"filename_prefix": "PLACEHOLDER_PFX", "images": ["7", 0]}}
}

flux_shots = {
    "05": {
        "pfx": "ep01_shot05_v7b",
        "prompt": (
            "Pixar-style 3D animation, medium shot from BEHIND Michael, over-the-shoulder view, "
            "a young boy with short dark hair in bright red hoodie and red backpack, "
            "standing on a suburban sidewalk FACING FORWARD, looking ahead down the street, "
            "head tilted slightly in curiosity and concern, "
            "in the DISTANCE ahead of him: an elderly Asian woman with glasses fallen on the ground "
            "beside an empty tipped wheelchair, "
            "Michael is looking AT the fallen grandmother, he has NOT started running yet, "
            "warm morning light, suburban street with trees, "
            "NO other people, NO young women, NO girls"
        )
    },
    "06": {
        "pfx": "ep01_shot06_v7b",
        "prompt": (
            "Pixar-style 3D animation, dynamic wide shot, "
            "a young boy with short dark hair in bright red hoodie and red backpack "
            "RUNNING FORWARD TOWARD the camera/viewer with determination and urgency, "
            "running ALONG a suburban street sidewalk, trees in background, "
            "in the FAR BACKGROUND behind him: an elderly Asian woman with glasses "
            "fallen on the ground beside an empty tipped wheelchair (distant, small), "
            "he is running TO her, toward the camera, concerned caring expression, "
            "warm morning light, motion blur on legs, "
            "NO other people, NO young women, NO girls"
        )
    },
    "11": {
        "pfx": "ep01_shot11_v7b",
        "prompt": (
            "Pixar-style 3D animation, medium shot at a house entrance, "
            "a young boy with short dark hair in bright red hoodie and red backpack, "
            "FACING THE HOUSE DOORSTEP, waving his hand goodbye with a big happy smile, "
            "in the FOREGROUND at the doorstep: an elderly Asian woman with glasses "
            "sitting in a wheelchair, smiling warmly back at him, "
            "the boy is looking directly at the grandmother, facing her, "
            "warm sunny morning, cheerful farewell atmosphere, "
            "NO other people, NO young women"
        )
    }
}

flux_pids = {}
for sn, cfg in flux_shots.items():
    wf = json.loads(json.dumps(flux_template))
    wf["2"]["inputs"]["text"] = cfg["prompt"]
    wf["8"]["inputs"]["filename_prefix"] = cfg["pfx"]
    
    local = f"/tmp/flux_s{sn}_v7b.json"
    remote = f"D:/tmp_flux_s{sn}_v7b.json"
    with open(local, "w") as f:
        json.dump({"prompt": wf}, f)
    
    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)
    pid = json.loads(r.stdout).get("prompt_id", "?")
    flux_pids[sn] = pid
    print(f"Flux shot {sn}: {pid}")
    time.sleep(1)

# Wait for all Flux
for sn, pid in flux_pids.items():
    while True:
        try:
            h = json.loads(urllib.request.urlopen(f"http://{COMFY_HOST}:8188/history/{pid}", timeout=10).read())
            if pid in h and h[pid].get("status", {}).get("completed"):
                print(f"Flux {sn}: {h[pid]['status']['status_str']}")
                break
        except: pass
        time.sleep(5)

# Download Flux outputs + upload to ComfyUI input
for sn, cfg in flux_shots.items():
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        f"cmd /c \"dir /b D:\\ComfyUI_Mie_2026_V8.0\\ComfyUI\\output\\{cfg['pfx']}*.png 2>nul\""],
        capture_output=True, text=True, timeout=10)
    fn = r.stdout.strip()
    if fn:
        local_path = f"{SRC}/ep01_shot{sn}_v7b.png"
        subprocess.run(["scp", "-q",
            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/{fn}", local_path], check=True)
        subprocess.run(["scp", "-q", local_path,
            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/ep01_shot{sn}_v7b.png"], check=True)
        print(f"Flux {sn} downloaded: {fn}")

# ===== STEP 2: Wan 2.2 I2V =====
print("\n=== STEP 2: Wan 2.2 I2V ===")
with open("/tmp/wan22_flat_api.json") as f:
    wan_wf = json.load(f)

wan_shots = {
    "05": (49, "Pixar animation, medium shot from behind boy, young boy in red hoodie standing on sidewalk "
              "looking forward at fallen elderly woman in distance, head tilting, subtle movement, "
              "he is facing TOWARD the grandmother, NOT away, no women, 16fps"),
    "06": (49, "Pixar animation, young boy in red hoodie RUNNING FORWARD toward camera along sidewalk, "
              "determined expression, elderly woman fallen on ground visible far behind him, "
              "he is running TOWARD her, NOT away, suburban street, motion, no women, 16fps"),
    "11": (65, "Pixar animation, young boy in red hoodie FACING toward house doorstep, waving goodbye "
              "to elderly woman in wheelchair at the door, big happy smile, he is looking at her, "
              "facing the grandmother, NOT facing away, cheerful farewell, 16fps"),
}

NEG_EXTRA = (", no woman, no girl, no female, no swimsuit, no bikini, "
             "boy turning away, boy walking away, boy facing away from grandma, boy running away")

wan_pids = {}
for sn in ["05", "06", "11"]:
    frames, pos = wan_shots[sn]
    img = f"ep01_shot{sn}_v7b.png"
    
    prompt = json.loads(json.dumps(wan_wf["prompt"]))
    prompt["37"]["inputs"]["image"] = img
    prompt["36"]["inputs"]["text"] = pos
    prompt["36"]["inputs"]["value"] = str(frames)
    prompt["17"]["inputs"]["value"] = str(frames)
    prompt["33"]["inputs"]["text"] = prompt["33"]["inputs"]["text"] + NEG_EXTRA
    prompt["24"]["inputs"]["value"] = "a+1"
    
    local = f"/tmp/wan_s{sn}_v7b.json"
    remote = f"D:/tmp_wan_s{sn}_v7b.json"
    with open(local, "w") as f:
        json.dump({"prompt": prompt}, f)
    
    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)
    result = json.loads(r.stdout)
    pid = result.get("prompt_id", "?")
    errs = result.get("node_errors", {})
    wan_pids[sn] = pid
    print(f"Wan shot {sn}: {pid} {'✓' if not errs else f'✗ {errs}'}")
    time.sleep(1)

print(f"\nSubmitted {len(wan_pids)} Wan jobs. PIDs: {wan_pids}")
print("Will auto-download when complete. Then merge v7b.")
