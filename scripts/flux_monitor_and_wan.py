#!/usr/bin/env python3
"""Monitor Flux.2-Klein batch, download outputs, then submit Wan 2.2 I2V for v7."""
import json, urllib.request, time, subprocess, os, sys

COMFY_HOST = "192.168.178.104"
SSH_HOST = "liuyi@192.168.178.104"
OUT_SOURCE = "/home/pi5/ai_cartoon/happy_children/05-source"
OUT_VIDEO = "/home/pi5/ai_cartoon/happy_children/06-video"
OUT_FINAL = "/home/pi5/ai_cartoon/happy_children/07-final"
os.makedirs(OUT_SOURCE, exist_ok=True)
os.makedirs(OUT_VIDEO, exist_ok=True)
os.makedirs(OUT_FINAL, exist_ok=True)

# Load PIDs from step 1
with open(f"{OUT_SOURCE}/flux_pids.json") as f:
    pids = json.load(f)

# Shot definitions for Wan 2.2
shots_config = {
    1:  {"frames": 81,  "prompt": "Pixar animation, young boy in red hoodie with red backpack running out of house front door, sunny morning suburban neighborhood, birds flying, warm golden sunlight, smooth motion, 16fps"},
    2:  {"frames": 65,  "prompt": "Pixar animation, young boy in red hoodie happily skipping on sidewalk, backpack bouncing, trees in background, warm morning light, cheerful expression, smooth motion, 16fps"},
    5:  {"frames": 49,  "prompt": "Pixar animation, young boy in red hoodie standing on sidewalk, head tilting curiously, thinking expression, subtle movement, warm morning light, 16fps"},
    6:  {"frames": 49,  "prompt": "Pixar animation, young boy in red hoodie running toward fallen elderly woman, determined caring face, suburban street, smooth motion, 16fps"},
    9:  {"frames": 97,  "prompt": "Pixar animation, young boy in red hoodie pushing elderly woman in wheelchair along suburban street toward house, gentle morning light, smooth motion, 16fps"},
    10: {"frames": 65,  "prompt": "Pixar animation, elderly woman in wheelchair at doorstep, reaching hand to gently pat young boy's head, warm grateful smile, teary eyes, subtle motion, 16fps"},
    11: {"frames": 65,  "prompt": "Pixar animation, young boy in red hoodie waving goodbye at house entrance, big happy smile, elderly woman in wheelchair visible behind, cheerful, 16fps"},
    12: {"frames": 97,  "prompt": "Pixar animation, young boy in red hoodie happily running toward colorful school building in distance, golden sunlight, birds, heartwarming ending, smooth motion, 16fps"},
}

# ===== STEP 1: Poll Flux completion =====
print("=== STEP 1: Waiting for Flux completion ===")
done = set()
while len(done) < len(pids):
    q = json.loads(urllib.request.urlopen(f"http://{COMFY_HOST}:8188/queue", timeout=5).read())
    running = [x[1] for x in q.get("queue_running", [])]
    pending = [x[1] for x in q.get("queue_pending", [])]
    
    for sn, pid in pids.items():
        if sn in done:
            continue
        if pid in running or pid in pending:
            continue
        # Check history
        try:
            h = json.loads(urllib.request.urlopen(f"http://{COMFY_HOST}:8188/history/{pid}", timeout=10).read())
            if pid in h and h[pid].get("status", {}).get("completed", False):
                status = h[pid]["status"]["status_str"]
                done.add(sn)
                print(f"  Flux shot {sn:02d}: {status} ({len(done)}/{len(pids)})")
        except:
            pass
    if len(done) < len(pids):
        time.sleep(15)
print(f"All {len(done)} Flux shots complete!")

# ===== STEP 2: Download Flux outputs =====
print("\n=== STEP 2: Downloading Flux outputs ===")
for sn in sorted(pids.keys()):
    prefix = f"ep01_shot{sn:02d}_v6"
    local_path = f"{OUT_SOURCE}/{prefix}.png"
    cmd = (f'ssh {SSH_HOST} "python -c \\"import os;'
           f'outputs=[f for f in os.listdir(r\\\"D:\\\\\\\\ComfyUI_Mie_2026_V8.0\\\\\\\\ComfyUI\\\\\\\\output\\\")'
           f' if f.startswith(\\\"{prefix}\\\") and f.endswith(\\\".png\\\")];'
           f'print(outputs[0] if outputs else \\\"NOT_FOUND\\\")\\""')
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    remote_file = r.stdout.strip()
    if remote_file and remote_file != "NOT_FOUND":
        subprocess.run(["scp", "-q",
            f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/{remote_file}",
            local_path], check=True)
        print(f"  Shot {sn:02d}: ✓ ({remote_file})")
    else:
        print(f"  Shot {sn:02d}: ✗ NOT FOUND")

# ===== STEP 3: Submit Wan 2.2 I2V =====
print("\n=== STEP 3: Submitting Wan 2.2 I2V ===")

# Load Wan 2.2 workflow template (from ComfyUI history)
try:
    with open("/tmp/wan22_flat_api.json") as f:
        wan_wf = json.load(f)
except:
    print("ERROR: Wan 2.2 workflow not found at /tmp/wan22_flat_api.json")
    sys.exit(1)

wan_pids = {}
for sn in sorted(shots_config.keys()):
    cfg = shots_config[sn]
    img_file = f"ep01_shot{sn:02d}_v6.png"
    
    # Deep copy workflow
    prompt = json.loads(json.dumps(wan_wf["prompt"]))
    
    # Node 37: LoadImage
    prompt["37"]["inputs"]["image"] = img_file
    # Node 36: Positive prompt
    prompt["36"]["inputs"]["text"] = cfg["prompt"]
    prompt["36"]["inputs"]["value"] = str(cfg["frames"])  # also update PrimitiveStringMultiline value
    # Node 17: Frame count
    prompt["17"]["inputs"]["value"] = str(cfg["frames"])
    # Node 33: Negative prompt - enhance
    prompt["33"]["inputs"]["text"] = (prompt["33"]["inputs"]["text"] + 
        ", no woman, no girl, no female, no swimsuit, no bikini, no young woman, no lady")
    # Node 24: SimpleMath+ calc
    prompt["24"]["inputs"]["value"] = "a+1"
    # Node 21: VHS_VideoCombine already takes from [29] (pre-RIFE), no change needed

    payload = json.dumps({"prompt": prompt})
    local = f"/tmp/wan_v7_s{sn:02d}.json"
    remote = f"D:/tmp_wan_v7_s{sn:02d}.json"

    with open(local, "w") as f:
        f.write(payload)

    # Upload image first
    subprocess.run(["scp", "-q", f"{OUT_SOURCE}/{img_file}",
        f"{SSH_HOST}:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/{img_file}"], check=True)
    
    # Submit workflow
    subprocess.run(["scp", "-q", local, f"{SSH_HOST}:{remote}"], check=True)
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
         f"curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @{remote}"],
        capture_output=True, text=True, timeout=15)
    
    result = json.loads(r.stdout)
    pid = result.get("prompt_id", "?")
    errs = result.get("node_errors", {})
    status = "✓" if not any(errs) else f"✗ ERR: {errs}"
    wan_pids[sn] = pid
    print(f"  Wan shot {sn:02d}: {pid[:12]}... {status} ({cfg['frames']}f)")
    time.sleep(1)

# Save Wan PIDs
with open(f"{OUT_VIDEO}/wan_v7_pids.json", "w") as f:
    json.dump(wan_pids, f)

print(f"\nWan 2.2 submitted: {len(wan_pids)} shots")
print("Next: monitor Wan completion → download → merge")
