# ComfyUI API JSON 模板库

可直接 scp+curl 提交到 `192.168.178.104:8188`。

## 目录

| 目录 | 工作流 | 用途 |
|------|--------|------|
| `qwen-3ref/` | Qwen Image Edit 三参考 | 场景图生成（多角色+背景融合） |
| `wan22-gguf/` | Wan 2.2 GGUF 4步加速 | 图生视频 16fps |
| `flux-klein/` | Flux.2-Klein 文生图 | 人物/道具独立生成 |
| `ace-step/` | Ace-Step 1.5 | 背景音乐生成 |
| `index-tts2/` | IndexTTS2 声音克隆 | 角色配音 |

## 使用

```bash
# 1. 修改 payload JSON 中的图片/提示词/帧数
# 2. 上传参考图到 ComfyUI input/
# 3. 提交
scp payload.json liuyi@192.168.178.104:/D:/tmp/p.json
ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -d @D:\\tmp\\p.json"
```
