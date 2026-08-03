# 国内可访问：魔搭创空间部署（推荐，替代 Hugging Face）

Hugging Face / Render 在国内常打不开或要绑卡。  
改用阿里云 **魔搭 ModelScope 创空间**：国内网络友好，免费 2C16G CPU，Docker 端口 `7860`。

完成后评委链接类似：

`https://modelscope.cn/studios/<你的用户名>/xiaopeng-travel-agent`

---

## 你需要做的（约 10 分钟）

### 1. 注册 / 登录魔搭
打开：https://www.modelscope.cn/  
建议用已有**阿里云账号**登录（你做百炼的那个）。  
Docker 创空间通常需要**实名认证**（国内身份证，不是国外银行卡）。

### 2. 新建创空间
1. 打开：https://www.modelscope.cn/studios  
2. **新建创空间**
   - 名称：`xiaopeng-travel-agent`
   - 可见性：**公开**
   - SDK / 类型：选 **Docker**（若创建页没有 Docker，先建空仓库再按下面推送 `ms_deploy.json`）
   - 资源：选 **CPU basic / 2v CPU / 16G**（免费档）

### 3. 推送代码到创空间 Git

在创空间页面找到 **Git 地址** 和 **Access Token**（个人中心 → 访问令牌）。

在本机项目目录执行（替换用户名、token、空间名）：

```powershell
cd C:\Users\xingx\Desktop\8.2\xiaopeng-travel-agent

git remote remove ms 2>$null
git remote add ms https://oauth2:<你的魔搭Token>@www.modelscope.cn/studios/<你的用户名>/xiaopeng-travel-agent.git

# 若本机还推不了 GitHub，至少保证这些文件在目录里后用网页上传也行：
# Dockerfile / ms_deploy.json / requirements.txt / backend/ / frontend/ / .env.example

git push ms HEAD:master
# 有的空间默认分支是 main：
# git push ms HEAD:main
```

**必须包含的文件：**
- `Dockerfile`（已监听 7860）
- `ms_deploy.json`
- `requirements.txt`
- `backend/`
- `frontend/`
- `.env.example`

### 4. 上线
创空间 → **设置** → **上线 / 重启**  
等状态变成运行中，打开公网地址自测：点「自动演示 4 场景」（可无 Key）。

可选：在创空间环境变量里加 `DASHSCOPE_API_KEY`（不填也能演示）。

---

## 和评委怎么写

- **体验入口：** `https://modelscope.cn/studios/<用户名>/xiaopeng-travel-agent`  
- **GitHub：** https://github.com/SXY-xinyun/xiaopeng-travel-agent  

---

## 若创建页找不到 Docker

把 `ms_deploy.json` 和 `Dockerfile` 上传进创空间仓库后，在设置里按 Docker 配置上线；或发我你的**魔搭用户名 + Token**，我帮你写推送命令并核对文件清单。
