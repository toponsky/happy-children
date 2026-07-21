# Wan 2.2 I2V Flat Workflow (API-Submittable from n8n)

The n8n workflow `本地 - 单人视频工作流 - 生成视频片段` (ID: `eBw6NSL8ffSUNP3d`) contains a **flat, API-submittable** Wan 2.2 I2V workflow. Unlike the blueprint (`Image to Video (Wan 2.2).json`) which uses subgraphs and cannot be submitted via API, this workflow uses standard flat nodes.

## Source

Extract from n8n database on Pi5:
```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/home/pi5/.n8n/database.sqlite')
rows = db.execute('SELECT nodes FROM workflow_history WHERE workflowId=? ORDER BY \"createdAt\" DESC LIMIT 1', ('eBw6NSL8ffSUNP3d',)).fetchall()
nodes = json.loads(rows[0][0])
for n in nodes:
    if n.get('name') == 'HTTP Request':
        body = n.get('parameters',{}).get('jsonBody','')
        if body.startswith('='): body = body[1:]
        with open('wan22_flat.json', 'w') as f: f.write(body)
db.close()
"
```

## Workflow Structure (32 nodes)

| Node ID | Type | Purpose |
|---------|------|---------|
| 37 | `LoadImage` | Start image input |
| 36 | `PrimitiveStringMultiline` | Positive prompt |
| 33 | `CLIPTextEncode` | Negative prompt (extensive) |
| 17 | `ImpactInt` | Frame count |
| 18 | `ImpactInt` | Width (640) |
| 16 | `ImpactInt` | Height (832) |
| 19 | `Seed (rgthree)` | Random seed |
| 39 | `ImageResizeKJv2` | Resize + crop to target |
| 40 | `CLIPVisionEncode` | CLIP vision conditioning |
| 41 | `CLIPVisionLoader` | `clip_vision_h.safetensors` |
| 9 | `UNETLoader` | Low-noise model: `smoothMixWan22I2VT2V_i2vLow.safetensors` |
| 11 | `UNETLoader` | High-noise model: `smoothMixWan22I2VT2V_i2vHigh.safetensors` |
| 10 | `ModelSamplingSD3` | Shift=8 for low-noise |
| 12 | `ModelSamplingSD3` | Shift=8 for high-noise |
| 13 | `CLIPLoader` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors`, type=wan, device=cpu |
| 14 | `VAELoader` | `wan_2.1_vae.safetensors` |
| 5/8 | `PathchSageAttentionKJ` | SAGE attention patches |
| 6/15 | `ModelPatchTorchSettings` | FP16 accumulation |
| 25 | `WanImageToVideo` | Core I2V conditioning (width, height, length, batch_size=1) |
| 28 | `CLIPTextEncode` | Encode positive prompt |
| 30 | `KSamplerAdvanced` | High-noise sampler (steps 0→3, add_noise=enable) |
| 1 | `KSamplerAdvanced` | Low-noise sampler (steps 3→10000, add_noise=disable) |
| 22 | `VAEDecode` | Decode latent to image |
| 27 | `ImageScaleBy` | 2x scale up |
| 23 | `RIFE VFI` | Frame interpolation (2x multiplier, rife49.pth) |
| 29 | `easy cleanGpuUsed` | GPU cleanup node |
| 20 | `VHS_VideoCombine` | Preview video (16fps, save_output=false) |
| 21 | `VHS_VideoCombine` | Final video (32fps after RIFE, save_output=true) |

## Model Path Verification (Mie V8.0)

All models confirmed present on `D:\ComfyUI_Mie_2026_V8.0\ComfyUI\models\`:

| Model | Path | Status |
|-------|------|--------|
| Low-noise UNET | `unet/smoothMixWan22I2VT2V_i2vLow.safetensors` | ✅ |
| High-noise UNET | `unet/smoothMixWan22I2VT2V_i2vHigh.safetensors` | ✅ |
| CLIP | `text_encoders/Wan/umt5-xxl-enc-fp8_e4m3fn.safetensors` | ✅ (note: different filename) |
| CLIP (alt) | `clip/umt5_xxl_fp8_e4m3fn_scaled.safetensors` | ✅ |
| VAE | `vae/wan_2.1_vae.safetensors` | ✅ |
| CLIP Vision | `clip_vision/clip_vision_h.safetensors` | ✅ |
| RIFE | `rife/rife49.pth` | ✅ |

## API Submission Pattern

```python
import json, subprocess

# 1. Load workflow
with open('wan22_flat.json') as f:
    wf = json.load(f)

prompt = wf['prompt']

# 2. Set parameters
prompt['37']['inputs']['image'] = 'scene.png'          # LoadImage
prompt['36']['inputs']['text'] = 'Pixar style...'     # Positive prompt
prompt['17']['inputs']['value'] = 81                   # Frame count

# 3. Submit via SSH (bypasses RTK proxy)
payload = json.dumps({'prompt': prompt})
with open('/tmp/payload.json', 'w') as f:
    f.write(payload)

subprocess.run(['scp', '-q', '/tmp/payload.json',
    'liuyi@192.168.178.104:D:/tmp_payload.json'])
r = subprocess.run(['ssh', 'liuyi@192.168.178.104',
    'curl -s -X POST http://127.0.0.1:8188/prompt '
    '-H "Content-Type: application/json" '
    '-d @D:/tmp_payload.json'],
    capture_output=True, text=True)
result = json.loads(r.stdout)
print(f"prompt_id: {result['prompt_id']}")

# 4. Poll for completion
import urllib.request, time
pid = result['prompt_id']
while True:
    time.sleep(20)
    r = urllib.request.urlopen(f'http://192.168.178.104:8188/queue', timeout=5)
    q = json.loads(r.read())
    if not q.get('queue_running'):
        rh = urllib.request.urlopen(f'http://192.168.178.104:8188/history/{pid}', timeout=5)
        h = json.loads(rh.read())
        if pid in h:
            break
```

## Performance

- **81 frames** (≈5s @ 16fps input, 10s @ 32fps after RIFE): ~10-15 minutes on RTX 5090
- Without LoRA speedup (uses dual samplers directly)
- RIFE 2x interpolation doubles output frame count
- VHS encoding is the final step

## Key Differences from Blueprint

| Aspect | Blueprint (subgraph) | n8n Flat |
|--------|---------------------|----------|
| Format | `definitions/subgraphs` | Flat `nodes` dict |
| API submit | ❌ UUID not recognized | ✅ Standard flat nodes |
| Models | `wan/wan22-i2v-14b-fp8-*-scaled.safetensors` | `unet/smoothMixWan22I2VT2V_i2v*.safetensors` |
| RIFE VFI | No | Yes (2x frame interpolation) |
| VHS encode | Yes | Yes (preview + final) |
| GPU cleanup | No | `easy cleanGpuUsed` nodes |
| SAGE Attention | No | `PathchSageAttentionKJ` nodes |

## n8n Pipeline Context

This sub-workflow is invoked by the main workflow `本地 - 主工作流` (68 nodes) which orchestrates:
1. 生成人物 (Qwen Image via ComfyUI)
2. 生成分镜图片 (Flux via ComfyUI)
3. 生成配音 (DeepSeek + Qwen3-TTS)
4. **生成视频片段** ← this workflow
5. 生成背景音乐 (DeepSeek + AceStep)
