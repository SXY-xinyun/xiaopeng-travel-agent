# Qoder码力星期四·小鹏 AI 出行Agent

可运行、可体验的 **AI 出行服务编排 Agent**：覆盖「车主自驾」与「Robotaxi 乘客服务」，强调场景理解、工具编排闭环、安全边界与可解释输出。

运行时默认：**阿里云百炼千问多轮编排 + 规则安全护栏**；无 Key 自动降级规则引擎。

## 快速启动（本地）

```powershell
cd xiaopeng-travel-agent
copy .env.example .env
# 可选：编辑 .env，填入 DASHSCOPE_API_KEY=sk-xxx（不填也能规则演示）
.\run.ps1
```

打开 http://127.0.0.1:8000  
点击顶部 **「自动演示 4 场景」** 即可录制 Demo / 给评委演示。

## 部署与复现

- Docker：`docker compose up -d --build`  
- 魔搭创空间（可选）：[deploy/modelscope-studio.md](deploy/modelscope-studio.md)  
- 阿里云轻量（可选）：[deploy/aliyun-lightweight.md](deploy/aliyun-lightweight.md)  

## 能力对照赛题

| 赛题要求 | 本项目体现 |
|---|---|
| 场景理解 | 识别“放歌→疲劳”“跑过去→穿行风险”等真实意图 |
| 服务编排 | 多轮：规划→执行→结果回灌→收敛；工具形成闭环 |
| 安全边界 | 疲劳禁娱乐主策略、禁鼓励横穿、儿童强制锁门、求助强制转人工 |
| 结果输出 | 回复 + 服务计划 + 工具理由 + 禁止动作 + 安全提示 + 状态对比 |
| 可体验 Demo | 座舱 HUD、评委一键剧本、Demo 视频、GitHub 可复现 |

## 提交材料索引

| 材料 | 路径 |
|---|---|
| **交卷材料包（先看这个）** | [docs/交卷材料包.md](docs/交卷材料包.md) |
| 论坛正文（复制粘贴） | [docs/forum_post.md](docs/forum_post.md) |
| STAR 介绍 | [docs/STAR_final.md](docs/STAR_final.md) |
| 技术方案报告 | [docs/tech_report.md](docs/tech_report.md) · 打印页 [docs/tech_report_print.html](docs/tech_report_print.html) |
| 运行效果（4 场景） | [docs/demo_results.md](docs/demo_results.md) |
| Demo 视频脚本 | [docs/demo_script.md](docs/demo_script.md) |
| Qoder 证明清单 | [docs/qoder_checklist.md](docs/qoder_checklist.md) |
| 打包命令 | `.\pack_submission.ps1` → `submission/` |

论坛标题必须以 **「Qoder码力星期四·小鹏 AI 出行Agent」** 开头。

## 项目结构

```
xiaopeng-travel-agent/
├── backend/app/
│   ├── main.py
│   ├── agent/          # 多轮编排、安全护栏、场景、LLM
│   ├── tools/          # 模拟工具箱
│   └── models/
├── frontend/public/    # 座舱 Demo
├── deploy/
├── docs/
├── tests/
├── Dockerfile
├── docker-compose.yml
└── run.ps1
```

## API

- `GET /api/health` — 含 `llm_configured` / `planner_default`
- `GET /api/scenarios`
- `POST /api/chat`

## 测试

```powershell
.\.venv\Scripts\python tests\test_scenarios.py
```
