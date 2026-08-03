# 用 Render 从 GitHub 一键出公网体验链接

适合本项目（FastAPI + Dockerfile）。免费档即可参赛 Demo。

## 1. 代码已在 GitHub

确认仓库公开，例如：

`https://github.com/<你的用户名>/xiaopeng-travel-agent`

## 2. 在 Render 部署

1. 打开 https://dashboard.render.com/ 用 GitHub 登录  
2. **New → Web Service** → 选择本仓库  
3. 设置：
   - **Runtime:** Docker（会读根目录 `Dockerfile`）
   - **Instance:** Free
4. **Environment** 添加：

| Key | Value |
|---|---|
| `DASHSCOPE_API_KEY` | 你的百炼 sk-… |
| `DASHSCOPE_MODEL` | `qwen-plus` |

5. Create Web Service，等 Build 完成  

公网地址类似：

`https://xiaopeng-travel-agent.onrender.com`

## 3. 自测

- 首页：`https://你的服务.onrender.com/`  
- 健康：`https://你的服务.onrender.com/api/health` → 应见 `"llm_configured": true`  
- 点页面顶部 **「自动演示 4 场景」**

## 4. 注意

- 免费实例会休眠，首次打开可能要等 30–60 秒，属正常  
- **不要**把 Key 写进仓库；只放在 Render 环境变量  
- 若 Build 失败，在 Render Logs 看 pip/Docker 报错  

## 5. 提交到天池时写什么

- **体验链接：** `https://xxx.onrender.com`  
- **GitHub：** `https://github.com/<用户名>/xiaopeng-travel-agent`  
- 可不交视频（有公网体验链接即可）
