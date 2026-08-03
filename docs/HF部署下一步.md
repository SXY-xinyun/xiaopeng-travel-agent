# 一键部署到 Hugging Face Spaces（无需银行卡）

## 你只做 2 件事，然后把信息发我（或自己跑命令）

### 1）注册并拿 Token
1. 打开：https://huggingface.co/join  
2. 登录后打开：https://huggingface.co/settings/tokens  
3. **Create new token**
   - Type：`Write`
   - 复制形如 `hf_...` 的字符串（只显示一次）

### 2）把下面两样发给我（私聊即可）
- Hugging Face **用户名**（主页 URL 里那一段）
- 刚才的 **Write Token**（`hf_...`）

我会执行部署脚本，完成后给你：

- `https://huggingface.co/spaces/<用户名>/xiaopeng-travel-agent`
- `https://<用户名>-xiaopeng-travel-agent.hf.space`（评委直接点这个）

---

## 想自己跑也可以

```powershell
cd C:\Users\xingx\Desktop\8.2\xiaopeng-travel-agent
.\.venv\Scripts\pip install -U huggingface_hub
$env:HF_TOKEN = "hf_你的token"
.\.venv\Scripts\python scripts\deploy_hf_space.py --username 你的用户名
```

等 Space 状态变成 **Running** 后即可交卷。详细说明见 `deploy/huggingface-spaces.md`。
