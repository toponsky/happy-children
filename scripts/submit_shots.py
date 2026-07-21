#!/usr/bin/env python3
"""Generate 10 shot source images via Flux.2-Klein txt2img"""
import json, subprocess, os

shots = [
    ("01", "wide shot, sunny morning, residential street, a cute 5-year-old Chinese boy wearing a bright red hoodie and carrying a red backpack, running out of his house front door, door behind him, warm sunlight, green trees, Pixar style, children's book illustration, cinematic lighting, 8K", "5s全景"),
    ("02", "medium shot, a cute 5-year-old Chinese boy wearing a bright red hoodie and red backpack, happily skipping along a sidewalk, bright morning sunlight, trees and houses in background, cheerful atmosphere, Pixar style, children's book illustration, 8K", "4s中景"),
    ("03", "wide shot, street intersection sidewalk, an elderly Chinese woman with silver-white hair sitting in a dark metal manual wheelchair, she is NOT wearing glasses, her glasses have fallen on the ground in front of her, she is bending forward reaching her hand toward the glasses but cannot reach them, worried expression, bright morning, outdoor scene, NO glasses on her face, glasses visible on the ground, no other people, Pixar style, cinematic, 8K", "5s远景"),
    ("04", "close-up shot, face of an elderly Chinese woman with silver-white hair, sitting in wheelchair, anxious helpless expression, squinting because she cannot see without glasses, NO glasses on her face, her dropped glasses visible on the ground in the foreground, shallow depth of field, emotional, Pixar style, cinematic, 8K", "3s特写"),
    ("05", "medium shot, a cute 5-year-old Chinese boy in bright red hoodie with red backpack, stopped in his tracks, tilting his head thinking, looking at something in the distance with curiosity, sidewalk background, morning light, Pixar style, children's book illustration, 8K", "3s中景"),
    ("06", "wide shot, a cute 5-year-old Chinese boy in bright red hoodie running toward an elderly woman in a wheelchair, the boy's back is toward camera running away from us, the elderly woman with silver-white hair is in the wheelchair ahead, she is reaching for glasses on the ground, morning street scene, dynamic motion, Pixar style, cinematic, 8K", "3s全景"),
    ("07", "close-up shot, a cute 5-year-old Chinese boy in bright red hoodie bending down, picking up a pair of gold-rimmed glasses from the ground, holding them out with both hands toward an elderly woman in wheelchair, kind helpful expression, the elderly woman with silver-white hair is sitting in wheelchair looking at the boy, NO glasses on her face yet, warm morning light, emotional moment, Pixar style, cinematic, 8K", "4s近景"),
    ("08", "medium shot, an elderly Chinese woman with silver-white hair sitting in wheelchair, NOW wearing gold-rimmed glasses on her face, she has a surprised grateful happy smile, she just put on her glasses and can see clearly now, the boy in red hoodie is beside her, warm connection, morning street, emotional, Pixar style, cinematic, 8K", "4s中景"),
    ("09", "medium shot, a cute 5-year-old Chinese boy in bright red hoodie with red backpack, waving goodbye with a big smile, facing the camera, turning to run toward school direction, an elderly woman in wheelchair visible behind him waving back, morning sunlight, warm farewell, Pixar style, cinematic, 8K", "5s中景"),
    ("10", "wide shot, a cute 5-year-old Chinese boy in bright red hoodie with red backpack, happily skipping and running toward a distant school building, back view from behind the boy, the school is visible on the horizon, golden morning sunlight streaming down, beautiful sky, hopeful and warm atmosphere, Pixar style, cinematic, 8K", "6s远景"),
]

NEGATIVE = "no woman, no girl, no female, no swimsuit, no bikini, no other people, no extra characters, blurry, low quality, distorted, ugly, deformed, bad anatomy, text, watermark, dark, gloomy"

def make_workflow(prompt, prefix, seed=42):
    return {
        "1": {"class_type": "FluxLoader", "inputs": {
            "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
            "weight_dtype": "default",
            "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
            "clip_name2_opt": ".none",
            "vae_name": "Flux\\flux2-vae.safetensors",
            "clip_vision_name": ".none",
            "style_model_name": ".none"
        }},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": prompt}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": NEGATIVE}},
        "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1664, "height": 1280, "batch_size": 1}},
        "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": 3.5}},
        "6": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["5", 0], "negative": ["3", 0],
            "latent_image": ["4", 0], "seed": seed, "steps": 28,
            "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        }},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": f"ep01_shot{prefix}"}},
    }

for sn, prompt, desc in shots:
    wf = make_workflow(prompt, sn, seed=hash(sn) % 100000)
    payload = json.dumps({"prompt": wf})
    fname = f"/tmp/comfy_shot{sn}.json"
    with open(fname, "w") as f:
        f.write(payload)
    
    winfile = f"D:\\tmp\\comfy_shot{sn}.json"
    subprocess.run(["scp", fname, f"liuyi@192.168.178.104:{winfile}"], check=True, capture_output=True)
    
    curl = f'ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H \\"Content-Type: application/json\\" -d @{winfile}"'
    result = subprocess.run(curl, shell=True, capture_output=True, text=True)
    pid = "?"
    try:
        pid = json.loads(result.stdout).get("prompt_id", "?")[:12]
    except:
        pid = result.stdout.strip()[:50]
    print(f"Shot {sn} ({desc}): {pid}")
    os.remove(fname)

print("\nAll 10 shots submitted to ComfyUI!")
print("Monitor: /home/pi5/ai_cartoon/happy_children/00-characters/monitor_shots.sh")
