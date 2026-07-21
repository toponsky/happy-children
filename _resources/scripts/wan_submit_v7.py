#!/usr/bin/env python3
"""Submit Wan 2.2 I2V for 8 shots using v6 source images."""
import json, subprocess, time

SSH_HOST = "liuyi@192.168.178.104"
COMFY_HOST = "192.168.178.104"
OUTDIR = "/home/pi5/ai_cartoon/happy_children/06-video"

with open("/tmp/wan22_flat_api.json") as f:
    wan_wf = json.load(f)

shots = {
    1:  (81,  "Pixar animation, young boy in red hoodie with red backpack running out of house front door, sunny morning suburban neighborhood, birds flying, warm golden sunlight, smooth motion, no women, no female, 16fps"),
    2:  (65,  "Pixar animation, young boy in red hoodie happily skipping on sidewalk, backpack bouncing, trees in background, warm morning light, cheerful smile, solo boy, no women, 16fps"),
    5:  (49,  "Pixar animation, medium shot, young boy in red hoodie standing on sidewalk, head tilting curiously, thinking expression, subtle movement, solo boy, no women, 16fps"),
    6:  (49,  "Pixar animation, young boy in red hoodie running toward camera with determination, elderly woman fallen on ground visible in distance, empty tipped wheelchair, caring face, no young women, 16fps"),
    9:  (97,  "Pixar animation, young boy in red hoodie pushing elderly Asian woman with glasses in wheelchair along suburban street toward house, gentle morning light, trees, no other people, no young women, 16fps"),
    10: (65,  "Pixar animation, close-up at house doorstep, elderly Asian woman with glasses in wheelchair reaching hand to gently pat head of young boy in red hoodie, warm grateful smile, teary eyes, soft sunlight, 16fps"),
    11: (65,  "Pixar animation, young boy in red hoodie waving goodbye at house entrance, big happy smile, elderly woman in wheelchair visible behind at doorstep, cheerful, solo waving boy, no other people, 16fps"),
    12: (97,  "Pixar animation, wide shot, young boy in red hoodie with red backpack happily running toward colorful school building in far distance, golden warm sunlight filling scene, birds, heartwarming ending, no women, 16fps"),
}

NEG_EXTRA = ", no woman, no girl, no female, no swimsuit, no bikini, no young woman, no lady, no adult female"

pids = {}
for sn in sorted(shots.keys()):
    frames, pos_prompt = shots[sn]
    img_file = f"ep01_shot{sn:02d}_v6.png"
    
    prompt = json.loads(json.dumps(wan_wf["prompt"]))
    
    prompt["37"]["inputs"]["image"] = img_file
    prompt["36"]["inputs"]["text"] = pos_prompt
    prompt["36"]["inputs"]["value"] = str(frames)
    prompt["17"]["inputs"]["value"] = str(frames)
    prompt["33"]["inputs"]["text"] = prompt["33"]["inputs"]["text"] + NEG_EXTRA
    prompt["24"]["inputs"]["value"] = "a+1"

    payload = json.dumps({"prompt": prompt})
    local = f"/tmp/wan_v7_s{sn:02d}.json"
    remote = f"D:/tmp_wan_v7_s{sn:02d}.json"

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
    status = "✓" if not any(errs) else f"✗ ERR: {errs}"
    pids[sn] = pid
    print(f"Wan shot {sn:02d}: {pid[:12]}... {status} ({frames}f)")
    time.sleep(1)

with open(f"{OUTDIR}/wan_v7_pids.json", "w") as f:
    json.dump(pids, f)

print(f"\nDone. {len(pids)} Wan 2.2 jobs submitted.")
print(f"PIDs saved to {OUTDIR}/wan_v7_pids.json")
