#!/usr/bin/env python3
"""Complete v8 pipeline: all 12 shots from scratch (glasses story).
Step 1: Flux 2-Klein txt2img for 12 source images
Step 2: Wan 2.2 smoothMix I2V for 12 shots
Step 3: Download + merge + NAS upload
"""
import json, subprocess, time, urllib.request, os

SSH_HOST = "liuyi@192.168.178.104"
COMFY_HOST = "192.168.178.104"
SRC = "/home/pi5/ai_cartoon/happy_children/05-source"
VID = "/home/pi5/ai_cartoon/happy_children/06-video"
FINAL = "/home/pi5/ai_cartoon/happy_children/07-final"
os.makedirs(SRC, exist_ok=True)
os.makedirs(VID, exist_ok=True)
os.makedirs(FINAL, exist_ok=True)

# ============================================================
# FLUX WORKFLOW TEMPLATE
# ============================================================
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
        "blurred, low quality, bad anatomy, distorted face, extra limbs, bad hands, "
        "watermark, text, static pose, motionless, ugly, deformed"
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

# ============================================================
# SHOT DEFINITIONS
# ============================================================
flux_shots = {
    "01": ("ep01_shot01_v8", (
        "Pixar-style 3D animation, exterior suburban house, front door swinging OPEN outward, "
        "a young boy with short dark hair wearing bright red hoodie and red backpack "
        "RUNNING OUT through the doorway toward the street, stepping OUTSIDE onto porch, "
        "door is behind him, he is EXITING the house, sunny morning, warm golden light, "
        "blue sky with birds, green lawn, cheerful expression, NO other people, NO women"
    )),
    "02": ("ep01_shot02_v8", (
        "Pixar-style 3D animation, medium shot, young boy with short dark hair in bright red hoodie "
        "and red backpack, happily skipping along suburban sidewalk, trees and houses in background, "
        "bouncing backpack, warm morning sunlight, cheerful smile, solo boy, NO other people, NO women"
    )),
    "03": ("ep01_shot03_v8", (
        "Pixar-style 3D animation, wide shot, street corner sidewalk, "
        "elderly Asian woman with glasses SITTING IN HER WHEELCHAIR, "
        "her EYEGLASSES have fallen on the ground beside the wheelchair, "
        "she is leaning forward from her wheelchair reaching her hand down toward the glasses "
        "but cannot reach them, the glasses are clearly visible on the pavement, "
        "gentle morning light, suburban street, "
        "IMPORTANT: grandma is IN the wheelchair NOT on the ground, "
        "NO young women, NO other people, NO swimsuits"
    )),
    "04": ("ep01_shot04_v8", (
        "Pixar-style 3D animation, close-up portrait, "
        "elderly Asian woman with kind face SITTING IN WHEELCHAIR, "
        "worried helpless expression, looking down toward the ground, "
        "her EYEGLASSES clearly visible lying on the pavement in the foreground, "
        "she is reaching down but cannot reach them, "
        "warm morning light, emotional, NO other people, NO young women"
    )),
    "05": ("ep01_shot05_v8", (
        "Pixar-style 3D animation, medium shot from behind, "
        "young boy in red hoodie and backpack standing on sidewalk, "
        "head tilted slightly in curiosity, looking ahead into the distance, "
        "he sees something that makes him stop and think, "
        "warm morning light, suburban street, solo boy, NO women, NO other people"
    )),
    "06": ("ep01_shot06_v8", (
        "Pixar-style 3D animation, dynamic wide shot, "
        "young boy in red hoodie and backpack RUNNING FORWARD along sidewalk, "
        "running TOWARD the camera with determination and caring expression, "
        "in the distant background: elderly woman in wheelchair reaching for glasses on ground, "
        "suburban street, warm morning light, motion blur, "
        "NO other people, NO young women"
    )),
    "07": ("ep01_shot07_v8", (
        "Pixar-style 3D animation, close-up, "
        "young boy in red hoodie BENDING DOWN picking up a pair of eyeglasses "
        "from the pavement with both hands, "
        "elderly Asian woman in wheelchair visible behind him, "
        "caring helpful expression on boy's face, "
        "he is handing/lifting the glasses toward the grandma, "
        "warm sunlight, heartwarming, NO other people, NO young women"
    )),
    "08": ("ep01_shot08_v8", (
        "Pixar-style 3D animation, medium shot, "
        "elderly Asian woman SITTING IN WHEELCHAIR, "
        "she has just PUT ON her eyeglasses (glasses now on her face), "
        "surprised happy grateful smile, turning toward the boy beside her, "
        "sunlight on her face, emotional warm moment, "
        "NO other people, NO young women"
    )),
    "09": ("ep01_shot09_v8", (
        "Pixar-style 3D animation, wide shot, suburban street, "
        "young boy in red hoodie pushing elderly Asian woman with glasses in wheelchair "
        "along sidewalk toward a house, gentle morning light, "
        "trees and houses lining the street, caring atmosphere, "
        "NO other people, NO young women"
    )),
    "10": ("ep01_shot10_v8", (
        "Pixar-style 3D animation, close-up at house doorstep, "
        "elderly Asian woman with glasses sitting in wheelchair, "
        "reaching her hand to gently pat the head of young boy in red hoodie standing beside her, "
        "warm grateful smile, teary emotional eyes, soft golden sunlight, "
        "heartwarming moment, NO other people, NO young women"
    )),
    "11": ("ep01_shot11_v8", (
        "Pixar-style 3D animation, medium shot at house entrance, "
        "young boy in red hoodie and backpack FACING TOWARD the house doorstep, "
        "waving his hand goodbye with a big happy smile, "
        "he is looking at the elderly woman in wheelchair at the doorstep, "
        "facing her directly, cheerful farewell atmosphere, "
        "warm sunny morning, NO other people, NO young women"
    )),
    "12": ("ep01_shot12_v8", (
        "Pixar-style 3D animation, wide establishing shot, "
        "young boy in red hoodie and backpack happily skipping and running "
        "toward a colorful school building in the far distance, "
        "suburban street with trees, golden warm sunlight filling scene, "
        "birds flying, beautiful sky, heartwarming cheerful ending, "
        "NO other people, NO women"
    )),
}

