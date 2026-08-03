# 复制到天池论坛的正文

**发帖标题（必须这样开头）：**

Qoder码力星期四·小鹏 AI 出行Agent —— 双模式出行服务编排管家

---

## 一、作品介绍（STAR）

### S · 场景与痛点

智能座舱与 Robotaxi 已具备空调、导航、订单、改点等基础能力，但用户一句自然语言背后往往是风险与目标的组合：

- 「有点困，放首歌」→ 真实风险是疲劳驾驶，不能只放音乐  
- 「车在对面，我跑过去」→ 真实风险是穿行事故，应改安全落客区  
- 「宝宝有点热，开窗」→ 需要儿童锁与温控，而不是简单开窗  
- 「头晕想吐」→ 必须舒适辅助 + 安全停车 + 转人工  

若 Agent 只做指令映射或普通聊天，会错过安全边界与服务闭环。

### T · 任务目标

打造更高层的 AI 出行服务编排 Agent，在已有工具之上完成：

1. 识别车主自驾 / Robotaxi 乘客真实意图与风险等级  
2. 组合工具形成可解释服务计划  
3. 对高风险动作拒绝、降级或转人工  
4. 通过 Web Demo 让评委一键复现至少 4 类典型场景  

成功标准：同时输出「自然语言回复 + 结构化服务计划 + 工具调用理由 + 禁止动作 + 安全提示」。

### A · 方案与实现

- **架构：** FastAPI + 多轮编排（意图理解 → 安全评估 → 工具执行 → 结果回灌 → 收敛回复）  
- **模型：** 阿里云百炼通义千问负责意图与工具规划；规则引擎做安全护栏  
- **工具箱：** 座舱 / 导航补能 / Robotaxi 订单改点 / 转人工等模拟工具（赛题允许自建模拟数据）  
- **安全：** 疲劳禁娱乐主策略、禁止鼓励横穿、儿童强制锁门、求助强制转人工  
- **体验：** 座舱 HUD + 评委一键剧本 + 工具时间线 + 世界状态前后对比  
- **工程：** Docker 部署；代码开源在 GitHub，公网体验由 Render 托管  

本作品强调「已有能力之上的更高层服务编排」，不是基础车控指令助手，也不是普通 Prompt 聊天机器人。

### R · 结果与价值

- 覆盖赛题推荐场景；评委剧本固化 4 个高风险闭环（2 车主 + 2 Robotaxi）  
- 公网可体验 + GitHub 可复现；自动化测试覆盖理解 / 编排 / 安全 / 转人工  
- 编排层可扩展对接真实座舱 SDK / Robotaxi 订单 API  

## 二、可体验入口

- **公网体验链接：** https://d1dd36e288fffc.lhr.life  
- **建议操作：** 打开后无需填 Key，直接点顶部「自动演示 4 场景」（2 车主 + 2 Robotaxi）。可选粘贴百炼 Key 启用千问多轮编排。  
- **健康检查：** https://d1dd36e288fffc.lhr.life/api/health  
- **GitHub 仓库：** https://github.com/SXY-xinyun/xiaopeng-travel-agent  
- **源码 zip：** https://github.com/SXY-xinyun/xiaopeng-travel-agent/releases/tag/v0.1.0  
- **长期部署（推荐，防临时隧道失效）：** https://render.com/deploy?repo=https://github.com/SXY-xinyun/xiaopeng-travel-agent 

> 本作品不在重复实现空调/导航等基础能力，而是在已有模拟工具之上做更高层服务编排：识别真实意图与风险 → 多轮规划—执行—回灌 → 规则护栏拦截危险动作，并输出可解释服务计划与安全边界。

## 三、附件说明

1. 技术方案报告 PDF（≤10 页）  
2. 完整可运行代码（见 GitHub；亦可附 zip）  
3. 运行效果：疲劳驾驶、亲子出行、上车点异常、乘客求助（截图或见仓库 `docs/demo_results.md`）  
4. 开发过程截图（可选，密钥已打码）  

## 四、本地复现

```bash
git clone https://github.com/SXY-xinyun/xiaopeng-travel-agent.git
cd xiaopeng-travel-agent
cp .env.example .env   # 填入 DASHSCOPE_API_KEY
docker compose up -d --build
# 或 Windows: .\run.ps1
```

打开 http://127.0.0.1:8000 即可体验。公网部署说明见仓库 `deploy/render.md`。
