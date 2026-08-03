from __future__ import annotations

from typing import Any, Optional

from ..models.schemas import (
    AgentResponse,
    Mode,
    RiskLevel,
    SceneType,
    ServiceStep,
    ToolCall,
    WorldState,
)
from ..tools.registry import TOOL_SPECS, clone_world, execute_tool
from .llm import (
    MAX_AGENT_ROUNDS,
    configured_model,
    llm_configured,
    parse_llm_plan,
    plan_round,
    polish_reply,
)
from .safety import assess_risk, enforce_safety_plan, max_level, should_block_tool
from .scenarios import get_scenario


def _mode_label(mode: Mode) -> str:
    return "车主自驾" if mode == Mode.OWNER else "Robotaxi 乘客服务"


def _match_scene(message: str, mode: Mode, world: WorldState) -> tuple[SceneType, str, str]:
    surface = message.strip()

    if mode == Mode.OWNER:
        if any(k in message for k in ("困", "疲劳", "瞌睡", "睁不开", "提提神")):
            return (
                SceneType.FATIGUE_DRIVING,
                "用户表面要提神娱乐，真实意图是对抗疲劳；核心目标是降低驾驶风险并引导安全休息。",
                surface,
            )
        if any(k in message for k in ("宝宝", "孩子", "儿童", "小孩")) or world.vehicle.child_seat_occupied:
            return (
                SceneType.FAMILY_TRIP,
                "亲子出行温控/舒适诉求，需叠加儿童安全边界（门锁、温度、开窗风险）。",
                surface,
            )
        if any(k in message for k in ("补能", "充电", "电不够", "没电", "续航")) or world.vehicle.battery_pct <= 20:
            return (
                SceneType.LONG_RANGE_CHARGING,
                "长途续航焦虑，需要补能站检索 + 导航闭环，而非仅口头安慰。",
                surface,
            )
        if any(k in message for k in ("快到", "下车", "准备一下", "到公司", "到家了")):
            return (
                SceneType.COMMUTE_ARRIVAL,
                "通勤到达前准备：座舱复位、温控与下车欢迎流程。",
                surface,
            )
        return SceneType.GENERAL, "通用车主服务请求，按安全优先做最小必要编排。", surface

    if any(k in message for k in ("找不到", "没看到车", "车在哪", "看不见")):
        return (
            SceneType.ROBOTAXI_CANT_FIND,
            "乘客无法定位车辆，需要订单同步、相对定位播报，必要时改安全上车点。",
            surface,
        )
    if any(k in message for k in ("对面", "跑过去", "横穿", "马路对面")) or (
        world.order and world.order.passenger_side in {"马路对面", "隔离带外侧"}
    ):
        return (
            SceneType.PICKUP_ABNORMAL,
            "上车点存在穿行/临停风险，真实目标是安全会合，而不是催促乘客冒险过去。",
            surface,
        )
    if any(k in message for k in ("改去", "改目的地", "不去", "换个地方", "改下车")):
        return (
            SceneType.DEST_CHANGE,
            "行程中临时改目的地，需校验订单状态并更新 ETA。",
            surface,
        )
    if any(k in message for k in ("不舒服", "头晕", "想吐", "难受", "求助", "急救")):
        return (
            SceneType.PASSENGER_HELP,
            "乘客身体不适/求助，优先舒适辅助与安全停车策略，并升级人工。",
            surface,
        )
    return SceneType.GENERAL, "通用 Robotaxi 乘客服务请求。", surface


