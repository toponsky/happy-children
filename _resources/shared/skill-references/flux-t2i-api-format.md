# Flux.2-Klein 文生图 API 完整格式

## 工作流（7 节点）

```python
{
  "prompt": {
    "1": {"class_type": "FluxLoader",
          "inputs": {
              "model_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors",
              "weight_dtype": "default",
              "clip_name1": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors",
              "clip_name2_opt": ".none",
              "vae_name": "Flux\\flux2-vae.safetensors",
              "clip_vision_name": ".none",
              "style_model_name": ".none"}},
    "2": {"class_type": "CLIPTextEncode",
          "inputs": {"clip": ["1", 1], "text": "PROMPT_HERE"}},
    "3": {"class_type": "CLIPTextEncode",
          "inputs": {"clip": ["1", 1], "text": "NEGATIVE_PROMPT"}},
    "4": {"class_type": "EmptySD3LatentImage",
          "inputs": {"width": 1280, "height": 720, "batch_size": 1}},
    "5": {"class_type": "KSampler",
          "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0],
                      "latent_image": ["4", 0], "seed": 42, "steps": 8,
                      "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                      "denoise": 1.0}},
    "6": {"class_type": "VAEDecode",
          "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
    "7": {"class_type": "SaveImage",
          "inputs": {"images": ["6", 0], "filename_prefix": "output"}}
  }
}
```

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| model_name | `Flux\Flux.2-Klein\flux-2-klein-9b-fp8.safetensors` | Flux.2-Klein fp8 |
| clip_name1 | `Flux.2-Klein\qwen_3_8b_fp8mixed.safetensors` | Qwen 3 8B 编码器 |
| clip_name2_opt | `.none` | 不用第二个编码器 |
| clip_vision_name | `.none` | 必须设，否则报 missing required |
| style_model_name | `.none` | 必须设 |
| vae_name | `Flux\flux2-vae.safetensors` | Flux 2 VAE |
| steps | 6-10 | 8=平衡质量速度 |
| cfg | 1.0 | Flux 模型固定值 |
| seed | 42 | 可改 |
| width × height | 1280 × 720 | 16:9 |

## 陷阱

1. **必须用 FluxLoader**（不是 UNETLoader+CLIPLoader）— 自动处理 VAE 和 guidance
2. **clip_vision_name 和 style_model_name 必须设 `.none`** — 否则 `required_input_missing` 错误
3. **cfg 必须浮点数** `1.0`，不能是整数 `1`
4. **不要用 CLIPTextEncodeFlux** — 它期望 T5 编码器，Qwen 3 8B 的 tokenize() 返回不同键名 → KeyError
5. **图片自动保存到** `ComfyUI/output/`，下载时用 SCP
