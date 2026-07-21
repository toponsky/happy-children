# PIL 道具合成 + Flux 融合技术

## 问题

Flux 文生图只能"描述"道具外观，无法把参考图（如 R4 眼镜）精确复制到场景中。img2img 也只能基于文字修改，不能"粘贴"特定对象。

**症状**：同一道具出现在多张源图时（如眼镜在地上→被捡起→戴在脸上），每张图的道具都长得不一样。

## 解决方案：两步法

### Step 1: PIL 裁剪 + 去背景 + 粘贴

Flux 生成的道具参考图通常是**白底孤立**（1280×1280，RGB 无 alpha 通道），道具只占画面 ~5%。

```python
from PIL import Image
import numpy as np

# 1. 加载道具参考图，找道具区域（非白色像素）
r4 = Image.open("R4_glasses.png").convert("RGBA")
arr = np.array(r4)

non_white = (arr[:,:,0] < 230) | (arr[:,:,1] < 230) | (arr[:,:,2] < 230)
rows = np.any(non_white, axis=1)
cols = np.any(non_white, axis=0)
ymin, ymax = np.where(rows)[0][[0, -1]]
xmin, xmax = np.where(cols)[0][[0, -1]]

# 2. 裁剪 + 加 padding，去掉白色背景
pad = 20
cropped = arr[ymin-pad:ymax+pad, xmin-pad:xmax+pad]
white = (cropped[:,:,0] > 230) & (cropped[:,:,1] > 230) & (cropped[:,:,2] > 230)
cropped[white, 3] = 0  # 白色变透明
glasses = Image.fromarray(cropped, "RGBA")

# 3. 缩放（场景中道具应占约 200-300px）
scale = 250 / glasses.size[0]
new_w, new_h = int(glasses.size[0]*scale), int(glasses.size[1]*scale)
glasses = glasses.resize((new_w, new_h), Image.LANCZOS)

# 4. 旋转 + 定位粘贴
glasses = glasses.rotate(-15, expand=True, resample=Image.BICUBIC)
scene = Image.open("ep01_shot03_v1.png").convert("RGBA")
px = scene.size[0] // 2 - glasses.size[0] // 2 + 80  # 水平居中偏右
py = scene.size[1] - glasses.size[1] - 280           # 垂直靠下
scene.paste(glasses, (px, py), glasses)

# 5. 保存合成图
scene.convert("RGB").save("shot03_composited.png")
```

### Step 2: Flux img2img 轻量融合

合成图的边缘可能有白边/锯齿，用低 denoise img2img 自然融合：

**API 工作流模板**：

```json
{
  "1": {"class_type": "LoadImage", "inputs": {"image": "shot03_composited.png"}},
  "4": {"class_type": "VAEEncode", "inputs": {"pixels": ["1", 0], "vae": ["12", 0]}},
  "9": {"class_type": "CLIPLoader", "inputs": {"clip_name": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors", "type": "flux2"}},
  "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["9", 0], "text": "same scene, keep everything exactly the same, just blend the composited glasses naturally into the scene. High quality, photorealistic."}},
  "11": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["9", 0], "text": "changing the woman, changing composition, different glasses style, thick frame, plastic frame, blurry, low quality, distorted"}},
  "13": {"class_type": "UNETLoader", "inputs": {"unet_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors", "weight_dtype": "default"}},
  "14": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["10", 0], "latent": ["4", 0]}},
  "15": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["11", 0], "latent": ["4", 0]}},
  "17": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["14", 0], "guidance": 3.5}},
  "18": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["15", 0], "guidance": 3.5}},
  "19": {"class_type": "KSampler", "inputs": {"model": ["13", 0], "positive": ["17", 0], "negative": ["18", 0], "latent_image": ["4", 0], "seed": 42, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 0.25}},
  "12": {"class_type": "VAELoader", "inputs": {"vae_name": "Flux\\flux2-vae.safetensors"}},
  "20": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["12", 0]}},
  "21": {"class_type": "SaveImage", "inputs": {"images": ["20", 0], "filename_prefix": "shot03_final"}}
}
```

**关键参数**：
- `denoise`: **0.2-0.3** — 只融合边缘，不改画面主体
- `steps`: **6** — 少量步数足够
- 负面提示词必须包含 `"different glasses style, thick frame, plastic frame"` 防止 Flux 把道具样式改掉

## Pitfalls

1. **道具参考图是 RGB 没有 alpha** — Flux 输出默认无透明通道。`convert("RGBA")` 后再做白色阈值去除。已验证 R4_glasses.png 为 (1280,1280,3) 无 alpha。
2. **道具在白底图里占比极小**（可能 <5%）— 必须**先裁剪再粘贴**，直接整图缩放会导致道具不可见。实战：R4 眼镜仅 75k 非白像素 / 1.6M 总像素（4.6%）。裁剪后得到 (1112,453) 的有效区域。
3. **denoise 太低（<0.15）可能无效果，太高（>0.4）会改变道具样式** — 最佳 0.2-0.3。
4. **旋转后 `expand=True` 会增加画布尺寸** — 先旋转再定位，或在粘贴前调整。
5. **在 Pi5 上跑 PIL** 需要 `pip install Pillow` — 系统默认可能没装。

## 迭代定位工作流（实战验证）

道具合成**无法一步到位**——需要多轮调位置/大小。预期流程：

```
1. 粗略合成（估算位置 + 默认大小）→ 发给用户确认
2. 用户反馈："左移 100px，下移 20px，再小一点"
3. 调参数重新合成 → 再次确认
4. 用户确认位置/大小 OK → 上传 ComfyUI 做 img2img 融合
```

**交互模式**：用户反馈精确像素级别调整（"左移200px，下移100px"），直接在 Python 中改 `px`/`py`/`scale` 参数，<30秒重新生成合成图，立即发送确认。

**只有在用户确认位置 OK 之后**，才进入 ComfyUI img2img 融合步骤。避免在位置还没定好时就浪费 GPU 时间跑融合。
