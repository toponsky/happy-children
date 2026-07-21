---
name: comic-drama-pipeline
description: AI漫剧制作管线 — Flux.2-Klein + Qwen三参考 + Wan 2.2 GGUF + IndexTTS2 完整生成工作流
triggers:
  - 漫剧
  - 视频生成
  - 分镜
  - 风格锚定
  - 人物设计
  - 配音
  - 声音克隆
  - 场景图
  - 源图
---

# AI漫剧制作管线

基于 ComfyUI 技术栈的完整漫剧生成工作流。从零生成动画片。

## 七步流程总览 🎬

```mermaid
graph LR
    A[1.剧本] --> B[2.分镜]
    B --> C[3.源图]
    C -->|审图| D[4.视频]
    D --> E[5.配音]
    E --> F[6.BGM]
    F --> G[7.拼接+上传]
```

| 步骤 | 环节 | 工具 | 产出 | 审查 |
|:--:|------|------|------|:--:|
| 1 | **剧本** | 手写 + AI 可行性评估 | 分镜表 + 对白 | 👤 |
| 2 | **分镜** | 按角色拆镜头 | 每镜景别/时长/动作 | 👤 |
| 3 | **源图** | Flux 人物+道具 / Qwen 三参考 场景图 | 1280×720 PNG | 👤 ⚠️ |
| 4 | **视频** | Wan 2.2 GGUF I2V 4步加速 | 16fps MP4 | 👤 |
| 5 | **配音** | IndexTTS2（回退 EdgeTTS） | 每镜台词 WAV/MP3 | — |
| 6 | **BGM** | Ace-Step 1.5 柔和背景音乐 | 30s MP3 | — |
| 7 | **拼接上传** | ffmpeg concat + adelay + amix → NAS | 成品 MP4 | 👤 |

**⚠️ 关键原则**：
- 第 3 步源图生成后**必须等用户确认**再跑 Wan（源图错=视频全浪费）
- 第 5 步 IndexTTS2 节点常挂 → 直接切 EdgeTTS，不浪费时间排查
- 第 3 步**先检查已有资产**，能复用的角色/背景不重复生成
- Wan 提示词**不要用 ChatGPT 增强**（实测无效），写清楚动作即可

**参考仓库**: `/home/pi5/YubAI-DramaFlow/`

**⚠️ 每次做漫剧必须先加载本 skill（`skill_view comic-drama-pipeline`），再加载 `comfyui` skill。图片质量检查时加载 `qwen3-vl-local` skill（本地 Qwen3VL 替代云 Vision）。按五阶段流程走，不跳步。**

## 核心工具链（当前真实管线）

| 环节 | 工具 | 工作流文件 | 规则 |
|------|------|-----------|------|
| **人物/道具** | Flux.2-Klein 文生图 | `我的工作流/Flux.2-Klein-文生图.json` | 独立角色、道具用 Flux |
| **场景图** | Qwen-Image-Edit 三图参考 | `我的工作流/Qwan-Image-三图参考图生图.json` | 多角色+背景场景用三参考 |
| **视频** | Wan 2.2 GGUF I2V 4步加速 | `阿硕进阶工作流/031)Wan2.2全系列/` GGUF+LoRA | 16fps，双KSamplerAdvanced(0→2, 2→10000) |
| **配音** | IndexTTS2 声音克隆 | `阿硕进阶工作流/010)TTS文本转语音/Index-TTS2_自定义音色声音克隆.json` | 真实人声参考，AI合成音不行 |
| **质检** | Qwen3VL 本地视觉 | `qwen3-vl-local` skill（llama-server 或 ComfyUI） | 源图/视频逐帧审阅；云 Vision API 不可靠时用本地替代 |
| **合并** | ffmpeg（Pi5 本地） | 命令行 | concat + adelay + amix + BGM |

**⚠️ 旧管线（BERNINI + LTX 2.3 + smoothMix + FaceDetailer）已废弃。翻拍换脸模式不常用，见 `references/legacy-bernini-ltx.md`。**

## 源图生成决策

```
需要生成什么？
├─ 人物参考图（正面照）  → Flux.2-Klein
├─ 道具参考图（白底孤立）→ Flux.2-Klein  
├─ 场景图（多角色互动）  → Qwen 三图参考
│   ├─ 参考图1 = 角色A
│   ├─ 参考图2 = 角色B（或道具）
│   └─ 参考图3 = 背景
└─ 场景图（单角色简单）  → Flux.2-Klein 也可
```

---

## 项目管理：YubAI-DramaFlow 五阶段流程

**每个新项目必须按这五阶段走，每阶段结束自检。不要跳过。**

