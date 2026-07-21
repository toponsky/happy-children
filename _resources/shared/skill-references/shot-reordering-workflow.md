# 分镜后期重组工作流

用户可能在视频生成后要求调换镜头顺序、删除某镜、新增台词。本参考覆盖操作流程。

## 标准流程

### Step 1: 确认新镜头顺序
列出新的视频文件列表（不改文件名，改 ffmpeg 输入顺序）。不要重命名视频文件——fp 计算的原始文件不会变。

### Step 2: ffprobe 实测每个视频时长
```
for f in 06-video/ep01_shot*_anim_v1.mp4; do
  d=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$f")
  printf "%-35s %7.2fs\n" "$f" "$d"
done
```
⚠️ 理论帧数/fps 不准确，必须以实测值为准。

### Step 3: 按新顺序重新计算累计 adelay
```
累计时间数组：每镜的adelay = 前面所有镜头的实测时长总和（毫秒）
```

### Step 4: 新增台词用 IndexTTS2 生成
使用真实人声参考音色：
- `成熟女声.flac` → 王奶奶（老年女性）
- `可爱儿童男声.flac` → Michael/Luke（5-4岁男孩）

直接 Python 调用：
```python
from indextts.infer_v2 import IndexTTS2
tts = IndexTTS2(model_dir='checkpoints', cfg_path='checkpoints/config.yaml', use_fp16=True)
tts.gr_progress = lambda *a, **kw: None
tts.infer(spk_audio_prompt=r'D:\...\成熟女声.flac', text='台词', output_path='voices/output.wav')
```

### Step 5: 重跑 ffmpeg
- concat=n 匹配实际镜头数
- amix=N 匹配实际音频轨道数
- 每个音频的 adelay 跟着它在 ffmpeg 输入列表的位置走
- -shortest 让 BGM 自动截断

### Step 6: 上传 NAS + 通知用户审查

## 复杂重组案例：EP01 最终版

### 操作记录
1. **调换**: shot02 ↔ shot03（视频顺序互换）
2. **删除**: 砍掉 shot06
3. **新增台词**: 王奶奶「够不到啊，真的是老了」→ 用 IndexTTS2 生成，放在新 shot02 位置
4. **台词移位**: Michael 内心「咦？」从原 shot05 移到新 shot03

### 最终 8 镜顺序
```
01(4.81s) → 03(4.81s) → 02(3.81s) → 05(3.81s) → 07(3.81s) → 08(3.81s) → 09(3.81s) → 10(4.81s)
总长: 33.48s
```

### 配音 adelay
```
shot02(原03): 4810ms → 王奶奶「够不到啊」
shot03(原02): 9620ms → Michael内心「咦？」
shot07:      17240ms → Michael「奶奶我来帮您」
shot08:      21050ms → 王奶奶「谢谢你」
shot09:      24860ms → Michael「奶奶再见」
shot10:      28670ms → 旁白
```

### ffmpeg 命令模板
```bash
ffmpeg -y \
  -i $VD/ep01_shot01_anim_v1.mp4 \
  -i $VD/ep01_shot03_anim_v1.mp4 \
  -i $VD/ep01_shot02_anim_v1.mp4 \
  ... \
  -i $AD/ep01_shot03_granny.wav \
  -i $AD/ep01_shot05_michael.wav \
  ... \
  -i $AD/bgm_ep01.flac \
  -filter_complex "
    [0:v][1:v][2:v]...[N:v]concat=n=8:v=1:a=0[v];
    [V0:a]adelay=4810|4810[a2];
    [V1:a]adelay=9620|9620[a3];
    ...
    [a2][a3]...[aN]amix=6:normalize=0[voices];
    [BGM:a]volume=0.25[bgm];
    [voices][bgm]amix=2:normalize=0[a]
  " -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -ar 44100 -shortest \
  $AD/ep01_v8.mp4
```

### ⚠️ 陷阱
- **「调换配音」≠ 调换视频**：用户说「调换 shotX 和 shotY 的配音」时，只改 ffmpeg 音频输入文件顺序，视频 concat 不变
- **shot 编号有间隙时**（如跳过 shot04），必须用显式映射，不能依赖 enumerate
- **每次重组后立即通知用户审查**，不要假设一次过
