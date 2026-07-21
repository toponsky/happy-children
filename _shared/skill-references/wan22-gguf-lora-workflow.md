# Wan 2.2 I2V GGUF + LoRA 4-Step Workflow

用户验证过的工作流：`wan2_2_14B_I2V _4步加速.json`（ComfyUI `全部/视频/Wan2.2/` 目录）。

## 与旧 n8n smoothMix 工作流的区别

| 特性 | n8n smoothMix (旧) | GGUF + LoRA (新) |
|------|-------------------|-----------------|
| High-noise model | `smoothMixWan22I2VT2V_i2vHigh.safetensors` | `Wan2.2-I2V-A14B-HighNoise-Q8_0.gguf` + `high_noise_model.safetensors` LoRA |
| Low-noise model | `smoothMixWan22I2VT2V_i2vLow.safetensors` | `Wan2.2-I2V-A14B-LowNoise-Q8_0.gguf` + `low_noise_model.safetensors` LoRA |
| Loader | UNETLoader | UnetLoaderGGUF + LoraLoaderModelOnly |
| Steps | 6 (high: 0→3, low: 3→10000) | 4 (high: 0→2, low: 2→10000) |
| Shift | 8 | 5 |
| RIFE VFI | Yes (2x, disabled for OOM) | No |
| Resolution | 640×832 | 1280×720 |
| Sampler | euler_ancestral | euler |
| Output | VHS 16fps + preview | Single VHS 16fps |
| Swimwear risk | High (smoothMix bias) | Low (GGUF official model) |

## 节点结构 (19 nodes)

```
LoadImage(62) → ImageResizeKJv2(77, 1280×720, crop=center) → WanImageToVideo(63)

CLIPLoader(38, umt5_xxl_fp8_e4m3fn_scaled, type=wan, device=default)
  → CLIPTextEncode(6, positive) → WanImageToVideo(63, positive)
  → CLIPTextEncode(7, negative) → WanImageToVideo(63, negative)

VAELoader(39, wan_2.1_vae) → WanImageToVideo(63, vae) → VAEDecode(8)

UnetLoaderGGUF(68, HighNoise-Q8_0.gguf)
  → LoraLoaderModelOnly(81, high_noise_model.safetensors, strength=1)
  → PatchSageAttentionKJ(70, auto)
  → ModelPatchTorchSettings(71, fp16_accumulation=true)
  → ModelSamplingSD3(54, shift=5)
  → KSamplerAdvanced(57, high: enable, seed=77, steps=4, 0→2, euler/simple, cfg=1)

UnetLoaderGGUF(73, LowNoise-Q8_0.gguf)
  → LoraLoaderModelOnly(82, low_noise_model.safetensors, strength=1)
  → PatchSageAttentionKJ(75, auto)
  → ModelPatchTorchSettings(72, fp16_accumulation=true)
  → ModelSamplingSD3(55, shift=5)
  → KSamplerAdvanced(58, low: disable, seed=77, steps=4, 2→10000, euler/simple, cfg=1)

VAEDecode(8) → VHS_VideoCombine(76, 16fps, h264-mp4, save=true)
```

## API 模板复用

EP01 的成功 API payload 保存在 Windows `D:\tmp\wan22_ep01_shot*.json`（共9个文件）。新镜头直接用 Python `json.load` 加载任一模板，修改以下字段即可提交：

| 节点 | 修改项 | 示例 |
|------|--------|------|
| 62 (LoadImage) | `image` | `ep02_shot01_v2.png` |
| 6 (CLIPTextEncode) | `text` | 新镜头动作描述 |
| 63 (WanImageToVideo) | `length` | 秒×16fps |
| 57/58 (KSamplerAdvanced) | `noise_seed` | 每镜不同避免缓存 |
| 76 (VHS_VideoCombine) | `filename_prefix` | `wan2.2/ep02_shot01` |

**不要重建完整 payload**——模板已有正确的节点 ID、link 引用、模型路径、LoRA 设置和采样参数。只改上述 5 项即可。

## 提示词风格

用户偏好详细的动作描述，包含 `(Dynamic actions: ...)` 段落：

```
Pixar-style 3D animation. [场景描述]. [人物描述]. (Dynamic actions: [具体动作]). Cinematic lighting, 8k resolution.
```

负面提示词包含场景特定的禁止动作（如 `wheelchair moving`）。

## 输出路径

VHS 输出在 `ComfyUI/output/wan2.2/` 子目录下（由 `filename_prefix` 决定）。