# ============================================================
# STEP 1: Submit all 12 Flux jobs
# ============================================================
print("=" * 60)
print("STEP 1: Flux 2-Klein txt2img (12 shots)")
print("=" * 60)

flux_pids = {}
for sn in sorted(flux_shots.keys(), key=int):
    pfx, prompt_text = flux_shots[sn]
    
    wf = json.loads(json.dumps(flux_base))
    wf["2"]["inputs"]["text"] = prompt_text
    wf["6"]["inputs"]["seed"] = int(sn) * 1000 + 42
    wf["8"]["inputs"]["filename_prefix"] = pfx
    
    local = f"/tmp/flux_v8_s{sn}.json"
    remote = f"D:/tmp_flux_v8_s{sn}.json"
    with open(local, "w") as f:
        json.dump({"prompt": wf}, f)
    
    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
         f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)
    result = json.loads(r.stdout)
    pid = result.get("prompt_id", "?")
    errs = result.get("node_errors", {})
    flux_pids[sn] = pid
    status = "✓" if not errs else f"✗ {errs}"
    print(f"Flux {sn}: {pid[:12]}... {status}")
    time.sleep(1)

# ============================================================
# STEP 2: Wait for Flux + download
# ============================================================
print(f"\nWaiting for {len(flux_pids)} Flux jobs...")
done = set()
while len(done) < len(flux_pids):
    for sn, pid in list(flux_pids.items()):
        if sn in done:
            continue
        try:
            h = json.loads(urllib.request.urlopen(
                f"http://{COMFY_HOST}:8188/history/{pid}", timeout=10).read())
            if pid in h and h[pid].get("status", {}).get("completed"):
                ss = h[pid]["status"]["status_str"]
                done.add(sn)
                print(f"  Flux {sn}: {ss} ({len(done)}/12)")
        except:
            pass
    if len(done) < len(flux_pids):
        time.sleep(10)

