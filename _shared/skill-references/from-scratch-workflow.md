# 从零生成漫剧工作流

当没有源视频、需要从故事创意开始全新创作时的管线。

---

## 第一阶段：快速故事版出片（已验证）

最快的出片路径：**Flux.2-Klein 生场景图 → ffmpeg 拼成故事版 → EdgeTTS 配音**

### Step 1: 生成场景图

每个镜头一张 Flux.2-Klein 图。使用 `run_workflow.py` 批量提交到 Windows ComfyUI：

```bash
cd ~/.hermes/skills/creative/comfyui
python3 scripts/run_workflow.py \
  --workflow /tmp/shot_01.json \
  --host http://192.168.178.104:8188 \
  --output-dir project/06-video
```

**Flux.2-Klein 工作流模板**（API 格式）：
- `FluxLoader` 节点：需要 `weight_dtype`, `clip_vision_name`, `style_model_name` 输入
- 环境镜头用 1280×720 宽屏，人物镜头用 1024×1024 方形
- 每个镜头的 prompt 中**必须包含风格锚定英文**

### Step 2: 拼接故事版

```bash
ffmpeg -y \
  -loop 1 -t DUR1 -i shot01.png \
  -loop 1 -t DUR2 -i shot02.png \
  ... \
  -filter_complex "[0:v]scale=1280:720...[v0]; [v0][v1]...concat=n=N:v=1:a=0" \
  -c:v libx264 -pix_fmt yuv420p -r 24 storyboard.mp4
```

### Step 3: EdgeTTS 配音

在 Pi5 上直接用 EdgeTTS（无需模型下载，即时生成）：

```bash
python3 -m edge_tts --voice zh-CN-YunxiNeural --text "台词" --write-media narr_01.mp3
```

双角色配音示例：男孩用 `zh-CN-YunxiNeural`，奶奶/女性用 `zh-CN-XiaoxiaoNeural`。

用 ffmpeg `adelay` + `amix` 将各段旁白精确放置到对应时间戳，然后合并到视频。

---

## 第二阶段：Wan 2.2 I2V 动画化（待验证）

将静态场景图升级为真正的动画。

### 模型

Windows 路径：`diffusion_models/wan/wan22-i2v-14b-fp8-high/low-scaled.safetensors`

### 工作流

需要从 ComfyUI blueprints 加载 `Image to Video (Wan 2.2)` 并导出 API 格式。
当前问题：MultiGPU 示例工作流过复杂，需在 Windows 本地 UI 中手动搭建简化版。

### BERNINI 不适用于从零生成

BERNINI 是视频人物替换工具（source video + reference face → replaced video），
不是静帧→视频动画工具。从零生成必须用 Wan I2V 或 LTX 2.3。

---

## ComfyUI 远程操作技巧

### 批量提交流程

```bash
# 使用 run_workflow.py 批量提交（异步后台模式）
for f in /tmp/shot_*.json; do
  python3 scripts/run_workflow.py \
    --workflow "$f" --host http://192.168.178.104:8188 \
    --output-dir project/06-video &
done
wait
```

### RTK 代理干扰

Pi5 上 `curl` 直连 Windows IP 可能被 RTK 拦截返回 schema。`run_workflow.py` 已内置处理。

### 并行处理

多个 Flux.2-Klein 任务可以在 ComfyUI 队列中排队自动串行执行。
每个 1024×1024 图约 10-12 秒（RTX 5090）。