| 阶段 | 名称 | 任务 | 输出 | 自检 | 审查 |
|------|------|------|------|------|------|
| 1 | **故事层** | 创意→剧本 | 故事大纲 + 剧本 | AI可行性评估（必做！） | 👤 等用户确认剧本 |
| 2 | **风格层** | 定义视觉风格 | 风格锚定提示词 + 参考图 | 风格统一验收 | （沿用已有项目可跳过） |
| 3 | **设计层** | 人物+道具+场景 | 参考图 + 提示词库 | 资产库验收 | （新项目才需） |
| 4 | **分镜层** | 剧本→分镜表 | 分镜表 + 台词 | 每镜画面描述+时长 | 👤 等用户确认分镜 |
| 5 | **视频层** | 生成+拼接+配音 | 最终成片 | 成片质量验收 | 👤 每步源图/视频/配音输出后等审查

**模板位置**: `/home/pi5/YubAI-DramaFlow/templates/`

| 模板 | 用途 | 阶段 |
|------|------|------|
| `AI可行性评估模板.md` | 评估剧本 AI 生成难度 | 阶段1 |
| `故事大纲模板.md` | 故事结构 | 阶段1 |
| `剧本格式模板.md` | 标准剧本格式 | 阶段1 |
| `风格定义模板.md` | 视觉风格锚定 | 阶段2 |
| `人物设计模板.md` | 角色外观设计 | 阶段3 |
| `场景设计模板.md` | 场景设计 | 阶段3 |
| `分镜表模板.md` | 镜头分镜 | 阶段4 |

### 阶段1 必做：AI 可行性评估 ⚠️

**进入设计前必须完成**。评估维度：

| 维度 | 检查项 | 达标线 |
|------|--------|--------|
| 人物 | 主角单人镜头占比 | >60% |
| 场景 | 场景数量 | 5分短剧≤5个 |
| 动作 | 无复杂动作 | 打斗/舞蹈=🔴 |
| 运镜 | 固定镜头优先 | 快速运镜=慎用 |

**综合评分**: 4-5分🟢通过 / 2-3分🟡需优化 / <2分🔴重新设计

**⚠️ 故事从简原则**：用户偏好极简剧情。能用一个人物讲完绝不用两个；能用三个镜头绝不用五个。AI漫剧的核心是角色对镜头独白/互动，不是复杂叙事。先写极简版，用户如果要加再加。

### 阶段进度追踪

每个项目在 `02-storyboard/` 下创建进度文件：

```markdown
## 项目: Happy Children EP01
- [x] 阶段1: 故事层 — 剧本完成
- [x] 阶段2: 风格层 — Pixar 3D, 暖色调
- [x] 阶段3: 设计层 — R1 Michael, R2 王奶奶, R9 Shane
- [x] 阶段4: 分镜层 — 12镜, 约60秒
- [ ] 阶段5: 视频层 — Shot 01-12 视频生成 + 配音 + 拼接
```

```bash
mkdir -p project/{_shared/{characters,backgrounds,voices},ep01/{script,prompts,source,video,voice,bgm,final},ep02/{...}}
```

- `_shared/characters/` — 跨集复用角色参考图（R1_Michael.png 等）
- `_shared/backgrounds/` — 跨集复用背景图（R7_street_bg.png 等）
- `_shared/voices/` — 声音克隆参考音频
- `epXX/prompts/` — **每集提示词归档**（`source.md` + `video.md`），避免散落在 /tmp payload JSON 中
- `epXX/source/` — Qwen 三参考/Flux 源图
- `epXX/video/` — Wan I2V 生成的动画片段
- `epXX/voice/` — 配音 WAV/MP3
- `epXX/bgm/` — Ace-Step BGM
- `epXX/final/` — ffmpeg 合成成品 + 上传 NAS

**⚠️ 新集开始先检查 `_shared/`**：角色/背景/参考音频已存在就复用，不要重复生成。

## 项目目录（Happy Children 项目）

当前项目目录: `/home/pi5/ai_cartoon/happy_children/`

```
happy_children/
├── _shared/
│   ├── characters/    R1-Michael  R2-王奶奶  R3-眼镜  R4-眼镜  R5-轮椅  R6-书包  R9-Shane  R10-Luke
│   ├── backgrounds/   R7_street_bg.png
│   └── voices/        各角色声音克隆参考音频 (21 files)
├── ep01/
│   ├── script.md      EP01 剧本+分镜
│   ├── workflows/     9个 Wan API JSON payload
│   ├── source/        10张 Qwen/Flux 源图
│   ├── video/         10段 Wan I2V 动画
│   ├── voice/         旁白 MP3
│   ├── bgm/           Ace-Step BGM
│   └── final/         14版成品 MP4
├── ep02/
│   ├── script.md      EP02 剧本+分镜
│   ├── prompts/       source.md + video.md 提示词归档
│   ├── workflows/     7个 API JSON (Qwen+Wan+BGM)
│   ├── source/        9张源图（含旧版迭代）
│   ├── video/         5段动画（含旧版迭代）
│   ├── voice/         Shane配音 WAV/MP3
│   ├── bgm/           Ace-Step BGM
│   └── final/         成品 MP4
└── scripts/           提交/监控脚本
```