def _plan_tools(scene: SceneType, message: str, world: WorldState) -> list[ToolCall]:
    plans: list[ToolCall] = []

    def add(tool: str, why: str, **args: Any) -> None:
        plans.append(ToolCall(tool=tool, args=args, reason=why, status="planned"))

    if scene == SceneType.FATIGUE_DRIVING:
        add("enable_fatigue_assist", "疲劳风险升高，先启用座舱疲劳辅助组合策略", intensity="strong")
        add("set_ac", "提高通风与略降舱温，帮助保持清醒", temp_c=22, on=True)
        add("find_rest_area", "寻找最近安全休息点，而不是继续催促驾驶", prefer="服务区/安全港湾")
        add("navigate_to", "将导航途经点更新为安全休息点", destination="观澜服务区", eta_min=8)
    elif scene == SceneType.FAMILY_TRIP:
        add("child_safety_check", "儿童在座，先做安全检查", force_occupied=True)
        add("lock_doors", "确认儿童锁与车门锁定，避免误开车门")
        add("set_ac", "用空调降温替代开窗，降低高速开窗与异物风险", temp_c=23, on=True)
        add("set_seat", "后排通风轻度开启，提升儿童舒适", vent_level=2, heat_level=0)
    elif scene == SceneType.LONG_RANGE_CHARGING:
        add("find_charging_station", "电量偏低，检索高功率可用超充", min_power_kw=120)
        add("navigate_to", "导航至推荐超充站，形成补能闭环", destination="小鹏超充 · 科技园", eta_min=6)
        add("set_ac", "适度节能温控，延长到达补能站前续航", temp_c=24, on=True)
    elif scene == SceneType.COMMUTE_ARRIVAL:
        add(
            "prep_arrival",
            "到达前座舱准备，帮助用户顺畅下车",
            temp_c=23,
            actions=["回正座椅", "柔光迎宾", "关闭冥想音效", "准备手机遗忘提醒"],
        )
        add("set_ac", "维持舒适下车温度", temp_c=23, on=True)
    elif scene == SceneType.ROBOTAXI_CANT_FIND:
        add("get_order_status", "同步订单与车辆到达状态")
        add("locate_vehicle_and_passenger", "计算车辆与乘客相对位置")
        add(
            "announce_to_passenger",
            "播报车牌与会合指引，降低焦虑",
            text="您的 Robotaxi 粤B·XP888 已在 B 出口辅路等候，抬头可见车顶浅蓝灯带。",
        )
    elif scene == SceneType.PICKUP_ABNORMAL:
        add("get_order_status", "确认车辆是否已到达危险临停点")
        add("locate_vehicle_and_passenger", "确认乘客是否位于马路对面等高风险侧")
        add("suggest_safe_pickup", "生成不需横穿马路的安全上车点")
        add(
            "change_pickup_point",
            "执行改点，避免乘客冒险穿行",
            pickup="科技园地铁站出租车落客区",
            eta_min=4,
        )
        add(
            "announce_to_passenger",
            "安抚乘客并给出步行指引",
            text="请不要横穿马路。我已把上车点改到出租车落客区，步行约 2 分钟，车辆同步驶过去接您。",
        )
    elif scene == SceneType.DEST_CHANGE:
        dest = "深圳湾万象城"
        for token in ("改去", "去", "到"):
            if token in message:
                part = message.split(token, 1)[-1].strip(" ，。！?？")
                if part:
                    dest = part[:32]
                    break
        add("get_order_status", "确认乘客已在车上，允许改目的地")
        add("change_destination", "更新订单目的地并重算 ETA", destination=dest, eta_min=22)
        add(
            "announce_to_passenger",
            "向乘客确认新终点与预计到达时间",
            text=f"好的，目的地已改为{dest}，预计约 22 分钟到达。",
        )
    elif scene == SceneType.PASSENGER_HELP:
        add("comfort_assist", "先做舒缓：降温、柔风、减少晃动感", mode="nausea_care")
        add("set_ac", "快速降温通风", temp_c=22, on=True)
        add(
            "navigate_to",
            "改驶最近安全临停/急诊友好落客点（模拟）",
            destination="滨海大道应急停车带 · 安全港湾",
            eta_min=3,
        )
        add(
            "transfer_to_human",
            "身体不适属于高风险，升级人工安全坐席",
            reason="乘客头晕恶心，请求停车协助",
            priority="high",
        )
        add(
            "announce_to_passenger",
            "安抚并告知下一步",
            text="我在了。先帮您调低空调、放缓驾驶；正在前往最近安全停车点，并已通知人工坐席。",
        )
    else:
        if world.mode == Mode.OWNER:
            add("set_ac", "维持基础舒适", temp_c=23, on=True)
        else:
            add("get_order_status", "先同步订单上下文再响应")

    return plans


