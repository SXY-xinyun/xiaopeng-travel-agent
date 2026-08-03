from __future__ import annotations

from typing import Any

from ..models.schemas import Mode, RiskLevel, SceneType, ToolCall, WorldState


CROSS_ROAD_ENCOURAGE = ("跑过去", "直接过马路", "穿过马路", "对面过来", "闯红灯", "现在就过马路")
CROSS_NEGATION = ("不要", "别", "禁止", "请勿", "请不要", "切勿")


def assess_risk(message: str, world: WorldState) -> tuple[RiskLevel, list[str], list[str]]:
    """Return (risk_level, safety_tips, forbidden_actions)."""
    tips: list[str] = []
    forbidden: list[str] = []
    level = RiskLevel.LOW

    fatigue_words = ["困", "疲劳", "睁不开眼", "犯困", "打瞌睡", "太累", "提提神"]
    help_words = ["不舒服", "难受", "急救", "报警", "害怕", "求助", "头晕", "恶心", "想吐"]
    child_words = ["孩子", "儿童", "宝宝", "小孩", "婴儿"]
    stop_words = ["停路边", "随便停", "应急停车", "先停一下"]

    if any(w in message for w in fatigue_words) or world.vehicle.driver_fatigue_score >= 0.55:
        level = RiskLevel.HIGH
        tips.append("检测到疲劳驾驶风险：优先引导至安全休息点，不要用娱乐掩盖困意。")
        forbidden.append("play_media 作为疲劳场景的主策略（可短暂低音量舒缓，但不能替代休息）")
        forbidden.append("继续高速巡航而不建议休息")

    if any(w in message for w in help_words):
        level = RiskLevel.CRITICAL if "急救" in message or "报警" in message else RiskLevel.HIGH
        tips.append("乘客/车主体感异常：先保障安全与舒适，必要时立即转人工。")
        forbidden.append("忽略不适主诉继续常规导航推荐")

    if any(w in message for w in child_words) or world.vehicle.child_seat_occupied:
        if level == RiskLevel.LOW:
            level = RiskLevel.MEDIUM
        tips.append("亲子出行：确认儿童锁、温控与急加速限制。")
        if not world.vehicle.doors_locked:
            level = max_level(level, RiskLevel.HIGH)
            forbidden.append("在儿童在座时保持车门解锁状态")
        forbidden.append("高速行驶时开窗作为儿童降温主策略")

    if world.mode == Mode.ROBOTAXI and world.order:
        if world.order.passenger_side in {"马路对面", "隔离带外侧", "施工围挡后"}:
            level = max_level(level, RiskLevel.HIGH)
            tips.append("上车点存在穿行风险：禁止引导乘客横穿马路，应改安全落客区。")
            forbidden.append("引导乘客横穿马路前往原上车点")
            forbidden.append("在危险路边长时间等待开门")
        if world.env.road_works_nearby:
            level = max_level(level, RiskLevel.HIGH)
            tips.append("附近有道路施工：优先改点并安抚乘客。")
            forbidden.append("在施工点附近维持原危险上车点")
        if not world.vehicle.parking_safe and world.order.status == "arrived":
            level = max_level(level, RiskLevel.HIGH)
            tips.append("当前临停点不安全，应改安全落客区。")

    if any(w in message for w in stop_words) and world.vehicle.speed_kmh > 40:
        level = max_level(level, RiskLevel.HIGH)
        tips.append("高速/快速路禁止随意路边停车，应导航至服务区或应急停车带。")
        forbidden.append("在非安全区域执行路边停车")

    if world.vehicle.battery_pct <= 18 and world.mode == Mode.OWNER:
        level = max_level(level, RiskLevel.MEDIUM)
        tips.append("电量偏低，补能规划应优先于娱乐与绕路。")

    if "施工" in message or world.env.road_works_nearby:
        tips.append("关注道路事件，必要时重规划路线或改上车点。")

    if not tips:
        tips.append("保持情境感知：在执行前核对模式、车辆状态与安全边界。")

    return level, tips, forbidden