NAS: `TopOnSky@192.168.178.20:/volume1/photo/n8n_workflow/output/happy_children/`

**新集模板**: 
```bash
EP=ep03
mkdir -p $EP/{prompts,workflows,source,video,voice,bgm,final}
```

---

## 提示词工场：按模型填模板 🌟

**核心原则：每个模型有专属语法。不要跨模型混用。**

### 全局风格锚定（所有 prompt 第一行必须包含）

```
Pixar-style 3D animation, warm morning sunlight, vibrant colors, 1280x720, high quality
```

### Flux.2-Klein 文生图提示词

**语言**: English（中文理解差）
**结构**: `[风格锚定] + [主体描述] + [服装CAPS] + [光线/氛围] + [镜头景别]`
**Negative**: `no woman, no girl, no female, no swimsuit, blurred, low quality, bad anatomy, watermark, text`

| 场景 | 模板 |
|------|------|
| 人物正面 | `Pixar-style 3D animation, [角色描述], facing camera, neutral expression, BRIGHT RED HOODIE, blue jeans, even lighting, high quality character reference, 1280x1664` |
| 人物背面 | `Pixar-style 3D animation, back view of [角色描述], his back facing the camera, BRIGHT RED HOODIE, blue jeans, [环境], warm morning light, 1280x720` |
| 道具白底 | `Pixar-style 3D animation, isolated [道具] on pure white background, product photography, studio lighting, centered, 1280x1280` |
| 远景人物 | `Pixar-style 3D animation, wide shot, [角色] is a small distant figure in the center of [环境], [光线], 1280x720` |

**⚠️ Flux 专属坑**:
- 颜色用大写锁定：`BRIGHT RED HOODIE`
- close-up→面部过大，用 `medium shot showing upper body, natural composition, not too tight`
- 背对镜头必须在正面 prompt 写 `back view, back facing camera`，负面加 `facing camera, front view`
- steps≥25，guidance=3.5

### Qwen-Image-Edit 2511 三图参考提示词

**语言**: 中文（效果更好）
**结构**: `图像3的[背景]上，图像1中的[角色A][位置][动作]。图像2中的[角色B][位置][状态]。保持图像1[角色A]面部和[服装]。保持图像2[角色B]面部、衣服和[特征]。完全保留图像3[背景]。`
**参数**: steps=8, cfg=1.0, denoise=1.0 (搭配 Lightning 4-step LoRA)

| 场景 | 模板 |
|------|------|
| 两人物+背景 | `图像3的[地点]上，图像1中的[角色A][动作/姿态]，[位置描述]。图像2中的[角色B][状态]，[位置描述]。[角色A]不在[错误位置]。保持图像1[角色A]面部和[服装]。保持图像2[角色B]面部、衣服和[特征]。完全保留图像3[背景]。` |
| 远景单人 | `图像3的[地点]远景，图像1中的[角色]站在远处，小小的身影，[朝向]。这是远景镜头，[角色]在画面中占比很小。保持图像1[角色]的面部和[服装]。完全保留图像3[背景]。` |
| 单人挺直站姿 | `图像3的[地点]上，图像1中的[角色]笔直地站在[位置]，[朝向]。腰背挺直，站姿端正挺拔，双肩平齐。身体没有前倾没有弯腰。保持图像1[角色]面部和[服装]。完全保留图像3[背景]。` |
| 背对镜头 | `图像3的[地点]上，图像1中的[角色]背对镜头，[动作]。保持图像1[角色]面部和[服装]。完全保留图像3[背景]。` |

**⚠️ Qwen 专属坑**:
- 远景必须写 "站在远处""小小的身影""远景镜头"，否则人物太大
- 站姿必须写 "腰背挺直，身体没有前倾没有弯腰"
- 显式否定错误位置："[角色]不在[错误位置]"
- 三句"保持"收尾：保持图1+保持图2+完全保留图3

### Wan 2.2 GGUF I2V 图生视频提示词

**语言**: English
**结构**: `[风格锚定] + [人物]在源图中的[动作]，持续[描述运动]。No other people, only the character.`
**参数**: 16fps, 双KSamplerAdvanced(start=0→2/2→10000), cfg=1.0

| 场景 | 模板 |
|------|------|
| 走路 | `Pixar-style 3D animation, [角色] walking toward the camera on [环境]. Smooth confident stride, arms swinging gently in sync with each step, posture upright, walking in a straight line. No limp, no stagger. Warm morning sunlight. No other people.` |
| 站立说话 | `Pixar-style 3D animation, [角色] standing on [环境], talking with a warm smile, slight natural head movement. His posture remains straight and confident throughout. Warm sunlight. No other people.` |
| 奔跑 | `Pixar-style 3D animation, [角色] seen from behind running toward [目标] in the distance on [环境]. Natural running motion, arms pumping, smooth stride. Warm morning sunlight. No other people.` |
| 敬礼 | `Pixar-style 3D animation, [角色] raising right hand to salute, smooth arm movement, standing at attention on [环境]. Posture straight and confident throughout. Warm sunlight. No other people.` |

