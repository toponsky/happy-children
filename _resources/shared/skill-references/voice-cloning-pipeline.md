# 声音克隆管线

漫剧角色声音克隆有三种方式，按推荐顺序：

## 方式 1：ComfyUI IndexTTS2 节点（推荐，与视频管线统一）

ComfyUI 已安装 `ComfyUI-IndexTTS2` 插件（`D:\ComfyUI_Mie_2026_V8.0\ComfyUI\custom_nodes\ComfyUI-IndexTTS2\`），提供五个节点：

| 节点 | 功能 |
|------|------|
| `IndexTTS2Simple` | 文本→语音，输入参考音频(AUDIO)+文本(STRING)，输出 AUDIO |
| `IndexTTS2Advanced` | 高级参数控制 |
| `IndexTTS2EmotionFromText` | 从文本提取情感向量 |
| `IndexTTS2EmotionVector` | 情感向量控制 |
| `IndexTTS2SaveAudio` | 保存音频到文件 |

### Whisper + IndexTTS2 自动换声工作流

已创建 `whisper_indextts2_voice_clone.json`，流程：

```
VHS_LoadVideo → Apply Whisper(转录) → IndexTTS2Simple(克隆) → VHS_VideoCombine
                    ↓ text(STRING)    ↑ 参考音频(上传)
```

**已验证**：Apply Whisper 的 `text` 输出（STRING）与 IndexTTS2Simple 的 `text` 输入（STRING）类型匹配，可直连。

## 方式 2：IndexTTS2 Python API（批量/脚本）

IndexTTS2 独立安装在 `D:\index-tts2.0\`，通过 SSH 远程调用。

```python
import sys; sys.path.insert(0, 'indextts')
from indextts.infer_v2 import IndexTTS2

tts = IndexTTS2(model_dir='checkpoints', cfg_path='checkpoints/config.yaml', use_fp16=True)
tts.gr_progress = lambda *a, **kw: None  # 必须！否则 TypeError
tts.infer(spk_audio_prompt='voices/ref.wav', text='台词', output_path='voices/output.wav')
```

详见 `index-tts2-api` skill。

## 方式 3：OpenAI TTS 生成参考 → IndexTTS2 克隆

用于初次建立角色音色：

```
OpenAI TTS(gpt-4o-mini-tts) → 参考音频 → ffmpeg转wav → scp到Windows → IndexTTS2克隆
```

推荐音色分配：
- Michael (5岁男孩): `nova`
- Luke (4岁男孩): `echo`
- Ella (2岁女孩): `shimmer`
- 王奶奶 (80岁): `alloy`

## IndexTTS2 服务管理

- **Windows 计划任务**: `\IndexTTS-WebUI`，触发条件「用户登录时」
- **启动命令**: `D:\index-tts2.0\start_webui.bat`
- **Python**: `D:\index-tts2.0\myvenv\python.exe` (Python 3.10.11)
- **端口**: 7860 (Gradio WebUI)
- **模型版本**: 2.0
- **检查状态**: `netstat -an | findstr :7860`（需 LISTENING）
- **首次加载**: 启动后 30-60 秒模型加载，期间端口可能未就绪
