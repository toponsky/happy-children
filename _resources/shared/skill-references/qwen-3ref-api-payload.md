# Qwen Image Edit 2511 三图参考 API 提交格式

完整的 15 节点 API JSON 模板，可直接 scp + curl 提交。

## 完整模板

```json
{
  "prompt": {
    "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image"}},
    "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "Qwen\\qwen_image_edit_2511_fp8mixed.safetensors", "weight_dtype": "default"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "Qwen\\qwen_image_vae.safetensors"}},
    "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": "Qwen-Image-Edit\\Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors", "strength_model": 1}},
    "5": {"class_type": "LoadImage", "inputs": {"image": "R1_character.png"}},
    "6": {"class_type": "LoadImage", "inputs": {"image": "R2_prop.png"}},
    "7": {"class_type": "LoadImage", "inputs": {"image": "R3_background.png"}},
    "8": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["1", 0], "vae": ["3", 0], "image1": ["5", 0], "image2": ["6", 0], "image3": ["7", 0], "prompt": "..."}},
    "9": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["8", 0], "reference_latents_method": "index_timestep_zero"}},
    "10": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["8", 0], "reference_latents_method": "index_timestep_zero"}},
    "11": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["10", 0]}},
    "12": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 720, "batch_size": 1}},
    "13": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["9", 0], "negative": ["11", 0], "latent_image": ["12", 0], "seed": 42, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
    "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["3", 0]}},
    "15": {"class_type": "SaveImage", "inputs": {"images": ["14", 0], "filename_prefix": "output"}}
  }
}
```

## 节点映射

| 节点 ID | 类型 | 作用 | 需要修改 |
|---------|------|------|---------|
| 1 | CLIPLoader | 加载 qwen_2.5_vl CLIP | ❌ 固定 |
| 2 | UNETLoader | 加载 qwen_image_edit_2511 UNET | ❌ 固定 |
| 3 | VAELoader | 加载 qwen_image_vae | ❌ 固定 |
| 4 | LoraLoaderModelOnly | 加载 Lightning 4-step LoRA | ❌ 固定 |
| 5 | LoadImage | 参考图 1（主角） | ✅ `image` 文件名 |
| 6 | LoadImage | 参考图 2（道具/配角） | ✅ `image` 文件名 |
| 7 | LoadImage | 参考图 3（背景） | ✅ `image` 文件名 |
| 8 | TextEncodeQwenImageEditPlus | 提示词编码 | ✅ `prompt` 文本 |
| 9-11 | FluxKontextMultiReferenceLatentMethod ×2 + ConditioningZeroOut | 三图参考方法 | ❌ 固定 |
| 12 | EmptySD3LatentImage | 画布尺寸 | ✅ width/height |
| 13 | KSampler | 采样 | ✅ seed |
| 14 | VAEDecode | 解码 | ❌ 固定 |
| 15 | SaveImage | 保存 | ✅ filename_prefix |

## 常见错误

| 错误信息 | 原因 | 修复 |
|---------|------|------|
| `Required input is missing: prompt` | 文本字段名用了 `text` | 改为 `"prompt"` |
| `Invalid image file: R8_shot01_door.png` | 参考图未上传到 ComfyUI input | scp 到 `D:\ComfyUI_...\input\` |
| `Custom validation failed for node` | LoadImage 的 `image` 或 `upload` 参数格式错误 | 只保留 `"image": "filename.png"` |

## 提交命令

```bash
# 1. 上传参考图
scp R1.png "liuyi@192.168.178.104:/D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/"

# 2. 写 payload（修改 image 文件名 + prompt）
write_file /tmp/payload.json '{"prompt": {...}}'

# 3. 提交
scp /tmp/payload.json "liuyi@192.168.178.104:/D:/tmp/payload.json"
ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @D:\\tmp\\payload.json"

# 4. 等待 + 下载
sleep 30
# 查 history → 拿 filename → scp
```
