# Flux.2-Klein API 工作流格式

通过 ComfyUI API 提交 Flux.2-Klein 文生图工作流时的正确格式。

## 节点清单

| 节点 | class_type | 关键字段 |
|------|-----------|---------|
| 1 | `FluxLoader` | 模型加载器 |
| 2 | `CLIPTextEncode` | 正提示词 |
| 3 | `CLIPTextEncode` | 负提示词 |
| 4 | `FluxGuidance` | 引导强度 |
| 5 | `EmptyLatentImage` | 画布尺寸 |
| 6 | `KSampler` | 采样参数 |
| 7 | `VAEDecode` | 解码 |
| 8 | `SaveImage` | 保存输出 |

## FluxLoader 完整字段（极易遗漏）

`FluxLoader` 节点有 **7 个必填字段**，缺任何一个都会报 `required_input_missing`：

```json
{
  "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
  "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
  "clip_name2_opt": ".none",
  "weight_dtype": "default",
  "clip_vision_name": ".none",
  "style_model_name": ".none",
  "vae_name": "Flux\\flux2-vae.safetensors"
}
```

**不是 `UNETLoader`** — Flux.2-Klein 用 `FluxLoader` 一站式加载模型+Qwen编码器+VAE。

## KSampler 关键参数

```json
{
  "seed": 42,
  "steps": 20,
  "cfg": 1.0,
  "sampler_name": "euler",
  "scheduler": "simple",
  "denoise": 1.0
}
```

**注意**: `cfg` 必须是 `1.0`（Flux 用 FluxGuidance 而非 CFG）。

## API 提交格式

工作流 JSON 必须包在 `{"prompt": {...}}` 里：

```bash
curl -X POST http://HOST:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": <workflow_json>, "client_id": "..."}'
```

直接用 `python3 scripts/run_workflow.py --workflow W.json --host HOST --output-dir DIR` 最省事。

## 提示词结构

```
[风格锚定英文] + [人物一致性关键词] + [场景动作描述]
+ bright warm colors, soft cinematic lighting
+ high quality CGI render, Disney Pixar inspired
```

负提示词统一：
```
realistic, photorealistic, dark, horror, scary, sharp angles,
thin, gritty, anime, 2D flat, low quality, blurry, deformed,
bad anatomy, extra limbs, missing limbs, text, watermark,
signature, ugly face, bad face
```