**⚠️ Wan 专属坑**:
- 走路 80f 不够→112f（7秒），否则一瘸一拐
- 视频时长≠帧数/fps，拼接前必须 ffprobe
- GGUF 干净无泳装，但也别写 "woman/female" 相关
- **不要用 ChatGPT/GPT 增强 Wan prompt** 🌟🌟 — 实测 GPT 版效果不如手写版。Wan I2V 是图生视频，源图决定 80%+ 视觉内容，prompt 只管运动描述。GPT 加的视觉细节（光照、阴影、纹理、运镜）Wan 改不了，甚至可能误导（如 "camera zooms in" — Wan 镜头固定）。写清楚动作即可：smooth stride, posture straight, no limp, no swaying。

### 提示词检查清单

生成前逐条对照：

- [ ] 风格锚定在第一句
- [ ] 服装颜色 CAPS（Flux）/ 显式描述（Qwen）
- [ ] 背对镜头→正面 prompt 写 "back view" 或 "背对镜头"
- [ ] 远景→写 "小小的身影" 或 "small distant figure"
- [ ] 站姿→写 "腰背挺直""posture straight"
- [ ] 走路→写 "smooth stride, no limp, no stagger"
- [ ] Negative 包含 `no woman, no female, no swimsuit`
- [ ] Prompt 语言匹配模型（Flux/Wan→English, Qwen→中文）

**所有镜头统一用 Wan 2.2 GGUF I2V**，不区分人物/环境镜头。

| 参数 | 值 | 说明 |
|------|-----|------|
| 模型 | `Wan2.2-I2V-A14B` GGUF Q8_0 (HighNoise + LowNoise) | 双模型，`models/diffusion_models/Wan2.2/I2V/` |
| LoRA | `Wan2.2-I2V-14B-LoRA` | 4步加速必需 |
| 采样 | 双 KSamplerAdvanced：0→2 高噪 + 2→10000 低噪 | steps=4 总 |
| fps | 16fps | VHS_VideoCombine |
| 分辨率 | 1280×720 | ImageResizeKJv2 → EmptyHunyuanLatentVideo |
| 帧数 | 秒×16 | 4s=64f, 5s=80f, 7s=112f |
| cfg | 1.0 | 双 KSampler 都是 1.0 |

**工作流文件**: `阿硕进阶工作流/031)Wan2.2全系列/`（GGUF+LoRA 变体）

**⚠️ 不要用 smoothMix**（社区微调模型，会随机生成泳装美女）。GGUF Q8_0 干净无污染。

**⚠️ Wan I2V 不创造源图没有的内容** — 源图是空轮椅就不会凭空生成老奶奶。故事改动必须先更新源图。

**⚠️ 视频实际时长 ≠ 帧数/fps** — VHS 输出比理论值短（80f→4.81s 非 5.0s）。拼接配音前必须 `ffprobe` 逐镜实测时长计算 adelay。详见 `references/audio-sync-recalculation.md`。

---

## 管线流程

### Phase 0: 项目初始化

```bash
# 每集独立目录 + 共享资产
mkdir -p project/_shared/{characters,backgrounds,voices}
mkdir -p project/epXX/{prompts,workflows,source,video,voice,bgm,final}
```

**目录结构**：
| 目录 | 内容 | 生命周期 |
|------|------|----------|
| `_shared/characters/` | 角色参考图（R1_Michael.png 等） | 跨集复用 |
| `_shared/backgrounds/` | 场景背景图 | 跨集复用 |
| `_shared/voices/` | 声音克隆参考音频 | 跨集复用 |
| `epXX/script.md` | 剧本+分镜表 | 每集 |
| `epXX/prompts/` | `source.md` + `video.md` 提示词归档 | 每集 |
| `epXX/workflows/` | ComfyUI API JSON payload 存档 | 每集 |
| `epXX/source/` | Qwen/Flux 源图 PNG | 每集 |
| `epXX/video/` | Wan I2V 动画 MP4 | 每集 |
| `epXX/voice/` | 配音 WAV/MP3 | 每集 |
| `epXX/bgm/` | Ace-Step BGM MP3 | 每集 |
| `epXX/final/` | ffmpeg 合成成品 + NAS 上传 | 每集 |

**⚠️ 新集开始先检查 `_shared/`**：角色/背景/参考音频已存在就复用，不要重复生成。
**⚠️ 扁平旧结构（`00-characters/` `05-source/`）已废弃** — EP01-02 已迁移到新结构。

### Phase 1: 风格定义（必做）

参考 `YubAI-DramaFlow/templates/风格定义模板.md`：

