# 无银行卡公网部署（Hugging Face Spaces）

Render 免费档常要求绑卡。改用 **Hugging Face Spaces（Docker）**，注册一般**不需要银行卡**。

## 约 5 分钟步骤

1. 打开并注册/登录：https://huggingface.co/join  
2. 打开：https://huggingface.co/new-space  
3. 填写：
   - **Space name：** `xiaopeng-travel-agent`（随意）
   - **SDK：** 选 **Docker**
   - **Visibility：** Public（公开，评委才能看）
4. 创建后，在 Space 页点 **Files** → **Add file** → **Upload files**，或用 Git 推送本仓库全部内容  
5. 重要：把仓库根目录的 `README.hf.md` **改名为 / 覆盖成 Space 的 `README.md`**（带 YAML 头，`app_port: 7860`）  
6. 等待 Building → Running  

完成后地址类似：

`https://huggingface.co/spaces/<你的用户名>/xiaopeng-travel-agent`

或直接嵌入页：

`https://<你的用户名>-xiaopeng-travel-agent.hf.space`

## 用 Git 推到 Space（推荐）

在 Hugging Face 账号设置里创建 Access Token（Write 权限），然后：

```powershell
cd C:\Users\xingx\Desktop\8.2\xiaopeng-travel-agent
Copy-Item README.hf.md README.space.md -Force

# 克隆空 Space 后复制文件，或直接加 remote：
git remote add hf https://huggingface.co/spaces/<你的用户名>/xiaopeng-travel-agent
# 推送前确保 Space 根目录 README.md 使用 README.hf.md 的内容
```

更省事：在网页上传这些关键文件即可：

- `Dockerfile`
- `requirements.txt`
- `backend/` 整个目录
- `frontend/` 整个目录
- `README.md`（用 `README.hf.md` 内容）
- `.env.example`

## 环境变量（可选）

Space → Settings → Variables：

- `DASHSCOPE_API_KEY`：可不填（免 Key 演示）
- `DASHSCOPE_MODEL`：`qwen-plus`
- `PORT`：`7860`（一般不用手填，Dockerfile 已适配）

## 评委怎么用

打开 Space 链接 → 点 **「自动演示 4 场景」** → 无需填 Key。  
可选在页面粘贴自己的百炼 Key 启用 LLM。
