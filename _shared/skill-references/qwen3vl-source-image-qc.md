# Qwen3VL 本地源图质检（云 Vision 备用方案）

Qwen3VL-8B-Instruct Q4_K_M GGUF 模型，通过 llama-cpp-python 在 Windows ComfyUI 主机上运行。

## 快速使用

```bash
# 先写脚本到 /tmp/check_shots.py，然后 scp + 运行
scp /tmp/check_shots.py "liuyi@192.168.178.104:/D:/tmp/check_shots.py"
ssh liuyi@192.168.178.104 "D:\\ComfyUI_Mie_2026_V8.0\\python_embeded\\python.exe D:\\tmp\\check_shots.py"
```

## 脚本模板

```python
import sys, base64, io
sys.path.insert(0, r"D:\ComfyUI_Mie_2026_V8.0\ComfyUI\custom_nodes\ComfyUI-llama-cpp")
from llama_cpp import Llama
from PIL import Image

llm = Llama(
    model_path=r"D:\AI\models\Qwen3VL-8B-Instruct-Q4_K_M.gguf",
    n_ctx=4096, n_gpu_layers=-1, verbose=False
)

for img_path in ["path/to/image1.png", "path/to/image2.png"]:
    img = Image.open(img_path)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    resp = llm.create_chat_completion(
        messages=[{"role":"user","content":[
            {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}},
            {"type":"text","text":"Is this a wide/distant shot? Is the police officer a small figure? Posture straight? Answer 2-3 sentences."}
        ]}],
        max_tokens=150
    )
    print(resp["choices"][0]["message"]["content"])
```

## 质检 Check List

生成源图后逐张检查：

| 检查项 | 问题句式 |
|--------|---------|
| 景别 | Is this a wide/distant shot or a medium close-up? |
| 角色可见 | Is the [角色] in [服装] visible? |
| 远景比例 | Is the character a small figure in the distance? |
| 朝向 | Is the character facing the camera or away? |
| 站姿 | Is the posture straight and upright? |
| 表情 | Does the character have a warm smile? |

## 模型信息

- 文件: `D:\AI\models\Qwen3VL-8B-Instruct-Q4_K_M.gguf`
- mmproj: `D:\AI\models\mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf`（Qwen3VL GGUF 内置视觉编码，无需单独加载）
- 加载时间: ~5s (RTX 5090)
- 单图推理: ~3s

## 注意事项

- llama-cpp-python 必须是 ComfyUI embedded Python 安装的版本（`D:\ComfyUI_Mie_2026_V8.0\python_embeded\`）
- Q4_K_M 量化精度足以胜任源图 QC，不需要 Q8
- 用 Yes/No 问题比开放式描述更可靠