1. **选择主风格** — 日漫/仿真人/CG/国风等
2. **生成风格锚定提示词** — 中英文各一份，每次生图/生视频必须包含
3. **准备风格参考图** — 至少3张

输出到 `project/00-style/style-anchor.md`

### Phase 2: 人物 & 道具 & 场景设计

#### 2a. 清单梳理（先列后跑）

确定剧本后，先列出所有需要独立生成的元素：

| 类别 | 内容 | 示例 |
|------|------|------|
| 人物 | 每个角色的正面参考图 | Michael（5岁半男孩，红卫衣） |
| 人物变体 | 同一个角色不同状态 | 王奶奶（不戴眼镜）、王奶奶（戴眼镜） |
| 道具 | 关键道具的独立参考图 | 眼镜、轮椅、书包 |
| **场景** | **统一背景图（多镜头复用）** | **街道/人行道背景** |

**输出清单**：编号列表（R1/R2/R3...），每个条目标注角色名、关键特征、用途。

#### 2e. 场景背景图（多镜头复用 🌟）

当多个外景镜头共享同一环境时，**先生成一张空场景背景图**，后续所有镜头用它做 Flux img2img 底图。这样保证环境一致性（路面、光照、树木位置等），比每个镜头独立文生图效果好得多。

详见 `references/master-background-img2img.md`。

#### 2b. 道具参考图（必须先跑）

道具用 Flux.2-Klein 生成，提示词格式：
- **白底孤立**（isolated on pure white background）
- **产品摄影风格**（product photography, studio lighting）
- **1:1 方形**（1280×1280）
- 独立对象，无人物、无背景杂物

#### 2c. 人物参考图（道具之后）

人物正面照，Flux.2-Klein，竖版（1280×1664）：
- 正面视角，中性表情
- 光线均匀、高分辨率
- 服装颜色用大写强调（如 `BRIGHT RED HOODIE`）

#### 2d. 人物变体 + 道具一致性（关键 🌟）

当人物需要**穿戴/使用**某个道具时，不能独立生成——必须保证道具外观一致：

```
正确流程：
1. 先生成道具（如眼镜 R4）
2. 用 Flux img2img，以 R4 为参考图，生成"戴眼镜的人物"（如 R3）
   → 提示词描述人物戴眼镜，img2img 会保留眼镜的形状/颜色
3. 验证两张图中的眼镜一致
```

**错误做法**：人物和道具各自独立文生图 → 眼镜长得不一样。

存到 `project/01-characters/`：
- `R1_michael.png` — Michael 正面
- `R2_granny_no_glasses.png` — 王奶奶不戴眼镜
- `R3_granny_with_glasses.png` — 王奶奶戴眼镜（img2img 用 R4 参考）
- `R4_glasses.png` — 眼镜道具
- `R5_wheelchair.png` — 轮椅道具
- `R6_bag.png` — 红色书包

### Phase 3: 源视频分析与分镜映射

#### 3a. 分析源视频
```bash
ffprobe -v quiet -print_format json -show_format -show_streams source.mp4
```

#### 3b. 切分视频段 + 提取第一帧
```bash
# 按N秒切段，每段取第一帧
ffmpeg -i source.mp4 -c:v libx264 -crf 0 \
  -force_key_frames "expr:gte(t,n_forced*4)" \
  -segment_time 4 -f segment -reset_timestamps 1 \
  project/04-segments/seg_%03d.mp4

# 提取每段第一帧
for f in project/04-segments/seg_*.mp4; do
  ffmpeg -i "$f" -vframes 1 "project/04-segments/$(basename "$f" .mp4)_f0.png"
done
```

#### 3c. 分镜映射
参考 `YubAI-DramaFlow/templates/分镜表模板.md`，将源视频每个镜头映射到分镜表：
- 镜号、景别、运镜、画面描述、时长
- 标注需要换脸的人物
- 输出 `project/02-storyboard/storyboard.md`

### Phase 4: 场景图生成（Qwen 三图参考） 🌟

场景图（多角色+背景）用 **Qwen-Image-Edit 三图参考工作流**。

**工作流文件**: `我的工作流/Qwan-Image-三图参考图生图.json`

