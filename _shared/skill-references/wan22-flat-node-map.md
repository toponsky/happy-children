# Wan 2.2 smoothMix I2V Flat 工作流节点映射

32 节点 flat API 工作流，从 ComfyUI `/history` 提取（不是 n8n 模板，n8n 的有模板变量无法解析）。

## 提取方法

```bash
# 从 ComfyUI history 找最新 Wan 工作流
ssh host "curl -s http://127.0.0.1:8188/history" | python3 -c "
import json,sys
h=json.load(sys.stdin)
for pid in sorted(h.keys(),reverse=True):
    e=h[pid]; s=e.get('status',{})
    if s.get('completed') and s.get('status_str')=='success':
        p=e.get('prompt',[{},{},{}])[2]
        types=[v.get('class_type','') for v in p.values()]
        if any('WanVideo' in t for t in types):
            json.dump({'prompt':p}, open('/tmp/wan22_flat_api.json','w'))
            break
"
```

## 关键节点 ID（提交时修改这些）

| 节点 | class_type | 作用 | 修改方式 |
|------|-----------|------|---------|
| **37** | LoadImage | 输入源图 | `prompt["37"]["inputs"]["image"] = "filename.png"` |
| **36** | PrimitiveStringMultiline | 正面提示词 | `prompt["36"]["inputs"]["text"] = "..."` |
| **17** | ImpactInt | 帧数 | `prompt["17"]["inputs"]["value"] = "81"` |
| **33** | CLIPTextEncode | 负面提示词 | `prompt["33"]["inputs"]["text"] = "..."` |
| **21** | VHS_VideoCombine | 视频输出(save_output=True) | 已连接 [29]（pre-RIFE），无需修改 |
| **19** | Seed (rgthree) | 随机种子 | 默认 -1，自动随机 |

## 完整节点清单（32节点）

| ID | class_type | 说明 |
|----|-----------|------|
| 1 | KSamplerAdvanced | 低噪采样器（steps 3→10000） |
| 5 | PathchSageAttentionKJ | sage_attention=auto |
| 6 | ModelPatchTorchSettings | fp16_accumulation=True |
| 8 | PathchSageAttentionKJ | sage_attention=auto |
| 9 | UNETLoader | smoothMixWan22I2VT2V_i2vLow.safetensors |
| 10 | ModelSamplingSD3 | shift=8.0 |
| 11 | UNETLoader | smoothMixWan22I2VT2V_i2vHigh.safetensors |
| 12 | ModelSamplingSD3 | shift=8.0 |
| 13 | CLIPLoader | umt5_xxl_fp8_e4m3fn_scaled.safetensors, type=wan |
| 14 | VAELoader | wan_2.1_vae.safetensors |
| 15 | ModelPatchTorchSettings | fp16_accumulation=True |
| 16 | ImpactInt | value=832（高度） |
| 17 | ImpactInt | value=96（帧数，**需修改**） |
| 18 | ImpactInt | value=640（宽度） |
| 19 | Seed (rgthree) | seed=-1 |
| 20 | VHS_VideoCombine | 预览输出(save_output=False) |
| 21 | VHS_VideoCombine | 最终输出(save_output=True)，从 [29] 取图 |
| 22 | VAEDecode | 解码 latent |
| 23 | RIFE VFI | 插帧（已被 21 绕过） |
| 24 | SimpleMath+ | value=a+1（帧数计算） |
| 25 | WanImageToVideo | Wan I2V 核心节点 |
| 26 | easy cleanGpuUsed | 清理 GPU |
| 27 | ImageScaleBy | 2x upscale (lanczos) |
| 28 | CLIPTextEncode | 正面 text→[36] |
| 29 | easy cleanGpuUsed | 清理 GPU |
| 30 | KSamplerAdvanced | 高噪采样器（steps 0→3） |
| 33 | CLIPTextEncode | 负面 text（**需修改**） |
| 36 | PrimitiveStringMultiline | 提示词文本+value（**需修改**） |
| 37 | LoadImage | 输入图（**需修改**） |
| 39 | ImageResizeKJv2 | 尺寸调整 |
| 40 | CLIPVisionEncode | CLIP Vision 编码 |
| 41 | CLIPVisionLoader | clip_vision_h.safetensors |

## smoothMix 双模型结构

```
High UNET(11) → SD3 shift(12) → SageAttn(8) → TorchPatch(15) → KSampler(30: steps 0→3)
                                                                           ↓
LoadImage(37) → Resize(39) → WanI2V(25) ← CLIP(28)←PrimitiveString(36)
                                   ↓
Low UNET(9) → SD3 shift(10) → SageAttn(5) → TorchPatch(6) → KSampler(1: steps 3→10000)
                                   ↓
                          cleanGpu(26) → VAEDecode(22) → ImageScaleBy(27) → cleanGpu(29)
                                                                              ↓
                                                                     VHS_VideoCombine(21: save=True)
```

## RIFE 绕过

**已默认绕过** — 节点 21 的 `images` 连接到 [29]（ImageScaleBy 输出），不是 RIFE 输出。
无需额外修改。OLD 脚本里 `prompt["21"]["inputs"]["images"] = ["29", 0]` 是多余的（本来就是 [29]）。

## 帧数计算公式

- 帧数 = 时长(秒) × 16fps，向上取整到最近的 ≈.0625 边界
- 5s → 81帧, 4s → 65帧, 3s → 49帧, 6s → 97帧
- ImpactInt(17) 和 PrimitiveStringMultiline(36).value 都需要同步修改

## 提交模式

```python
# 1. 上传源图到 ComfyUI input/
scp source.png host:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/input/
# 2. 修改工作流参数 → JSON
# 3. SCP workflow JSON 到 Windows
# 4. SSH curl 提交
ssh host "curl -s -X POST http://127.0.0.1:8188/prompt -H 'Content-Type: application/json' -d @D:/workflow.json"
# 5. 轮询 /history 检查完成
# 6. SCP 下载 outputs (gifs: mp4 视频)
```

## 负面提示词模板

针对 smoothMix 泳装污染的加固版：
```
色调艳丽，过曝，静态，细节模糊不清，...（原有负面词）
, no woman, no girl, no female, no swimsuit, no bikini, no young woman, no lady, 
no adult female, no woman face, no female body
```
