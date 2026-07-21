# Master Background → Multi-Shot img2img

## Problem

Generating each outdoor shot independently via Flux txt2img produces inconsistent environments — different pavement textures, different lighting angles, different tree placements. This breaks visual continuity across shots.

## Solution

Generate **one master background** (empty scene, no characters) via Flux txt2img, then reuse it as the img2img base for ALL outdoor shots.

## Workflow

### Step 1: Generate Master Background

Flux.2-Klein txt2img, wide establishing shot, NO people:

```
WIDE ESTABLISHING SHOT of a quiet, tree-lined suburban neighborhood sidewalk
on a sunny morning. Gray asphalt pavement with subtle cracks, green grass strip
beside the sidewalk, a few leafy trees casting dappled shadows, distant houses
with fences visible but not prominent. Warm golden morning sunlight, soft shadows,
peaceful atmosphere. Pixar-style 3D animation, cinematic wide-angle composition,
empty street scene with no people or characters, clean background suitable for
character placement. Neutral colors, photorealistic pavement texture, 4K quality.
```

Negative: `woman, girl, female, man, boy, person, people, character, swimsuit, bikini, blurry, low quality, bad anatomy, watermark, text, signature, cars, vehicles`

Save as `00-characters/R_bg_street.png`.

### Step 2: Upload to ComfyUI input

```bash
scp R_bg_street.png "liuyi@192.168.178.104:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/R_bg_street.png"
```

### Step 3: Flux img2img per Shot (FluxLoader-based, 9 nodes)

Same background, different prompt per shot. Template:

```json
{
  "1": {"class_type": "LoadImage", "inputs": {"image": "R_bg_street.png"}},
  "2": {"class_type": "FluxLoader", "inputs": {
    "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
    "weight_dtype": "default",
    "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
    "clip_name2_opt": ".none",
    "vae_name": "Flux\\flux2-vae.safetensors",
    "clip_vision_name": ".none",
    "style_model_name": ".none"
  }},
  "3": {"class_type": "VAEEncode", "inputs": {"pixels": ["1", 0], "vae": ["2", 2]}},
  "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "SHOT PROMPT HERE — describe characters + action, add 'Keep the exact same background, same lighting, same pavement, same trees, same houses as the original image'", "clip": ["2", 1]}},
  "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "woman, girl, female, swimsuit, bikini, blurry, low quality, bad anatomy, deformed, watermark, text, signature, black glasses, thick frames, plastic frames, sunglasses, different background", "clip": ["2", 1]}},
  "6": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["4", 0], "guidance": 3.5}},
  "7": {"class_type": "KSampler", "inputs": {"seed": RANDOM, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 0.55, "model": ["2", 0], "positive": ["6", 0], "negative": ["5", 0], "latent_image": ["3", 0]}},
  "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["2", 2]}},
  "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "ep01_shotXX_i2i", "images": ["8", 0]}}
}
```

### Key Parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `denoise` | 0.55 | Enough to add characters, low enough to preserve background |
| `steps` | 8 | Fast, sufficient for img2img (not full generation) |
| `guidance` | 3.5 | Standard Flux value |
| Prompt ending | "Keep the exact same background..." | Critical — tells Flux to preserve the input environment |

### Shots Using Same Background

For Happy Children ep01, shots 03, 04, 06, 07, 08, 09 are all outdoor street scenes sharing the same master background.

## vs PIL Compositing

| Approach | When to use |
|----------|------------|
| **Master bg + img2img** | Generating entire scenes with characters interacting in environment (shots 03,07,08,09) |
| **PIL compositing + low denoise Flux** | Pasting a specific prop image exactly, when Flux would get the prop wrong (pitfall #25 in SKILL.md) |

## Submission Pattern

SSH submit via Windows localhost curl (bypasses RTK proxy):

```bash
scp -q workflow.json liuyi@192.168.178.104:D:/tmp_workflow.json
ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H 'Content-Type: application/json' -d @D:\\tmp_workflow.json"
```