**关键参数**:
| 参数 | 值 | 说明 |
|------|-----|------|
| Model | `qwen_image_edit_2511_fp8mixed.safetensors` | Qwen Image Edit 2511 |
| CLIP | `qwen_2.5_vl_7b_fp8_scaled.safetensors` | **必须是 VL 模型**，不能用纯文本 CLIP |
| LoRA | `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | 4步加速 |
| KSampler | steps=8, cfg=1.0, denoise=1.0, euler/simple | |
| 分辨率 | 1280×720 | EmptyLatentImage |

**提示词模板**:
```
图像3的[背景描述]上，图像1中的[角色A]和图像2中的[角色B]在[动作]。
Pixar风格3D动画，[光线/氛围描述]。1280×720。
```

**⚠️ 三张参考图必须 scp 到 ComfyUI input/ 再提交**。
**⚠️ 远景需显式写「在远处」「小小的身影」「远景镜头」否则人物太大**。
**⚠️ 站姿需写「腰背挺直，身体没有前倾没有弯腰」否则角色驼背**。
**⚠️ 背对镜头需写「back view, back facing camera」否则默认面对镜头**。
**⚠️ 编辑器格式转 API 后必删节点**: `MarkdownNote`, `Note`, `PrimitiveNode`, `Fast Groups Muter (rgthree)`, `Fast Groups Bypasser (rgthree)`, `SeedVR2VideoUpscaler`, `SeedVR2LoadVAEModel`, `SeedVR2LoadDiTModel`, `ImageConcanate`, `PreviewImage`, `ImageConcatMulti`。这些是 UI 辅助节点，API 提交会报 `missing_node_type`。

详见 `comfyui` skill 的 `references/qwen-image-edit-multi-reference.md`。

**⚠️ 生成后立即归档提示词 + API JSON** — 把每个镜头的 Qwen prompt 保存到 `epXX/prompts/source.md`，Wan prompt 保存到 `epXX/prompts/video.md`，API payload JSON 保存到 `epXX/workflows/`。不要在 `/tmp` 里丢失，翻拍/改参数时直接复用。

### Phase 5: 视频生成（Wan 2.2 GGUF I2V）

**工作流文件**: `阿硕进阶工作流/031)Wan2.2全系列/`（GGUF+LoRA 4步加速变体）

**API 提交**: 从 `/tmp/` 缓存模板中复用（ep01 已验证），修改 LoadImage + 帧数 + VHS filename_prefix 后 scp+curl 提交。

**关键参数**:
- 帧数 = 秒×16fps（4s=64f, 5s=80f, 7s=112f）
- 双 KSamplerAdvanced: start=0→2 (高噪) + start=2→10000 (低噪), cfg=1.0
- 模型: UnetLoaderGGUF × 2（HighNoise + LowNoise Q8_0）
- LoRA: LoraLoaderModelOnly × 2
- VHS_VideoCombine: 16fps, h264

**⚠️ VHS 输出时长 ≠ 帧数/fps** — 拼接配音前必须 ffprobe 实测。

### Phase 6: 拼接 + 配音 + BGM
# 帧数计算公式：时长秒 × 16fps = 帧数
# 示例：5s→80帧, 4s→64帧, 3s→48帧, 6s→96帧

# 拼接所有视频段
for f in project/06-video/ep01_shot*_anim.mp4; do
  echo "file '$f'" >> segments.txt
done
ffmpeg -f concat -safe 0 -i segments.txt -c copy project/07-final/video_nosound.mp4

# 加上原音轨
ffmpeg -i project/07-final/video_nosound.mp4 -i project/03-source/source.mp4 \
  -c:v copy -c:a aac -map 0:v -map 1:a -shortest \
  project/07-final/final.mp4
```

**BGM 生成**：用 Ace-Step 1.5（`ace_step_v1_3.5b.safetensors`），提示词 `"playful xylophone, 108 bpm, cheerful, bright, whimsical, lighthearted, children cartoon, Pixar style background music, instrumental"`，时长匹配视频总长。BGM 混入时音量降到 0.25。

**成品归档**：所有完整版输出自动复制到 Synology NAS：
```bash
scp -O project/07-final/ep01_final.mp4 TopOnSky@192.168.178.20:/volume1/photo/n8n_workflow/output/happy_children/
```

**配音时间轴**：IndexTTS2 CLI 生成每段台词 WAV，按分镜表的时间轴用 ffmpeg adelay+amix 混入：
```bash
# 配音 adelay 值 = 当前镜号之前的累计时长(毫秒)
# 例：shot05 在第25.8秒 → adelay=25800
[shot05]adelay=25800|25800[a5];[shot07]adelay=34900|34900[a7];
[a5][a7][a8][a10][a11][a12]amix=6:normalize=0[voices];
[bgm]volume=0.25[bgm_low];[voices][bgm_low]amix=2:normalize=0[a]
```

### Phase 7: 配音（IndexTTS2 声音克隆）

**工作流文件**: `阿硕进阶工作流/010)TTS文本转语音/Index-TTS2_自定义音色声音克隆.json`

**可用参考音频**（`ComfyUI/input/`）:

| 参考音频 | 适用角色 |
|---------|---------|
| `可爱儿童男声.flac` | Michael, Luke |
| `可爱儿童女声.flac` | 小女孩 |
| `沉稳男声.flac` | 警察, 成年男性 |
| `成熟女声.flac` | 王奶奶, 成年女性 |

**⚠️ 音色质量关键**: IndexTTS2 忠实克隆参考音频音色。AI合成音（OpenAI TTS 等）听起来像成年人，克隆出来也是成年人。儿童角色必须用真实儿童录音。