def _build_service_plan(
    scene: SceneType,
    tool_calls: list[ToolCall],
    transfer: bool,
    planner: str,
    rounds: int,
) -> list[ServiceStep]:
    steps: list[ServiceStep] = [
        ServiceStep(
            step=1,
            action="理解真实意图",
            owner="agent",
            detail=f"场景={scene.value}；规划器={planner}；编排轮次={rounds}",
        ),
        ServiceStep(step=2, action="安全边界评估", owner="agent", detail="规则护栏识别风险并生成禁止动作"),
    ]
    n = 3
    for tc in tool_calls:
        action = f"拦截工具 {tc.tool}" if tc.status == "blocked" else f"调用 {tc.tool}"
        steps.append(ServiceStep(step=n, action=action, owner="agent", detail=tc.reason))
        n += 1
    if transfer:
        steps.append(ServiceStep(step=n, action="转人工坐席", owner="human", detail="等待人工接管与回访"))
    else:
        steps.append(ServiceStep(step=n, action="向用户确认结果", owner="user", detail="用户可继续追加指令"))
    return steps


def _draft_reply(
    scene: SceneType,
    risk: RiskLevel,
    tool_calls: list[ToolCall],
    safety_tips: list[str],
    transfer: bool,
) -> str:
    executed = [t for t in tool_calls if t.status == "executed"]
    blocked = [t for t in tool_calls if t.status == "blocked"]

    mapping = {
        SceneType.FATIGUE_DRIVING: (
            "我更担心的是疲劳风险，而不是缺一首歌。"
            "已开启疲劳辅助并帮你导航到最近安全休息点；到服务区后再决定要不要听音乐。"
        ),
        SceneType.FAMILY_TRIP: (
            "后排有宝宝时，我建议先锁好儿童锁、用空调降温，而不是直接开窗。"
            "已经帮你完成安全检查和温控调节。"
        ),
        SceneType.LONG_RANGE_CHARGING: "续航有点紧，我按超充优先帮你选了补能站并更新导航，先保证稳稳到达。",
        SceneType.COMMUTE_ARRIVAL: "快到了。我已启动到达前准备：温度、座椅和迎宾流程都就绪，你下车会更顺。",
        SceneType.ROBOTAXI_CANT_FIND: "别着急。车辆已到达，我把车牌和相对位置发给你了；按指引走几步就能会合。",
        SceneType.PICKUP_ABNORMAL: (
            "请不要跑到马路对面。"
            "我已把上车点改到安全落客区，车辆会同步过去接你，步行大约两分钟。"
        ),
        SceneType.DEST_CHANGE: "目的地已更新，并为你重算了到达时间。行程中如需再改，随时说。",
        SceneType.PASSENGER_HELP: (
            "收到，你的不适我会优先处理。"
            "已开启舒适辅助、前往安全停车点，并转接人工坐席，请尽量深呼吸放松。"
        ),
    }
    base = mapping.get(scene, "已根据当前模式完成服务编排，有需要可以继续告诉我。")

    if blocked:
        base += f" 另外我拒绝了不安全动作（{len(blocked)} 项），把安全放在第一位。"
    if executed:
        base += f" 本次共执行 {len(executed)} 项工具调用。"
    if transfer:
        base += " 人工坐席正在接入。"
    if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} and safety_tips:
        base += f" 安全提示：{safety_tips[0]}"
    return base


