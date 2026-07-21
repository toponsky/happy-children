# 食物吉祥物生成模板

Pixar 风格卡通食物角色，用于动画项目吉祥物/配角设计。

## 通用提示词模板

**正面**：
```
Pixar-style 3D animation character design, a cute adorable [FOOD] mascot character, [SHAPE DESCRIPTION], tiny arms and legs, happy cheerful expression with big sparkly eyes and a warm smile, soft pink blush on cheeks, [DISTINCTIVE FEATURE], pastel colors, simple clean design suitable for animation, children's cartoon style, isolated on white background, front view full body, 8K, no other objects
```

**负面**：
```
blurry, low quality, distorted, ugly, deformed, bad anatomy, extra limbs, dark, realistic, photorealistic, human, monster, scary, text, watermark, signature
```

## 已验证的吉祥物

| 食物 | 形状关键词 | 特色细节 | 种子 |
|------|----------|---------|:--:|
| 包子 | soft white fluffy round body | red bow on top | 42 |
| 圆葱 | round purple onion body with layered texture | green sprout on top | 123 |
| 西蓝花 | bright green broccoli tree-shaped body with textured florets | flower buds on head | 456 |
| 饺子(水煮) | plump crescent-shaped dumpling body, white | golden crispy bottom | 111 |
| 饺子(元宝) | HALF-MOON CRESCENT shape like gold yuanbao ingot, NOT round | delicate pleated folds | 888 |
| 小笼包 | round plump dumpling body with delicate pleated folds | steam wisps above | 222 |
| 面条 | long wavy golden noodle body curled into cute shape | red Chinese-style collar bow | 333 |
| 米饭 | round white ceramic bowl filled with fluffy white steamed rice | chopsticks as arms, steam | 444 |
| 豆腐 | soft white square block of silky tofu, smooth jiggly texture | soy sauce drizzle | 555 |
| 锅贴 | long golden-brown pan-fried dumpling body with crispy bottom | crimped edges | 666 |
| 烧饼 | round flat disc-shaped baked bread body, golden brown crispy surface | sesame seeds on top | 111 |
| 烤玉米 | long yellow corn on the cob body with charred grill marks, golden roasted kernels | wooden stick at bottom, steam wisps | 222 |
| 羊肉串 | wooden skewer with juicy grilled lamb meat chunks stacked, golden brown charred edges | cumin and chili flakes, smoke | 333 |
| 火锅 | round copper hotpot pot body with chimney in middle | divided spicy/mild broth, bubbling, steam | 444 |
| 鱼蛋串 | bamboo skewer with three round white fish balls | golden curry sauce drizzle | 555 |
| 糖葫芦-香蕉 | bamboo skewer with three round yellow banana slices | shiny crystalline golden sugar glaze | 111 |
| 糖葫芦-草莓 | bamboo skewer with three bright red heart-shaped strawberries | glossy sugar coating, green leaf | 222 |
| 糖葫芦-葡萄 | bamboo skewer with four small round purple grapes | glossy translucent sugar glaze | 333 |
| 糖葫芦-山楂 | bamboo skewer with four round deep red hawthorn berries | classic traditional Chinese street snack | 444 |
| 糖葫芦-苹果 | bamboo skewer with three round small green apple fruits | glossy sugar coating, green leaf | 555 |

## 面条 v2（升级版）

面条第一版偏简单，升级版关键词：
- **正面**：`beautiful bowl of hand-pulled ramen noodles, golden wavy curly noodle strands flowing elegantly upward from a decorative blue and white porcelain bowl, fresh bright green chopped scallion garnish, soft-boiled egg with smiley face, chopsticks like arms, misty steam wisps, golden broth`
- **负面**：加 `ugly, messy, dark, dirty, plain, boring`
- **种子**：1122

## 工具与参数

- **模型**：Flux.2-Klein fp8（`flux-2-klein-9b-fp8.safetensors`）
- **CLIP**：Qwen 3 8B（`qwen_3_8b_fp8mixed.safetensors`）
- **分辨率**：1024×1024（方形）
- **采样**：steps=8, cfg=1.0, sampler=euler, scheduler=simple
- **FluxGuidance**：不需要（吉祥物不需要 guidance）

## 修正技巧

- **饺子太圆 → 强调 HALF-MOON CRESCENT，负面加 `round, circular, ball`**
- **饺子变锅贴 → 负面加 `golden, brown, fried, crispy, potsticker`**
- **旋转**：提示词加 `tilted and rotated approximately XX degrees`，无需后处理
- **白底不干净** → 负面加 `background objects, floor, shadow, platform`