**⚠️ IndexTTS2 节点缺失时的回退**: ComfyUI Mie 版可能未安装 `easy downloadIndexTTSAndLoadModel` 等节点。此时直接用 Pi5 本地 EdgeTTS：
```bash
edge-tts --voice zh-CN-YunxiNeural --text "台词" --write-media output.wav
```
可用男声：`zh-CN-YunxiNeural`（青年）, `zh-CN-YunjianNeural`（成熟）。女声：`zh-CN-XiaoxiaoNeural`, `zh-CN-XiaoyiNeural`。

**API 提交要点**:
- 节点: `easy downloadIndexTTSAndLoadModel` → `LoadAudio` → `easy indexTTSGenerateSimple` → `SaveAudio`
- `gr_progress = noop` 必须设（否则 Gradio 阻塞）
- 输出: `output/audio/ep01_shotXX_character_Index-TTS.wav`

---

## SSH 提交模式

ComfyUI API 在 Windows `192.168.178.104:8188`。RTK 代理会拦截跨机 POST，必须用：

```bash
scp payload.json "liuyi@192.168.178.104:D:/tmp_payload.json"
ssh liuyi@192.168.178.104 "curl -sS -X POST http://127.0.0.1:8188/prompt -d @D:\\tmp_payload.json"
```

**⚠️ 不要用 embedded Python 通过 SSH 调 API**（静默返回空输出）。用 `cmd /c curl` 最可靠。

## 已知 Pitfalls


