# Wan 2.2 I2V API 提交失败记录

## 背景

尝试通过 ComfyUI REST API (`POST /prompt`) 远程提交 `Image to Video (Wan 2.2)` 蓝图工作流，批量将 12 张场景图转为视频片段。

## 失败根因

蓝图工作流使用 **子图格式** (`definitions/subgraphs`)，class_type 是 UUID：
```
"class_type": "296b573f-1e7d-43df-a2df-925fe5e17063"
```

ComfyUI 的 `/prompt` 端点不认识这个 UUID，返回 `missing_node_type` 错误。

## 尝试过的方案

| 方案 | 方法 | 结果 |
|------|------|------|
| A | 直接提交 subgraph UUID + inputs | `missing_node_type` HTTP 400 |
| B | A + 包含 `definitions` 在 payload | 同样的 `missing_node_type` |
| C | `convert_to_api.py` 转换编辑器格式 | 参数映射错乱（unet_name=null, clip_name=模型路径） |

方案 C 的转换问题：`proxyWidgets` 中混入了 node 86 的 `noise_seed` / `control_after_generate`，导致 `widgets_values` 索引偏移。手写 API payload 也无法绕过 UUID 问题。

## 结论

蓝图/子图工作流 **只能在 ComfyUI Web UI 里手动加载运行**。如需 API 自动化，必须用扁平节点工作流（如 LTX Director、BERNINI、Flux.2-Klein 等）。

## 可用的 API 替代方案

| 工作流 | 节点格式 | 用途 |
|--------|---------|------|
| LTX导演台2.0【Director】 | 扁平 | 多图关键帧→视频 |
| 智能多参-LTX2.3导演台 | 扁平 | 音频+视频管线 |
| 超强bernini-14b满血版 | 扁平 | 人物镜头换脸 |
| Flux.2-Klein 文生图 | 扁平 | 场景图/人物图生成 |

## Wan 2.2 I2V 模型路径映射

工作流预期名称 → 实际磁盘文件名（Windows RTX 5090）：

| 蓝图默认名 | 实际路径 |
|-----------|---------|
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | `wan/wan22-i2v-14b-fp8-high-scaled.safetensors` |
| `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `wan/wan22-i2v-14b-fp8-low-scaled.safetensors` |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `Wan/umt5-xxl-enc-fp8_e4m3fn.safetensors` |
| `wan_2.1_vae.safetensors` | `wan_2.1_vae.safetensors` (不变) |
| Wan 2.2 LoRA（两个） | 不存在——只能用 `None` |

模型目录：`D:\ComfyUI_Mie_2026_V8.0\ComfyUI\models\diffusion_models\`

## 成功提交 ComfyUI API 的正确方式

避免 Pi5 的 RTK 代理拦截：通过 SSH 到 Windows localhost 提交：

```bash
scp payload.json "liuyi@192.168.178.104:D:\\tmp.json"
ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H 'Content-Type: application/json' -d @D:\\tmp.json"
```
