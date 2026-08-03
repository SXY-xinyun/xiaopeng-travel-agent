# 技术方案报告

**作品名称：** Qoder码力星期四·小鹏 AI 出行Agent —— 双模式出行服务编排管家  
**建议篇幅：** 导出 PDF 时控制在 8–10 页（可用浏览器打印 / Typora / Pandoc）

---

## 1. 概述

本作品面向「车主自驾」与「Robotaxi 乘客服务」双模式，构建可运行、可解释的 AI 出行服务编排 Agent。系统在模拟座舱与订单工具之上完成更高层编排，而不是重复实现语音识别或自动驾驶算法。

核心主张：**真实意图理解 + 工具组合闭环 + 安全护栏不可绕过 + 可体验 Demo。**

## 2. 系统架构

```
用户 / 评委 UI（座舱 HUD）
        │
        ▼
   FastAPI API 层
        │
        ├─► 规则安全护栏（风险、禁止动作、强制工具）
        │
        ├─► 百炼千问多轮编排（意图 / 工具计划 / 结果回灌）
        │
        └─► 模拟工具箱执行 → 更新世界状态 → 结构化输出
```

- **开发侧：** Cursor / Qoder 辅助架构与迭代  
- **运行时：** 阿里云百炼通义千问 + Docker 托管（阿里云轻量应用服务器）  
- **可选：** OSS 托管静态前端

## 3. 输入输出协议

### 3.1 请求 `POST /api/chat`

```json
{
  "message": "有点困了，给我放点歌提提神吧",
  "mode": "owner",
  "scenario_id": "fatigue_driving",
  "use_llm": true
}
```

### 3.2 响应（对齐赛题结果输出能力）

| 字段 | 含义 |
|---|---|
| `reply` | 面向用户的自然语言回复 |
| `service_plan` | 结构化服务计划步骤 |
| `tool_calls` | 工具名 / 参数 / 理由 / executed\|blocked |
| `forbidden_actions` | 禁止动作 |
| `safety_tips` | 安全提示 |
| `user_intent` / `scene_type` / `risk_level` | 场景理解 |
| `world_before` / `world_after` | 状态对比 |
| `planner` / `agent_rounds` | llm 多轮或 rules 降级 |

## 4. 工具箱设计

| 类别 | 工具 |
|---|---|
| 座舱 | set_ac, set_seat, play_media, enable_fatigue_assist, prep_arrival, lock_doors, child_safety_check |
| 出行 | navigate_to, find_rest_area, find_charging_station |
| Robotaxi | get_order_status, locate_vehicle_and_passenger, suggest_safe_pickup, change_pickup_point, change_destination, comfort_assist, announce_to_passenger |
| 升级 | transfer_to_human |

工具均模拟数据与服务，保证可离线复现；接口形态可映射真实 SDK。

## 5. 多轮编排与安全规则

### 5.1 多轮闭环

最多 3 轮：规划 → 执行 → 回传 tool_results → 决定继续或 `done=true` 收敛。  
拉开与「单次 Prompt 包装聊天」的差距。

### 5.2 安全护栏（规则始终生效）

| 场景 | 策略 |
|---|---|
| 疲劳驾驶 | 拦截 play_media 主策略；强制疲劳辅助 + 休息点 |
| 亲子出行 | 强制 child_safety_check + lock_doors；禁开窗主策略 |
| 上车异常 / 施工 | 强制 suggest/change pickup；禁鼓励横穿播报 |
| 乘客求助 | 强制 transfer_to_human |
| 模式隔离 | 车主工具与 Robotaxi 工具互斥校验 |

## 6. 场景样例

覆盖赛题 8 类推荐场景；评委剧本固化：

1. 疲劳驾驶（车主）  
2. 亲子出行（车主）  
3. 上车点异常（Robotaxi）  
4. 乘客不适求助（Robotaxi）  

详见 `docs/demo_results.md`。

## 7. 模型与云服务

| 组件 | 选型 |
|---|---|
| LLM | 阿里云百炼 `qwen-plus`（OpenAI 兼容接口） |
| 托管 | Docker Compose → 阿里云轻量应用服务器 |
| 静态资源 | 默认同容器；可选 OSS + CDN |
| 密钥 | 服务器 `.env`，不入库 |

无 Key 时自动降级规则编排，保证可演示；正式评测应开启 LLM。

## 8. 可复现说明

```powershell
cd xiaopeng-travel-agent
copy .env.example .env   # 填入 DASHSCOPE_API_KEY
.\run.ps1
# 或
docker compose up -d --build
```

测试：

```powershell
.\.venv\Scripts\python tests\test_scenarios.py
```

部署细节见 `deploy/aliyun-lightweight.md`。

## 9. 创新点与小鹏特色

- 双模式统一编排协议，明确「车主自驾 / Robotaxi 乘客」身份  
- 安全护栏与模型规划解耦：强制改点、强制转人工、禁止危险播报  
- 评委一键剧本 + 工具时间线 + 世界状态前后对比，强调可解释  
- 面向未来座舱 / Robotaxi：编排层不绑定具体车控实现

## 10. 导出 PDF 步骤

1. 用 Typora / VS Code Markdown PDF / 浏览器打开本文件  
2. 打印为 PDF，页边距适中，隐藏本页「导出步骤」小节  
3. 检查总页数 ≤ 10  
