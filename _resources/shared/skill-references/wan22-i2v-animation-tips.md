# Wan 2.2 I2V 动画质量调试指南

基于 EP02 Shane 走进镜头的实战经验。

## 走路动画 — 帧数与提示词

**问题**: 80 帧（5s）的走路动画，角色像"一瘸一拐"，步态僵硬不自然。

**根因**: Wan I2V 在较少帧数下难以生成流畅的走路循环，步幅节奏失控。

**修复**:
1. **增加帧数**: 80 → 112（7s）。更多帧给模型更多"空间"来展开自然步态。
2. **提示词必须显式约束步态**:

```
(Dynamic actions: Smooth confident stride, arms swinging gently in sync with each step, 
posture upright, walking in a straight line directly towards the viewer. 
No limp, no stagger, no mouth movement, no talking.)
```

不要只写 `walking` — 模型理解的"走路"可能是任何速度/质量的步态。

**验证标准**: 正常走路应该手臂自然前后摆动，步伐均匀，身体重心平稳过渡。

## 站姿 — 防止弯腰

**问题**: Qwen 三图生成的站立人物会前倾弯腰，Wan I2V 视频中持续弯腰。

**修复 — 源图提示词**:
```
笔直地站在街道中央，正面朝向镜头。腰背挺直，站姿端正挺拔，双肩平齐，下巴微收。
身体没有前倾没有弯腰。
```

**修复 — 视频提示词**:
```
His posture remains straight and confident throughout. No bending, no leaning forward.
```

## 远景 — 人物占比控制

**问题**: Qwen 三图提示词要求远景，但生成出来人物仍占画面很大比例。

**修复 — 源图提示词**:
```
站在远处街道的中央，小小的身影，这是远景镜头，X在画面中占比很小。
```

多加"小小的身影"、"占比很小"让模型理解这是远景镜头。

## 服装 — 跨镜一致性

**问题**: 不同工作流（Flux vs Qwen 三图）生成同一角色时服装颜色/款式漂移。

**根因**: 不同模型对同一参考图的解释不同，且 Flux 不锁角色特征。

**修复**: **所有涉及该角色的外景镜头统一用 Qwen 三图工作流**，用相同的角色参考图。

## VHS 输出路径 — scp 下载

**问题**: `filename_prefix: "wan2.2/ep02_shot01"` 输出到 `output/wan2.2/ep02_shot01_00001.mp4`，但监控脚本只从 `output/` 根目录 scp。

**修复**: history API 返回的 filename 已包含子目录路径，scp 时直接用:
```bash
scp "host:/D:/.../output/${fn}" ./local.mp4  # fn 如 wan2.2/ep02_shot01_00001.mp4
```
