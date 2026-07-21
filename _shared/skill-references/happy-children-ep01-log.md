# Happy Children — 从零生成漫剧实操记录

第一集「上学的路上」经 5 轮迭代完成。

## 项目路径

```
/home/pi5/ai_cartoon/happy_children/
├── 00-style/style-anchor.md          ← 皮克斯风格锚定
├── 01-characters/character-design.md  ← 四人设定（Michael/Luke/Ella/王奶奶）
├── 01-characters/*_ref.png           ← Flux.2-Klein 生成的角色参考图
├── 02-storyboard/ep01-going-to-school.md ← 12镜头分镜表（v3：扶起→送回家→上学）
├── 03-source/                         ← 旧素材（tmp.mp4等，已不用）
├── 04-voices/                         ← IndexTTS2 克隆声音样本
├── 06-video/ep01_shot*.png           ← Flux.2-Klein 12张场景图
├── 06-video/ep01_shot*_anim.mp4      ← Wan 2.2 I2V 生成的各镜头视频
└── 07-final/
    ├── ep01_shot*_michael.wav        ← 6段角色对白（IndexTTS2 克隆）
    ├── bgm_ep01.flac                  ← Ace-Step 1.5 BGM（77秒）
    └── ep01_v5.mp4                    ← 最终拼接版（51秒，28MB）
```

## 角色设定（更新为英文名）

- **Michael** 5岁：红色卫衣、翘发、小麦肤色
- **Luke** 4岁：黄色T恤、酒窝、刘海
- **Ella** 2岁：粉色连衣裙、双马尾、兔子玩偶
- **王奶奶** 80岁：紫色披肩、眼镜、轮椅

## 完整管线（v5）

```
Phase 1: Flux.2-Klein → 角色参考图（4张）
Phase 2: Flux.2-Klein → 场景静帧（12张）
Phase 3: IndexTTS2 声音克隆 → 6段对白 WAV
Phase 4: Ace-Step 1.5 → BGM FLAC（77秒）
Phase 5: Wan 2.2 I2V smoothMix → 12段动画（816帧≈51秒）
Phase 6: ffmpeg concat + adelay/amix → 最终视频
Phase 7: scp → Synology NAS
```

## 模型分工（5轮迭代经验）

| 镜头类型 | 正确模型 | 错误尝试 |
|---------|---------|---------|
| 环境/空镜（01/03/09/12） | LTX 2.3 | smoothMix → 泳装美女 |
| 人物特写（04/08/10） | BERNINI | smoothMix → 人脸漂移 |
| 人物中全景（02/05/06/07/11） | Wan 2.2 smoothMix | fp8 → 画质软 |

## 关键教训

1. **smoothMix ≠ 万能**：环境镜头绝对不能用了，泳装污染致命
2. **帧数必须按公式**：时长秒×16fps，不能随意设
3. **分镜剧本会改**：跑一轮用户可能改剧情，重新确认再跑
4. **配音时间轴**：adaelay 值 = 之前所有镜头累计时长（毫秒）
5. **关 RIFE 省显存**：双采样+smoothMix+RIFE→OOM，关RIFE即可

## API 提交模式

```bash
# 批量提交（12镜头一起）
python3 batch_submit.py
# 后台监控+自动下载
bash monitor_and_download.sh (background=true, notify_on_complete=true)
# 拼接+配音+BGM
ffmpeg -i [12段视频] -i [6段对白] -i [bgm] -filter_complex "concat+adelay+amix" final.mp4
# 归档
scp -O final.mp4 TopOnSky@192.168.178.20:/volume1/photo/n8n_workflow/output/happy_children/
```
