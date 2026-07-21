# 道具跨场景合成实战

## 问题

Flux 文生图无法保证同一个道具（眼镜、书包等）在多个镜头中外观一致。  
Flux img2img 在 denoise > 0.15 时会擦掉 PIL 贴上去的道具，替换为自己的想象版本。

## 两种方案

### 方案 A：PIL 直接合成（道具独立于人物，在地面/远处）

适用于：眼镜掉在地上、书包放在远处等不需要光影融合的镜头。

```python
from PIL import Image
import numpy as np

# 1. 裁剪道具参考图到 tight bounding box
ref = np.array(Image.open("R4_glasses.png").convert("RGBA"))
non_white = (ref[:,:,0] < 230) | (ref[:,:,1] < 230) | (ref[:,:,2] < 230)
rows = np.any(non_white, axis=1); cols = np.any(non_white, axis=0)
ymin, ymax = np.where(rows)[0][[0,-1]]
xmin, xmax = np.where(cols)[0][[0,-1]]
cropped = ref[ymin-20:ymax+20, xmin-20:xmax+20]

# 2. 白底透明化
white = (cropped[:,:,0] > 230) & (cropped[:,:,1] > 230) & (cropped[:,:,2] > 230)
cropped[white, 3] = 0
prop = Image.fromarray(cropped, "RGBA")

# 3. 缩放 + 旋转
scale = 280 / prop.size[0]  # 调整到场景中合适大小
new_w, new_h = int(prop.size[0]*scale), int(prop.size[1]*scale)
prop = prop.resize((new_w, new_h), Image.LANCZOS)
prop = prop.rotate(-20, expand=True, resample=Image.BICUBIC)

# 4. 粘贴到场景（不经过 Flux！）
scene = Image.open("ep01_shot03_v1.png").convert("RGBA")
scene.paste(prop, (px, py), prop)  # 第三参数为 mask
scene.convert("RGB").save("output.png")
```

**关键**：不需要 Flux img2img。直接 PIL 合成即可。

### 方案 B：干净底图 + Flux img2img 重生成（道具需光影融合）

适用于：道具靠近人物、需要自然融入场景光影的镜头。

```json
// Flux.2-Klein img2img 工作流
{
  "1": {"class_type": "LoadImage", "inputs": {"image": "clean_original.png"}},
  // ← 必须是未合成过的原始图！
  "4": {"class_type": "VAEEncode", "inputs": {"pixels": ["1", 0], "vae": ["12", 0]}},
  "9": {"class_type": "CLIPLoader", "inputs": {"clip_name": "Flux.2-Klein\\qwen_3_8b_fp8mixed.safetensors", "type": "flux2"}},
  "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["9", 0], "text": "same scene... gold-rimmed round eyeglasses with thin metal frame and transparent clear lenses on the ground..."}},
  "13": {"class_type": "UNETLoader", "inputs": {"unet_name": "Flux\\Flux.2-Klein\\flux-2-klein-9b-fp8.safetensors", "weight_dtype": "default"}},
  "14": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["10", 0], "latent": ["4", 0]}},
  "17": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["14", 0], "guidance": 3.5}},
  "19": {"class_type": "KSampler", "inputs": {
    "model": ["13", 0], "positive": ["17", 0], "negative": ["18", 0],
    "latent_image": ["4", 0], "seed": 42, "steps": 10,
    "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 0.45
  }},
  "12": {"class_type": "VAELoader", "inputs": {"vae_name": "Flux\\flux2-vae.safetensors"}},
  "20": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["12", 0]}},
  "21": {"class_type": "SaveImage", "inputs": {"images": ["20", 0], "filename_prefix": "output"}}
}
```

**关键参数**：
- `denoise`: 0.4-0.5（太低改不了道具，太高改变整个画面）
- `steps`: 8-10
- 底图必须是**干净的原始 Flux 输出**，不能有 PIL 合成残留

## 道具参考图预处理

Flux 生成的道具白底图常见问题：
1. **无 alpha 通道** — RGB only，需 `convert("RGBA")` 后手动设透明
2. **道具占比极小** — 如眼镜仅占 1280×1280 画面的 4.6%，裁剪到 bounding box 后才可用
3. **浅色薄框道具缩小后消失** — 金边眼镜缩到 180px 时镜框仅 1px 宽。保持 250-350px 可见性更好
4. **不要用 Flux img2img 融合 PIL 合成图** — 会擦掉道具。要么纯 PIL，要么纯 Flux

## 实战案例：Happy Children 眼镜

- **Shot 03**（眼镜在地上）：PIL 合成（方案 A），238×159 @ (450, 1000)，旋转 -20°
- **Shot 04**（奶奶特写，眼镜在地上）：干净原图 + Flux img2img denoise 0.45（方案 B）
- **Shot 08**（奶奶戴眼镜）：R2 不戴眼镜版 → img2img 描述"wearing gold-rimmed glasses"