def _execute_batch(
    batch: list[ToolCall],
    world: WorldState,
    scene: SceneType,
    forbidden: list[str],
    risk: RiskLevel,
) -> list[ToolCall]:
    for tc in batch:
        if tc.tool not in TOOL_SPECS:
            tc.status = "blocked"
            tc.reason = f"安全拦截：未知或不允许的工具 {tc.tool}"
            tc.result = {"ok": False, "message": tc.reason}
            continue

        mode_ok = world.mode.value in TOOL_SPECS[tc.tool]["modes"]
        if not mode_ok:
            tc.status = "blocked"
            tc.reason = f"安全拦截：工具 {tc.tool} 不适用于{_mode_label(world.mode)}"
            tc.result = {"ok": False, "message": tc.reason}
            continue

        block, why = should_block_tool(tc.tool, tc.args, forbidden, risk, scene, world)
        if block:
            tc.status = "blocked"
            tc.reason = f"安全拦截：{why or tc.reason}"
            tc.result = {"ok": False, "message": tc.reason}
            continue

        result = execute_tool(tc.tool, world, tc.args)
        tc.result = result
        tc.status = "executed" if result.get("ok") else "blocked"
        if not result.get("ok"):
            tc.reason = f"{tc.reason}（执行失败：{result.get('message')}）"
    return batch


def _dedupe_tools(calls: list[ToolCall]) -> list[ToolCall]:
    seen: set[str] = set()
    out: list[ToolCall] = []
    for tc in calls:
        key = f"{tc.tool}:{sorted(tc.args.items())}"
        if key in seen and tc.status == "planned":
            continue
        # allow re-execution records; for planned duplicates skip
        if tc.status == "planned":
            seen.add(key)
        out.append(tc)
    return out


async def _run_llm_loop(
    message: str,
    mode: Mode,
    world: WorldState,
    rule_risk: RiskLevel,
    rule_tips: list[str],
    rule_forbidden: list[str],
) -> Optional[tuple[SceneType, str, RiskLevel, list[ToolCall], str, list[str], list[str], bool, int]]:
    all_calls: list[ToolCall] = []
    history: list[dict[str, Any]] = []
    scene = SceneType.GENERAL
    intent = ""
    risk = rule_risk
    tips = list(rule_tips)
    forbidden = list(rule_forbidden)
    reply = ""
    transfer = False
    rounds_done = 0

    for round_idx in range(1, MAX_AGENT_ROUNDS + 1):
        data = await plan_round(
            message,
            mode,
            world,
            tips,
            forbidden,
            rule_risk,
            round_idx,
            history,
        )
        if not data:
            if round_idx == 1:
                return None
            break

        rounds_done = round_idx
        (
            scene,
            intent,
            llm_risk,
            batch,
            reply,
            llm_forbidden,
            llm_tips,
            transfer,
            done,
        ) = parse_llm_plan(data)

        risk = max_level(risk, max_level(rule_risk, llm_risk))
        for item in llm_forbidden:
            if item not in forbidden:
                forbidden.append(item)
        for item in llm_tips:
            if item not in tips:
                tips.append(item)

        if round_idx == 1:
            batch = enforce_safety_plan(scene, batch, world, risk, message)
            batch = _dedupe_tools(batch)

        if not batch:
            break

        _execute_batch(batch, world, scene, forbidden, risk)
        all_calls.extend(batch)
        history.append(
            {
                "round": round_idx,
                "results": [
                    {
                        "tool": t.tool,
                        "status": t.status,
                        "reason": t.reason,
                        "result": t.result,
                    }
                    for t in batch
                ],
            }
        )

        if done or round_idx >= MAX_AGENT_ROUNDS:
            break
        # continue only if something executed successfully and model may need follow-up
        if not any(t.status == "executed" for t in batch):
            break

    if rounds_done == 0:
        return None

    # final safety inject if still missing (e.g. LLM never called transfer)
    extra = enforce_safety_plan(scene, [], world, risk, message)
    missing = [t for t in extra if t.tool not in {c.tool for c in all_calls}]
    if missing:
        _execute_batch(missing, world, scene, forbidden, risk)
        all_calls.extend(missing)
        rounds_done = max(rounds_done, 1)

    return scene, intent, risk, all_calls, reply, forbidden, tips, transfer, rounds_done


