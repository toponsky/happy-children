#!/usr/bin/env python3
"""Submit R4 glasses, R6 bag, R5 wheelchair to ComfyUI Flux.2-Klein"""
import json, subprocess, os, sys

COMFY = "http://127.0.0.1:8188"
OUT = "/home/pi5/ai_cartoon/happy_children/00-characters"

jobs = [
    {
        "name": "R4_glasses",
        "prefix": "ep01_ref_glasses",
        "prompt": "a pair of gold-rimmed round reading glasses, isolated on pure white background, product photography, studio lighting, high detail, clean edges, transparent lenses, 8K",
        "negative": "blurry, distorted, hands, face, person, dark background, shadows, text, watermark",
    },
    {
        "name": "R5_wheelchair",
        "prefix": "ep01_ref_wheelchair",
        "prompt": "a dark metal manual wheelchair, side profile view, isolated on pure white studio background, large rear wheels with handrims, small front casters, armrests, footrests, clean studio lighting, product photography, 8K",
        "negative": "blurry, person, human, face, distorted, dark background, text, watermark, car, vehicle",
    },
    {
        "name": "R6_bag",
        "prefix": "ep01_ref_bag",
        "prompt": "a bright red children's backpack, small size for a 5-year-old, isolated on pure white background, product photography, studio lighting, front view, cute design, clean edges, high detail, 8K",
        "negative": "blurry, person, face, dark background, text, watermark, distorted, other colors",
    },
]

# Flux.2-Klein API workflow template
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
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": prompt}
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": negative}
        },
        "4": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": 1280, "height": 1280, "batch_size": 1}
        },
        "5": {
            "class_type": "FluxGuidance",
            "inputs": {"conditioning": ["2", 0], "guidance": 3.5}
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["5", 0], "negative": ["3", 0],
                "latent_image": ["4", 0], "seed": seed, "steps": 28,
                "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]}
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": prefix}
        },
    }

for job in jobs:
    wf = make_workflow(job["prompt"], job["negative"], job["prefix"])
    payload_path = f"/tmp/comfy_{job['name']}.json"
    with open(payload_path, "w") as f:
        json.dump({"prompt": wf}, f)
    
    scp_cmd = f"scp {payload_path} 'liuyi@192.168.178.104:D:/tmp/comfy_{job['name']}.json'"
    subprocess.run(scp_cmd, shell=True, check=True)
    
    windows_file = f"D:\\tmp\\comfy_{job['name']}.json"
    curl_cmd = f'ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H \\"Content-Type: application/json\\" -d @{windows_file}"'
    result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
    print(f"{job['name']}: {result.stdout.strip()}")
    os.remove(payload_path)

print("All 3 props submitted. Monitoring...")
