# LTX 2.3 提示词格式

用于环境镜头/空镜的视频生成。LTX 2.3 支持全局提示词 + 分段关键帧提示词。

## 三段式结构

```
全局提示词（整个视频共享的风格/环境描述）
分段提示词（按时间轴的关键帧描述，模型自动插值过渡）
Negative prompt
```

## 示例：Shot 01（Michael 跑出家门）

**全局提示词：**
```
Pixar-style 3D animation, sunny morning suburban street, warm golden sunlight, trees and houses with manicured lawns, peaceful neighborhood atmosphere, cinematic lighting, smooth camera tracking, high quality
```

**分段提示词（Keyframe）：**

| 时间段 | 提示词 |
|--------|--------|
| 0-2s | a 5-year-old boy with spiky brown hair wearing a BRIGHT RED HOODIE and red backpack bursts energetically out of a front door, door swings behind him, cheerful excited expression, dynamic motion |
| 2-5s | the boy runs joyfully down the sidewalk away from the house, arms pumping, red backpack bouncing, wide shot showing the full suburban street, trees passing by, golden morning light |

**Negative：**
```
blurry, low quality, worst quality, deformed, ugly, bad anatomy, extra limbs, distorted face, static, motionless, no woman, no female, no swimsuit, no bikini, extra people, duplicate, overexposed, underexposed, fog, mist, grainy, text, watermark
```

## 与 Wan 2.2 I2V 提示词的区别

| 维度 | LTX 2.3 | Wan 2.2 I2V |
|------|---------|-------------|
| 提示词角色 | 驱动整个视频生成 | 辅助源图，源图主导内容 |
| 分段提示词 | 支持时间轴分段 | 单一提示词 |
| 人物一致性 | 较差（纯文生视频） | 好（源图锚定） |
| 适用场景 | 环境/空镜 | 人物中全景 |
| 泳装风险 | 零 | smoothMix 有风险 |