1. **帧数计算** — 始终用 `时长秒 × 16fps`。5s=80帧, 4s=64帧, 3s=48帧, 6s=96帧。
2. **分镜剧本是活的** — 跑新轮之前先确认剧本是否最新。
3. **批量提交 + 后台监控** — 多镜头一起 API 提交，bash 脚本轮询 + 自动 SCP 下载。
4. **Wan I2V 不创造源图没有的内容** 🌟🌟 — 如果源图是空轮椅就不会凭空生成老奶奶。故事剧情改动时，**必须先用 Flux 或 Qwen 重新生成正确的源图**，再提交 Wan I2V。
5. **道具跨镜头一致性** — Flux 文生图无法精确复制道具外观。PIL 合成 + 低 denoise Flux 融合方案见 `references/prop-compositing.md`。
6. **从零生成必须先跑参考图再跑场景** 🌟 — 不要跳过 Phase 2。必须先：清单 → 道具参考图 → 人物参考图 → 场景图。
7. **SSH 提交流可靠模式** — 用 Windows 原生 `curl`，不用 embedded Python。
8. **监控下载必须验证 scp 返回码** 🌟 — scp 失败时不标记完成，文件系统检查比 history API 更可靠。
9. **Flux close-up 导致面部过大** 🌟 — 用 "medium shot" 替代 "close-up"。
10. **人物默认面对镜头** — 需背对镜头时，prompt 写 "back view, back facing camera"。
11. **道具跨场景一致性** 🌟 — PIL 合成 + 低 denoise Flux 融合两步法，详见 `references/prop-compositing.md`。
12. **API格式→编辑器格式转换不可靠** 🌟 — 不要尝试转换。直接 API 提交或让用户提供编辑器格式文件。
13. **Wan 2.2 GGUF + LoRA 4步加速（首选）** 🌟 — GGUF Q8_0 干净无泳装问题。4步加速，1280×720 直接输出，无 RIFE。
14. **多镜头环境一致性** — 统一背景图 + Flux img2img 复用，详见 `references/master-background-img2img.md`。
15. **分镜后期重组** 🌟 — 调换/删除/新增对白 + ffprobe 实测 adelay 重算，详见 `references/shot-reordering-workflow.md`。
16. **Qwen 三图参考图需先上传 ComfyUI input/** — 3 张参考图必须 scp 到 input/ 再提交 API。
17. **TextEncodeQwenImageEditPlus 文本字段名是 `prompt`** 🌟 — 不是 "text"。
18. **Qwen 三图 KSampler 参数固定** — steps=8, cfg=1.0, denoise=1.0。
19. **复杂动作序列需多张源图** 🌟 — 单源图无法表达多阶段动作，主动建议分镜。
20. **远景提示词必须显式写** 🌟 — "站在远处""小小的身影""远景镜头"，否则人物太大。
21. **走路动画需要更多帧 + 自然步态** 🌟 — 80f→112f，提示词写 "smooth confident stride, no limp, no stagger"。
22. **VHS filename_prefix 子目录需匹配** 🌟 — scp 路径必须包含子目录。
23. **跨镜服装一致性** 🌟 — 同角色镜头用同一种工作流 + 同参考图。
24. **站姿必须写"挺直"** 🌟 — 默认会驼背，提示词加"腰背挺直，身体没有前倾没有弯腰"。
25. **视频实际时长 ≠ 帧数/fps** 🌟🌟 — 拼接配音前必须 ffprobe 逐镜实测时长计算 adelay。
26. **调换配音不调换视频** — 改 ffmpeg 音频输入顺序，视频 concat 不变。
27. **GPT/LLM 增强提示词对 Wan I2V 无用** 🌟🌟 — 2026-07 实测：原始提示词 vs ChatGPT 增强提示词，生成 6 个视频 A/B 对比。GPT 版本加入大量视觉细节（golden glow, soft shadows, texture），对 Wan I2V 无任何提升。Wan 是图生视频，源图决定 80%+ 视觉效果，提示词只控运动描述。不要在提示词上浪费时间。源图质量才是唯一关键。
28. **Synology NAS scp 需 -O 参数** — `scp -O` 用 legacy 协议，默认 SFTP 模式对某些 NAS 版本不兼容，报 `subsystem request failed`。
29. **Qwen 源图输出在 output/，Wan LoadImage 需要 input/** — Qwen 三参考生成的源图在 `output/` 目录，Wan 工作流的 LoadImage 节点从 `input/` 读取。提交 Wan 前必须 `copy output\*.png input\`。
27. **云 Vision API 不可靠时用本地 Qwen3VL** 🌟 — Hermes 内置 Vision 偶尔返回 503。遇到时立即切到 `qwen3-vl-local` skill，通过 SSH 调用 Windows 上的 llama-server（~3s/张）或 ComfyUI（~80s/张）。详见 `qwen3-vl-local` skill。
28. **每阶段结束必须等用户审查通过再继续** 🌟🌟 — 剧本写完后不要直接开始生成。先出示剧本等用户说"可以"。源图生成后先出示等确认。用户说"我还没审查通过那"就是你没等。宁愿多等一轮，不要白跑一管。
29. **Qwen 输出在 output/，Wan LoadImage 需要 input/** 🌟 — Qwen 三参考的输出图直接落在 `ComfyUI/output/`，但 Wan 工作流的 LoadImage 节点从 `ComfyUI/input/` 读文件。生成源图后必须 `copy output/xxx.png input/` 再提交 Wan。否则报 `Invalid image file`。
30. **Wan 输出 MP4 无音轨** 🌟 — Wan 生成的视频文件不含音频流。拼接配音时不能用 `[0:a]` 引用视频音轨（不存在）。必须先用 `anullsrc` 生成静音轨：`ffmpeg -f concat -i list.txt -f lavfi -i anullsrc=r=24000:cl=mono -shortest -c:v copy out.mp4`，再混音。
31. **配音时长 ≠ 视频时长时用 atempo 加速** — EdgeTTS 生成的配音时长可能与视频镜头时长不匹配。用 `atempo` 滤镜缩放：`ffmpeg -i voice.mp3 -filter:a \"atempo=1.16\" -c:a libmp3lame out.mp3`。注意 atempo 范围 0.5-2.0，超出需链式 `atempo=2.0,atempo=1.1`。
32. **每集归档提示词 + payload JSON** 🌟 — 生成完成后立即把该集的 Qwen/Wan/BGM prompt 和 API JSON 从 `/tmp/` 复制到 `epXX/prompts/` 和 `epXX/workflows/`。翻拍时直接改参数复用，不用重写。
33. **扁平目录不可扩展** 🌟 — `05-source/` `06-video/` 混放多集文件后期失控。新集必须用 `epXX/{prompts,workflows,source,video,voice,bgm,final}` 格式，跨集资产放 `_shared/`。

## 参考文档

- `references/wan22-gguf-lora-workflow.md` 🌟 — Wan 2.2 GGUF + LoRA 4步加速工作流详情
- `references/wan22-i2v-animation-tips.md` 🌟 — 动画质量：走路帧数、站姿、远景占比、服装一致性
- `references/wan22-prompt-comparison-gpt.md` 🌟 — Wan I2V 手写提示词 vs GPT 增强对比（结论：手写更好）
- `references/qwen3vl-source-image-qc.md` — Qwen3VL 本地源图质检（云 Vision 备用方案）
- `references/audio-sync-recalculation.md` — ffprobe 实测时长 + adelay 重算
- `references/shot-reordering-workflow.md` 🌟 — 分镜后期重组模板
- `references/qwen-3ref-api-payload.md` 🌟 — Qwen 三图参考 API 提交格式
- `references/qwen-multi-reference-prompt-template.md` — Qwen 提示词模板
- `references/flux-klein-api-workflow.md` — Flux.2-Klein API 格式
- `references/prop-compositing.md` — 道具跨场景一致性
- `references/master-background-img2img.md` — 统一背景图方案
- `references/voice-cloning-pipeline.md` — IndexTTS2 声音克隆管线
- `references/happy-children-ep01-log.md` — Happy Children 第一集实操记录
- `references/from-scratch-workflow.md` — 从零生成漫剧快速流程

**弃用归档**: `references/legacy-bernini-ltx.md`（BERNINI + LTX 2.3 + smoothMix 旧管线）