# Download Flux outputs
print("\nDownloading Flux outputs...")
for sn in sorted(flux_shots.keys(), key=int):
    pfx = flux_shots[sn][0]
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        f"cmd /c \"dir /b D:\\ComfyUI_Mie_2026_V8.0\\ComfyUI\\output\\{pfx}*.png 2>nul\""],
        capture_output=True, text=True, timeout=10)
    fn = r.stdout.strip()
    if fn:
        local_path = f"{SRC}/ep01_shot{sn}_v8.png"
        subprocess.run(["scp", "-q",
            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/{fn}", local_path], check=True)
        # Also upload to ComfyUI input for Wan
        subprocess.run(["scp", "-q", local_path,
            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/ep01_shot{sn}_v8.png"], check=True)
        sz = os.path.getsize(local_path)
        print(f"  Shot {sn}: ✓ ({sz//1024}KB)")
    else:
        print(f"  Shot {sn}: ✗ NOT FOUND!")

# ============================================================
# STEP 3: Submit Wan 2.2 I2V (12 shots)
# ============================================================
print(f"\n{'='*60}")
print("STEP 3: Wan 2.2 smoothMix I2V (12 shots)")
print("=" * 60)

with open("/tmp/wan22_flat_api.json") as f:
    wan_wf = json.load(f)

wan_shots = {
    "01": (81, "Pixar, boy in red hoodie RUNNING OUT of house front door toward street, door open behind, sunny morning, birds, 16fps"),
    "02": (65, "Pixar, boy in red hoodie happily skipping on sidewalk, backpack bouncing, trees, warm light, 16fps"),
    "03": (81, "Pixar, elderly woman SITTING IN wheelchair reaching for eyeglasses on ground, gentle movement, street corner, morning, 16fps"),
    "04": (49, "Pixar, close-up elderly woman in wheelchair, worried face, eyeglasses visible on ground, subtle emotion, 16fps"),
    "05": (49, "Pixar, boy in red hoodie standing on sidewalk, head tilting curiously, looking ahead, subtle movement, 16fps"),
    "06": (49, "Pixar, boy in red hoodie RUNNING FORWARD toward camera along sidewalk, determined caring face, motion, 16fps"),
    "07": (65, "Pixar, boy in red hoodie bending down picking up eyeglasses from ground, handing to elderly woman in wheelchair, 16fps"),
    "08": (65, "Pixar, elderly woman in wheelchair putting on glasses, surprised happy grateful smile, emotional, 16fps"),
    "09": (97, "Pixar, boy in red hoodie pushing elderly woman in wheelchair along suburban street toward house, gentle light, 16fps"),
    "10": (65, "Pixar, elderly woman in wheelchair at doorstep patting boy's head, warm grateful smile, soft sunlight, 16fps"),
    "11": (65, "Pixar, boy in red hoodie FACING house doorstep waving goodbye to grandma in wheelchair, cheerful smile, 16fps"),
    "12": (97, "Pixar, boy in red hoodie happily running toward colorful school in distance, golden sunlight, birds, 16fps"),
}

NEG_EXTRA = ", no woman, no girl, no female, no swimsuit, no bikini, no young woman, no lady"

wan_pids = {}
for sn in sorted(wan_shots.keys(), key=int):
    frames, pos = wan_shots[sn]
    img = f"ep01_shot{sn}_v8.png"
    
    prompt = json.loads(json.dumps(wan_wf["prompt"]))
    prompt["37"]["inputs"]["image"] = img
    prompt["36"]["inputs"]["text"] = pos
    prompt["36"]["inputs"]["value"] = str(frames)
    prompt["17"]["inputs"]["value"] = str(frames)
    prompt["33"]["inputs"]["text"] = prompt["33"]["inputs"]["text"] + NEG_EXTRA
    prompt["24"]["inputs"]["value"] = "a+1"
    
    local = f"/tmp/wan_v8_s{sn}.json"
    remote = f"D:/tmp_wan_v8_s{sn}.json"
    with open(local, "w") as f:
        json.dump({"prompt": prompt}, f)
    
    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
         f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)
    result = json.loads(r.stdout)
    pid = result.get("prompt_id", "?")
    errs = result.get("node_errors", {})
    wan_pids[sn] = pid
    status = "✓" if not errs else f"✗ {errs}"
    print(f"Wan {sn}: {pid[:12]}... {status} ({frames}f)")
    time.sleep(1)

print(f"\n{len(wan_pids)} Wan jobs submitted. PIDs saved.")
with open(f"{VID}/wan_v8_pids.json", "w") as f:
    json.dump(wan_pids, f)

print("\nPipeline submitted. Monitor will auto-download + merge + upload.")
print("Run: bash scripts/monitor_v8.sh")
