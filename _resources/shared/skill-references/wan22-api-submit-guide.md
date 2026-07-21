# Wan 2.2 I2V API 提交指南

基于 n8n 工作流 `eBw6NSL8ffSUNP3d`（单人视频-生成视频片段）的 32 节点 flat Wan 2.2 I2V 工作流，经 12 轮提交验证。

## 关键修改（从 UI 蓝图到 API 可提交）

### 1. 模型路径（必须复制）
UNETLoader 搜 `models/unet/`，不搜 `models/diffusion_models/`。
```powershell
copy D:\ComfyUI_Mie_2026_V8.0\ComfyUI\models\diffusion_models\wan\wan22-i2v-14b-fp8-*-scaled.safetensors ^
     D:\ComfyUI_Mie_2026_V8.0\ComfyUI\models\unet\
```

### 2. 防 OOM（关 RIFE）
```json
"21": {"inputs": {"images": ["29", 0]}},   // 绕过 RIFE，直接取 cleanup 输出
"21": {"inputs": {"frame_rate": 16.0}},      // fps 32→16
"24": {"inputs": {"value": "a+1"}},          // SimpleMath+ 不乘16
```

### 3. 帧数公式
`时长秒 × 16fps = 帧数`。节点 17 的 `value` 直接设为帧数。
| 时长 | 帧数 |
|:--:|:--:|
| 3s | 48 |
| 4s | 64 |
| 5s | 80 |
| 6s | 96 |

### 4. 模型选择
| 场景 | model_low | model_high | 
|------|-----------|------------|
| smoothMix（画质好） | smoothMixWan22I2VT2V_i2vLow | smoothMixWan22I2VT2V_i2vHigh |
| fp8 官方（安全） | wan22-i2v-14b-fp8-low-scaled | wan22-i2v-14b-fp8-high-scaled |

### 5. 提交命令
```bash
scp -q payload.json "liuyi@192.168.178.104:D:/tmp_wf.json"
ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H 'Content-Type: application/json' -d @D:/tmp_wf.json"
```

### 6. 泳装污染处理（终极方案：按镜头类型分工）

smoothMix 环境镜头必出泳装美女。**不要反复调试提示词**，直接按镜头类型分配模型：

| 镜头类型 | 用哪个 | 泳装风险 |
|---------|--------|:--:|
| 环境/空镜（街道、公园） | LTX 2.3 | 零风险 |
| 人物特写 | BERNINI | 零风险 |
| 人物中全景 | Wan smoothMix | 低（人物占比大） |

Wan smoothMix 只用于中全景人物镜头，且提示词必须加 `no other people, only the character, no woman, no swimsuit`。
