# Wan 2.2 I2V 手写 vs GPT 增强提示词 A/B 对比

## 测试环境

- 模型: Wan 2.2 I2V-A14B GGUF Q8_0 + LoRA 4步加速
- 源图: EP02 三张源图（Qwen 三参考生成，完全相同）
- 参数: 16fps, cfg=1.0, euler/simple, seed 随机但同镜一致

## 测试方法

每个镜头生成两个版本：
- **手写版**: 简洁运动描述（smooth stride, posture upright, no limp...）
- **GPT 版**: ChatGPT 4o-mini 增强（加入 golden glow, soft shadows, camera tracking, texture detail...）

## 结果

| 镜头 | 帧数 | 手写版 prompt_id | GPT 版 prompt_id | 用户评价 |
|------|------|-----------------|-----------------|----------|
| Shot 01 走向镜头 | 96f | 7bcc4ddc | eb848fa5 | 手写更好 |
| Shot 02 说话 | 256f | db751b5a | 59a4d084 | 手写更好 |
| Shot 03 走远 | 96f | ebb2f939 | cc2ab4bf | 手写更好 |

## 结论

**ChatGPT 增强对 Wan I2V 无任何提升。**

根因：
1. Wan I2V 是图生视频，源图决定 80%+ 视觉内容
2. 提示词只控运动描述，不管画面风格/光影/构图
3. GPT 加的视觉细节（golden glow, soft shadows, texture）Wan 改不了
4. 部分 GPT 内容可能误导（"camera zooms in" — Wan 镜头固定不会运镜）

## 建议

写 Wan prompt 只写动作即可：
- smooth confident stride
- posture upright, no swaying
- no limp, no stagger
- 源图质量才是唯一关键

不要在提示词上浪费时间。
