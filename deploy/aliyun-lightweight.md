# 阿里云轻量应用服务器公网部署

目标：评委可通过 `http://<公网IP>:8000` 直接体验 Agent；`/api/health` 显示 `llm_configured: true`。

## 1. 准备

- 阿里云轻量应用服务器（Ubuntu 22.04 推荐，1 核 2G 即可）
- 安全组 / 防火墙放行 **TCP 8000**（或 80 反代）
- 百炼 API Key（[控制台](https://bailian.console.aliyun.com/)）

## 2. 安装 Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
```

## 3. 上传代码

本机打包上传，或服务器 git clone。示例：

```bash
# 在服务器
mkdir -p ~/xiaopeng-travel-agent
cd ~/xiaopeng-travel-agent
# 将本地项目文件上传到此目录（不含 .venv）
```

## 4. 配置环境变量

```bash
cp .env.example .env
nano .env
```

必填：

```env
DASHSCOPE_API_KEY=sk-xxxxxxxx
DASHSCOPE_MODEL=qwen-plus
HOST=0.0.0.0
PORT=8000
```

**不要**把 `.env` 提交到 Git。

## 5. 启动

```bash
sudo docker compose up -d --build
sudo docker compose ps
curl http://127.0.0.1:8000/api/health
```

期望：

```json
{"ok":true,"llm_configured":true,"planner_default":"llm","model":"qwen-plus"}
```

公网访问：`http://<公网IP>:8000`

## 6. （可选）Nginx 反代 80 端口

```nginx
server {
  listen 80;
  server_name _;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

## 7. （可选加分）OSS 静态资源

1. 创建 OSS Bucket，开启静态网站托管或 CDN
2. 上传 `frontend/public/` 下的 `index.html / styles.css / app.js`
3. 将前端 API 地址改为公网后端（若前后端分离）
4. 技术方案报告中写明：**百炼（推理）+ 轻量服务器（Agent 托管）+ OSS（静态资源）**

当前默认单体部署已足够评委体验；OSS 为加分叙述，非必须。

## 8. 运维常用命令

```bash
sudo docker compose logs -f --tail=100
sudo docker compose restart
sudo docker compose down
```

## 9. 提交时填写

- 体验链接：`http://x.x.x.x:8000`
- 健康检查：`http://x.x.x.x:8000/api/health`
- 建议评委点击顶部「自动演示 4 场景」
