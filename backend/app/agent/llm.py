from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

import httpx

from ..models.schemas import Mode, RiskLevel, SceneType, ToolCall, WorldState
from ..tools.registry import list_tools

MAX_AGENT_ROUNDS = 3


def llm_configured() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"))


def configured_model() -> str:
    return os.getenv("DASHSCOPE_MODEL") or os.getenv("OPENAI_MODEL") or "qwen-plus"


def _api_config() -> tuple[str, str, str]:
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    base = os.getenv(
        "OPENAI_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    return api_key, base, configured_model()


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise
        return json.loads(m.group(0))


async def chat_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.2,
) -> Optional[dict[str, Any]]:
    if not llm_configured():
        return None

    api_key, base, model = _api_config()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                },
            )
            if resp.status_code >= 400:
                resp = await client.post(
                    f"{base.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {
                                "role": "user",
                                "content": user + "\n\n请只输出合法 JSON，不要 Markdown。",
                            },
                        ],
                        "temperature": temperature,
                    },
                )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _extract_json(content)
    except Exception:
        return None


PLAN_SYSTEM = """你是小鹏 AI 出行服务编排 Agent（运行在阿里云百炼/通义千问）。
你在「已有座舱/导航/Robotaxi 工具」之上做更高层服务编排，不是普通聊天机器人。

硬性原则：
1. 识别真实意图，而非表面指令（如“放歌提神”→疲劳风险）。
2. 组合多个工具形成服务闭环，顺序清晰。
3. 安全优先：疲劳不用娱乐当主策略；禁止引导横穿；儿童先锁门温控；求助必须转人工。
4. 只能使用 available_tools 中的工具名。
5. 你可能收到上一轮 tool_results；请据此决定是否继续调用工具，或 done=true 收敛最终回复。
6. 输出单个 JSON：
{
  "scene_type": "fatigue_driving|family_trip|long_range_charging|commute_arrival|robotaxi_cant_find|pickup_abnormal|dest_change|passenger_help|general",
  "user_intent": "真实意图",
  "risk_level": "low|medium|high|critical",
  "reply": "面向用户回复<=120字",
  "tool_calls": [{"tool":"名","args":{},"reason":"理由"}],
  "forbidden_actions": ["禁止动作"],
  "safety_tips": ["安全提示"],
  "transfer_to_human": false,
  "done": false
}
若服务已闭环，设 done=true 且 tool_calls 可以为空。
"""


async def plan_round(
    message: str,
    mode: Mode,
    world: WorldState,
    safety_tips: list[str],
    forbidden_actions: list[str],
    rule_risk: RiskLevel,
    round_idx: int,
    history: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    tools = list_tools(mode.value)
    payload = {
        "round": round_idx,
        "max_rounds": MAX_AGENT_ROUNDS,
        "user_message": message,
        "mode": mode.value,
        "mode_label": "车主自驾" if mode == Mode.OWNER else "Robotaxi乘客服务",
        "world_state": world.model_dump(mode="json"),
        "available_tools": tools,
        "rule_safety_tips": safety_tips,
        "rule_forbidden_actions": forbidden_actions,
        "rule_risk_level": rule_risk.value,
        "tool_history": history,
        "instruction": (
            "结合世界状态、规则安全提示与历史工具结果输出本轮编排。"
            "若规则已提示疲劳/横穿/儿童/求助等高风险，必须尊重并加强。"
            "第一轮应给出核心工具链；后续轮仅在需要基于结果补调用时继续。"
        ),
    }
    return await chat_json(PLAN_SYSTEM, json.dumps(payload, ensure_ascii=False), temperature=0.2)


def parse_llm_plan(
    data: dict[str, Any],
) -> tuple[SceneType, str, RiskLevel, list[ToolCall], str, list[str], list[str], bool, bool]:
    scene_raw = str(data.get("scene_type", "general"))
    try:
        scene = SceneType(scene_raw)
    except ValueError:
        scene = SceneType.GENERAL

    intent = str(data.get("user_intent") or "模型识别的服务意图")
    try:
        risk = RiskLevel(str(data.get("risk_level", "low")))
    except ValueError:
        risk = RiskLevel.LOW

    reply = str(data.get("reply") or "").strip()
    forbidden = [str(x) for x in (data.get("forbidden_actions") or [])]
    tips = [str(x) for x in (data.get("safety_tips") or [])]
    transfer = bool(data.get("transfer_to_human", False))
    done = bool(data.get("done", False))

    planned: list[ToolCall] = []
    for item in data.get("tool_calls") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("tool") or "").strip()
        if not name:
            continue
        args = item.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        reason = str(item.get("reason") or "模型规划调用")
        planned.append(ToolCall(tool=name, args=args, reason=reason, status="planned"))

    if not planned:
        done = True

    return scene, intent, risk, planned, reply, forbidden, tips, transfer, done


async def polish_reply(draft_reply: str, context: dict[str, Any]) -> Optional[str]:
    if not llm_configured():
        return None
    system = (
        "你是小鹏 AI 出行服务管家。润色面向用户的回复。"
        "要求：自然、克制、安全优先、可解释；不要编造未发生的工具结果；不超过 120 字。"
        '只输出 JSON：{"reply": "..."}'
    )
    data = await chat_json(
        system,
        json.dumps({"draft": draft_reply, "context": context}, ensure_ascii=False),
        temperature=0.4,
    )
    if not data:
        return None
    reply = str(data.get("reply") or "").strip()
    return reply or None
