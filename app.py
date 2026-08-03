"""ModelScope Studio entry (Gradio) — same orchestration agent, judge-friendly UI."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

import gradio as gr

from app.agent.orchestrator import run_agent
from app.agent.llm import override_api_key
from app.agent.scenarios import all_scenarios, get_scenario
from app.models.schemas import Mode

JUDGE_IDS = [
    "fatigue_driving",
    "family_trip",
    "pickup_abnormal",
    "passenger_help",
]


def _run(coro):
    return asyncio.run(coro)


def list_scenario_choices(mode: str):
    items = [s for s in all_scenarios() if s.mode.value == mode]
    return [(f"{s.title} — {s.description}", s.id) for s in items]


async def _chat_async(message: str, mode: str, scenario_id: str | None, api_key: str):
    key = (api_key or "").strip() or None
    with override_api_key(key):
        result = await run_agent(
            message=message,
            mode=Mode(mode),
            scenario_id=scenario_id or None,
            use_llm=True,
        )
    tools = "\n".join(
        f"- [{t.status}] {t.tool}: {t.reason}" for t in (result.tool_calls or [])
    ) or "（无）"
    forbidden = "\n".join(f"- {x}" for x in (result.forbidden_actions or [])) or "（无）"
    tips = "\n".join(f"- {x}" for x in (result.safety_tips or [])) or "（无）"
    plan = "\n".join(
        f"{p.step}. {p.action} — {p.detail}" for p in (result.service_plan or [])
    ) or "（无）"
    meta = (
        f"模式：{result.mode_label}\n"
        f"场景：{result.scene_type}\n"
        f"风险：{result.risk_level}\n"
        f"规划器：{result.planner}"
        + (f" / {result.model}" if result.model else "")
        + f"\n真实意图：{result.user_intent}"
    )
    detail = (
        f"### 结构化结果\n```\n{meta}\n```\n\n"
        f"### 工具调用\n{tools}\n\n"
        f"### 服务计划\n{plan}\n\n"
        f"### 禁止动作\n{forbidden}\n\n"
        f"### 安全提示\n{tips}"
    )
    return result.reply, detail


def chat(message, mode, scenario_id, api_key, history):
    message = (message or "").strip()
    history = history or []
    if not message:
        return history, "请输入指令，或先点「加载场景示例」。", ""
    sid = scenario_id if scenario_id not in (None, "", "（不指定）") else None
    reply, detail = _run(_chat_async(message, mode, sid, api_key))
    history = history + [[message, reply]]
    return history, detail, ""


def load_sample(scenario_id):
    if not scenario_id or scenario_id == "（不指定）":
        return "", "请先选择场景"
    card = get_scenario(scenario_id)
    if not card:
        return "", "场景不存在"
    return card.sample_utterance, f"已加载：{card.title}\n{card.description}"


def auto_demo(api_key, history):
    history = history or []
    details = []
    for sid in JUDGE_IDS:
        card = get_scenario(sid)
        if not card:
            continue
        user = f"【{card.title}】{card.sample_utterance}"
        reply, detail = _run(_chat_async(card.sample_utterance, card.mode.value, sid, api_key))
        history = history + [[user, reply]]
        details.append(f"## {card.title}\n{detail}")
    return history, "\n\n---\n\n".join(details)


def build_ui():
    with gr.Blocks(title="小鹏 AI 出行服务管家") as demo:
        gr.Markdown(
            """
# 小鹏 AI 出行服务管家
**Qoder码力星期四·小鹏 AI 出行Agent** · 更高层服务编排 Demo

无需 API Key 也可完整体验（规则编排 + 安全护栏）。有百炼 Key 可填入以启用千问多轮。
            """
        )
        with gr.Row():
            mode = gr.Radio(
                choices=[("车主自驾", "owner"), ("Robotaxi", "robotaxi")],
                value="owner",
                label="模式",
            )
            api_key = gr.Textbox(
                label="可选：百炼 API Key（仅本次会话使用）",
                type="password",
                placeholder="sk-... 可不填",
            )
        scenario = gr.Dropdown(
            choices=[("（不指定）", "（不指定）")] + list_scenario_choices("owner"),
            value="（不指定）",
            label="推荐场景",
        )
        with gr.Row():
            load_btn = gr.Button("加载场景示例")
            demo_btn = gr.Button("自动演示 4 场景（评委一键）", variant="primary")
        chatbot = gr.Chatbot(label="对话", height=360)
        msg = gr.Textbox(
            label="自然语言指令",
            placeholder="例如：有点困了，给我放点歌提提神吧",
        )
        send = gr.Button("编排", variant="primary")
        detail = gr.Markdown("结构化结果会显示在这里：工具链 / 禁止动作 / 安全提示")

        def on_mode_change(m):
            return gr.update(
                choices=[("（不指定）", "（不指定）")] + list_scenario_choices(m),
                value="（不指定）",
            )

        mode.change(on_mode_change, inputs=mode, outputs=scenario)
        load_btn.click(load_sample, inputs=scenario, outputs=[msg, detail])
        send.click(
            chat,
            inputs=[msg, mode, scenario, api_key, chatbot],
            outputs=[chatbot, detail, msg],
        )
        msg.submit(
            chat,
            inputs=[msg, mode, scenario, api_key, chatbot],
            outputs=[chatbot, detail, msg],
        )
        demo_btn.click(auto_demo, inputs=[api_key, chatbot], outputs=[chatbot, detail])
    return demo


demo = build_ui()

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
