# 可靠提交与下载模式（Pi5 → Windows ComfyUI）

经过多次静默失败后验证的可靠模式。

## 1. 提交工作流

**✅ 可靠：SSH + Windows 原生 curl**

```bash
# Step 1: 本地生成 API JSON
python3 -c "
import json
wf = {...}  # API 格式工作流
with open('/tmp/payload.json','w') as f:
    json.dump({'prompt': wf}, f)
"

# Step 2: scp 到 Windows
scp /tmp/payload.json "liuyi@192.168.178.104:D:/tmp/payload.json"

# Step 3: SSH + curl 提交（不用 PowerShell，不用 embedded Python）
ssh liuyi@192.168.178.104 "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @D:\\tmp\\payload.json"
# → {"prompt_id": "...", "number": N, "node_errors": {}}
```

**❌ 不可靠（会静默失败）：**
- `ssh ... "D:\\...\\python_embeded\\python.exe -c \"...\""` — 空输出，无报错
- `ssh ... "powershell -File D:\\submit.ps1"` — 空输出，无法调试
- 直接用 Pi5 curl 跨子网 → RTK 安全代理拦截

## 2. 检查文件（比 history API 可靠）

```bash
# ✅ 可靠：文件系统检查
ssh liuyi@192.168.178.104 "cmd /c \"dir /b /o-d D:\\ComfyUI_Mie_2026_V8.0\\ComfyUI\\output\\ep01_ref_*_00001_.png\""
# → 实际存在的文件列表

# ⚠️ 有时不可靠：history API 轮询
# /history/{pid} 可能返回空（status="?"），但文件已在磁盘上
```

## 3. 下载输出

**✅ 可靠：等全部完成 → 一次批量 scp**

```bash
# 确认文件全部存在后，顺序下载
for sn in 01 02 03 04 05 06 07 08 09 10; do
  scp "liuyi@192.168.178.104:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/ep01_shot${sn}_00001_.png" \
    "./ep01_shot${sn}_v1.png" && echo "shot${sn} ✓" || echo "shot${sn} ✗"
done
```

**❌ 不可靠：bash 关联数组 + 后台轮询**

```bash
# BUG: declare -A done 在 scp 失败时仍标记完成
scp ... "$OD/file.png"  # 静默失败
done[$key]=1             # 仍然标记！
count=$((count+1))       # 计数递增，实际文件未下载

# 正确做法：每次下载后检查文件是否存在
scp ... "$OD/file.png" && done[$key]=1 || continue
# 或直接等全部完成后统一下载
```

## 4. Flux.2-Klein 场景源图提示词要点

- 人物描述用大写强调关键特征：`BRIGHT RED HOODIE`, `NO glasses on her face`
- 负面提示词统一：`no woman, no girl, no female, no swimsuit, no other people, blurry, low quality, text, watermark`
- 横版使用 1664×1280（16:10），道具用 1280×1280
- steps=28, guidance=3.5（via FluxGuidance 节点）
- 每张用不同 seed，避免完全相同的 latent noise
