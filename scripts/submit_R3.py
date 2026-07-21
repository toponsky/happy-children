#!/usr/bin/env python3
"""R3: Flux.2-Klein img2img — add glasses to grandma"""
import json, subprocess, os

# Build API-format img2img workflow
wf = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "ep01_grandma_base.png"}},
    "2": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["1", 0], "upscale_method": "lanczos", "megapixels": 1.0}},
    "4": {"class_type": "VAEEncode", "inputs": {"pixels": ["2", 0], "vae": ["12", 0]}},
    "6": {"class_type": "GetImageSize", "inputs": {"image": ["2", 0]}},
    "9": {"class_type": "CLIPLoader", "inputs": {"clip_name": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors", "type": "flux2"}},
    "10": {"class_type": "CLIPTextEncode", "inputs": {
        "clip": ["9", 0],
        "text": "same elderly Chinese woman sitting in wheelchair, silver-white hair, warm gentle face, same clothing, same pose, same background, but now wearing a pair of gold-rimmed round reading glasses on her face, glasses sitting on her nose, clear lenses, thin gold metal frame. Keep everything else identical. Photorealistic, high quality, sharp focus."
    }},
    "11": {"class_type": "CLIPTextEncode", "inputs": {
        "clip": ["9", 0],
        "text": "blurry, low quality, distorted face, bad anatomy, different clothing, different background, no glasses, missing glasses, dark glasses, sunglasses, cartoon, anime, unnatural skin, ugly, mutation"
    }},
    "13": {"class_type": "UNETLoader", "inputs": {
        "unet_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
        "weight_dtype": "default"
    }},
    "14": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["10", 0], "latent": ["4", 0]}},
    "15": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["11", 0], "latent": ["4", 0]}},
    "17": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["14", 0], "guidance": 3.5}},
    "18": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["15", 0], "guidance": 3.5}},
    "19": {"class_type": "KSampler", "inputs": {
        "model": ["13", 0], "positive": ["17", 0], "negative": ["18", 0],
        "latent_image": ["4", 0], "seed": 7777, "steps": 8,
        "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 0.5
    }},
    "12": {"class_type": "VAELoader", "inputs": {"vae_name": "Flux\\flux2-vae.safetensors"}},
    "20": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["12", 0]}},
    "21": {"class_type": "SaveImage", "inputs": {"images": ["20", 0], "filename_prefix": "ep01_ref_grandma_glasses"}},
}

payload = json.dumps({"prompt": wf})

# scp payload to Windows
local = "/tmp/comfy_R3.json"
with open(local, "w") as f:
    f.write(payload)
subprocess.run(["scp", local, "liuyi@192.168.178.104:D:/tmp/comfy_R3.json"], check=True)

# create + submit via ps1
ps1 = '''$workflow = Get-Content "D:\\tmp\\comfy_R3.json" -Raw | ConvertFrom-Json
$body = @{prompt=$workflow; client_id="pi5"} | ConvertTo-Json -Depth 10
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8188/prompt" -Method Post -Body $body -ContentType "application/json"
Write-Output $response.prompt_id
'''
ps1_path = "/tmp/submit_R3.ps1"
with open(ps1_path, "w") as f:
    f.write(ps1)
subprocess.run(["scp", ps1_path, "liuyi@192.168.178.104:D:/tmp/submit_R3.ps1"], check=True)

result = subprocess.run(
    ['ssh', 'liuyi@192.168.178.104', 'powershell -ExecutionPolicy Bypass -File D:\\tmp\\submit_R3.ps1'],
    capture_output=True, text=True
)
print(f"R3: {result.stdout.strip()}")
os.remove(local)
os.remove(ps1_path)