async def run_agent(
    message: str,
    mode: Mode,
    scenario_id: str | None = None,
    world: WorldState | None = None,
    use_llm: bool = True,
) -> AgentResponse:
    if scenario_id:
        card = get_scenario(scenario_id)
        if card:
            world = clone_world(card.world)
            mode = card.mode
            if not message:
                message = card.sample_utterance

    if world is None:
        world = WorldState(mode=mode)
    else:
        world = clone_world(world)
        world.mode = mode

    world_before = clone_world(world)
    surface = message.strip()
    rule_risk, rule_tips, rule_forbidden = assess_risk(message, world)

    planner = "rules"
    model_name = ""
    agent_rounds = 1
    transfer = False
    reply = ""

    if use_llm and llm_configured():
        loop_result = await _run_llm_loop(
            message, mode, world, rule_risk, rule_tips, rule_forbidden
        )
        if loop_result is not None:
            (
                scene,
                intent,
                risk,
                planned,
                reply,
                forbidden,
                tips,
                transfer,
                agent_rounds,
            ) = loop_result
            planner = "llm"
            model_name = configured_model()
        else:
            scene, intent, _ = _match_scene(message, mode, world)
            risk, tips, forbidden = rule_risk, list(rule_tips), list(rule_forbidden)
            planned = enforce_safety_plan(
                scene, _plan_tools(scene, message, world), world, risk, message
            )
            _execute_batch(planned, world, scene, forbidden, risk)
            planner = "rules"
    else:
        scene, intent, _ = _match_scene(message, mode, world)
        risk, tips, forbidden = rule_risk, list(rule_tips), list(rule_forbidden)
        planned = enforce_safety_plan(
            scene, _plan_tools(scene, message, world), world, risk, message
        )
        planned = _dedupe_tools(planned)
        _execute_batch(planned, world, scene, forbidden, risk)

    transfer = transfer or any(t.tool == "transfer_to_human" and t.status == "executed" for t in planned)
    if risk == RiskLevel.CRITICAL:
        transfer = True

    if not reply:
        reply = _draft_reply(scene, risk, planned, tips, transfer)
    elif planner == "llm":
        blocked_n = sum(1 for t in planned if t.status == "blocked")
        executed_n = sum(1 for t in planned if t.status == "executed")
        if blocked_n:
            reply = reply.rstrip() + f" （已拦截 {blocked_n} 项不安全动作）"
        elif executed_n and "工具" not in reply:
            reply = reply.rstrip() + f" （已执行 {executed_n} 项服务工具）"

    if use_llm and planner == "rules" and llm_configured():
        polished = await polish_reply(
            reply,
            {
                "scene": scene.value,
                "intent": intent,
                "risk": risk.value,
                "tips": tips,
                "tools": [t.model_dump() for t in planned],
            },
        )
        if polished:
            reply = polished
            model_name = configured_model()

    plan = _build_service_plan(scene, planned, transfer, planner, agent_rounds)
    label = _mode_label(mode)
    explain = (
        f"模式={label}；场景={scene.value}；风险={risk.value}；规划器={planner}"
        + (f"({model_name})" if model_name else "")
        + f"；轮次={agent_rounds}。真实意图：{intent}"
    )

    return AgentResponse(
        mode=mode,
        scene_type=scene,
        risk_level=risk,
        user_intent=intent,
        surface_instruction=surface,
        reply=reply,
        service_plan=plan,
        tool_calls=planned,
        forbidden_actions=forbidden,
        safety_tips=tips,
        transfer_to_human=transfer,
        explain=explain,
        world_before=world_before,
        world_after=world,
        planner=planner,
        model=model_name,
        agent_rounds=agent_rounds,
        mode_label=label,
    )