def max_level(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    return order[max(order.index(a), order.index(b))]


def should_block_tool(
    tool: str,
    args: dict[str, Any],
    forbidden: list[str],
    risk: RiskLevel,
    scene: SceneType,
    world: WorldState,
) -> tuple[bool, str]:
    for item in forbidden:
        if tool in item.split()[0] or tool in item:
            # play_media mentioned in forbidden → block
            if tool == "play_media" and "play_media" in item:
                return True, item
            if tool != "play_media" and tool in item:
                return True, item

    if scene == SceneType.FATIGUE_DRIVING and tool == "play_media":
        return True, "疲劳场景禁止以播放媒体作为主策略"

    if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} and tool == "play_media":
        return True, "高风险场景禁止以娱乐媒体作为主响应"

    if tool == "announce_to_passenger":
        text = str(args.get("text", ""))
        if any(h in text for h in CROSS_ROAD_ENCOURAGE):
            return True, "禁止播报文案引导乘客横穿马路"
        if "横穿" in text and not any(n in text for n in CROSS_NEGATION):
            return True, "禁止播报文案引导乘客横穿马路"

    if world.mode == Mode.OWNER and scene == SceneType.FAMILY_TRIP:
        if tool == "set_ac" and args.get("on") is False and world.vehicle.child_seat_occupied:
            return True, "儿童在座时禁止关闭空调作为降温替代"

    return False, ""


def enforce_safety_plan(
    scene: SceneType,
    planned: list[ToolCall],
    world: WorldState,
    risk: RiskLevel,
    message: str,
) -> list[ToolCall]:
    """Post-process LLM/rule plans: inject mandatory safety tools."""
    names = {t.tool for t in planned}
    extra: list[ToolCall] = []

    # Child: lock doors first
    if scene == SceneType.FAMILY_TRIP or world.vehicle.child_seat_occupied:
        if "lock_doors" not in names:
            extra.append(
                ToolCall(
                    tool="lock_doors",
                    args={},
                    reason="安全强制：儿童在座必须确认车门/儿童锁",
                    status="planned",
                )
            )
        if "child_safety_check" not in names:
            extra.append(
                ToolCall(
                    tool="child_safety_check",
                    args={"force_occupied": True},
                    reason="安全强制：儿童乘车检查",
                    status="planned",
                )
            )

    # Passenger help / critical: must transfer
    help_like = scene == SceneType.PASSENGER_HELP or risk == RiskLevel.CRITICAL
    if help_like and "transfer_to_human" not in names:
        extra.append(
            ToolCall(
                tool="transfer_to_human",
                args={"reason": "高风险求助/身体不适，强制升级人工", "priority": "high"},
                reason="安全强制：求助场景必须转人工",
                status="planned",
            )
        )

    # Pickup abnormal / road works: prefer change pickup
    if scene == SceneType.PICKUP_ABNORMAL or (
        world.mode == Mode.ROBOTAXI
        and world.order
        and (world.env.road_works_nearby or not world.vehicle.parking_safe)
        and world.order.passenger_side in {"马路对面", "隔离带外侧", "施工围挡后"}
    ):
        if "suggest_safe_pickup" not in names:
            extra.append(
                ToolCall(
                    tool="suggest_safe_pickup",
                    args={},
                    reason="安全强制：危险上车点先生成安全方案",
                    status="planned",
                )
            )
        if "change_pickup_point" not in names:
            extra.append(
                ToolCall(
                    tool="change_pickup_point",
                    args={"pickup": "科技园地铁站出租车落客区", "eta_min": 4},
                    reason="安全强制：改到安全落客区，禁止维持危险上车点",
                    status="planned",
                )
            )

    # Fatigue: ensure rest path exists
    if scene == SceneType.FATIGUE_DRIVING:
        if "enable_fatigue_assist" not in names:
            extra.append(
                ToolCall(
                    tool="enable_fatigue_assist",
                    args={"intensity": "strong"},
                    reason="安全强制：开启疲劳辅助",
                    status="planned",
                )
            )
        if "find_rest_area" not in names and "navigate_to" not in names:
            extra.append(
                ToolCall(
                    tool="find_rest_area",
                    args={"prefer": "服务区/安全港湾"},
                    reason="安全强制：导航至安全休息点",
                    status="planned",
                )
            )

    # Prepend extras so safety tools run early
    if not extra:
        return planned
    return extra + planned
