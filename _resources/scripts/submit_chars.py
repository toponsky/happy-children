#!/usr/bin/env python3
"""Submit R1 Michael and R2 grandma (no glasses) to ComfyUI Flux.2-Klein"""
import json, subprocess, os

COMFY = "http://127.0.0.1:8188"

jobs = [
    {
        "name": "R1_michael",
        "prefix": "ep01_ref_michael",
        "prompt": "a cute 5-year-old Chinese boy, front facing portrait, looking directly at camera, happy smiling face, short dark hair, wearing a bright red hoodie, carrying a red backpack, clean white studio background, soft even lighting, full body shot, character reference sheet, high quality, 8K, Pixar style, children's book illustration style",
        "negative": "blurry, distorted, ugly, adult, teenager, girl, woman, white hoodie, blue hoodie, green hoodie, other colors, dark background, text, watermark, multiple people",
    },
    {
        "name": "R2_grandma_no_glasses",
        "prefix": "ep01_ref_grandma_noglass",
        "prompt": "a kind elderly Chinese woman, about 75 years old, sitting in a dark metal manual wheelchair, silver-white hair, warm gentle face, squinting eyes slightly because she cannot see clearly WITHOUT glasses, NO glasses on her face, wearing simple comfortable clothes, front facing, clean white studio background, soft lighting, full body shot showing wheelchair, character reference sheet, 8K, Pixar style",
        "negative": "glasses, eyeglasses, spectacles, sunglasses, wearing glasses, blurry, distorted, ugly, young woman, standing, walking, text, watermark, dark background, multiple people",
    },
]

def make_workflow(prompt, negative, prefix, seed=42):
    return {
        "1": {
            "class_type": "FluxLoader",
            "inputs": {
                "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
                "weight_dtype": "default",
                "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
                "clip_name2_opt": ".none",
                "vae_name": "Flux\\flux2-vae.safetensors",
                "clip_vision_name": ".none",
                "style_model_name": ".none"
            }
        },
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": prompt}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": negative}},
        "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 1664, "batch_size": 1}},
        "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["2", 0], "guidance": 3.5}},
        "6": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["5", 0], "negative": ["3", 0],
            "latent_image": ["4", 0], "seed": seed, "steps": 28,
            "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        }},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": prefix}},
    }

for job in jobs:
    wf = make_workflow(job["prompt"], job["negative"], job["prefix"])
    payload = json.dumps({"prompt": wf})
    
    fname = f"/tmp/comfy_{job['name']}.json"
    with open(fname, "w") as f:
        f.write(payload)
    
    winfile = f"D:\\tmp\\comfy_{job['name']}.json"
    subprocess.run(["scp", fname, f"liuyi@192.168.178.104:{winfile}"], check=True)
    
    curl = f'ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H \\"Content-Type: application/json\\" -d @{winfile}"'
    result = subprocess.run(curl, shell=True, capture_output=True, text=True)
    print(f"{job['name']}: {result.stdout.strip()}")
    os.remove(fname)

print("R1 + R2 submitted.")
