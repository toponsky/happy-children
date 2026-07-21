# EP03 图生视频提示词

## Shot 01 — Sam 走向镜头（112帧 / 7秒）
```
Pixar-style 3D animation. Wide shot of Fireman Sam in navy blue uniform with yellow reflective stripes, wearing a bright yellow firefighter helmet, standing at a fire station and then walking forward toward the camera. Smooth confident stride, arms swinging gently in sync with each step, posture upright, walking in a straight line from the distance all the way forward. No limp, no stagger. Warm morning sunlight. No other people.
```

## Shot 02 — Sam 说话（240帧 / 15秒）
```
Pixar-style 3D animation. Medium shot of Fireman Sam in navy blue uniform with yellow reflective stripes, wearing a bright yellow firefighter helmet, standing in front of a fire station, facing the camera and speaking with a warm friendly smile. (Dynamic actions: Sam stands completely still with posture perfectly straight and upright, body does not sway or rock, only slight natural head movement and lip movement as he speaks with a warm smile. No leaning, no slouching, no body swaying.) Warm morning sunlight. No other people.
```

## Shot 03 — Sam 走回消防站（80帧 / 5秒）
```
Pixar-style 3D animation. Back view of Fireman Sam in navy blue uniform with yellow reflective stripes, wearing a bright yellow firefighter helmet, walking away from the camera toward the fire station building with red garage doors. Smooth confident stride, arms swinging gently, posture upright, walking in a straight line away. No limp, no stagger. Warm morning sunlight. No other people.
```

## 统一参数
- 模型: Wan 2.2 GGUF I2V (HighNoise Q8_0 + LowNoise Q8_0)
- LoRA: Wan 2.2 I2V 14B LoRA (4步加速)
- 双 KSamplerAdvanced: 0→2 (高噪) + 2→10000 (低噪)
- 16fps, 1280×720, cfg=1.0
