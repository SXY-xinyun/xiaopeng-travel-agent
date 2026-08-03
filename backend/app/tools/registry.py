from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from ..models.schemas import WorldState


ToolFn = Callable[[WorldState, dict[str, Any]], dict[str, Any]]


def _ok(message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": True, "message": message, **extra}


def set_ac(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    temp = float(args.get("temp_c", 23))
    on = bool(args.get("on", True))
    world.vehicle.ac_on = on
    world.vehicle.cabin_temp_c = temp
    return _ok(f"空调已{'开启' if on else '关闭'}，目标温度 {temp}°C", temp_c=temp, on=on)


def set_seat(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    heat = int(args.get("heat_level", 0))
    vent = int(args.get("vent_level", 0))
    world.vehicle.seat_heat_level = max(0, min(3, heat))
    world.vehicle.seat_vent_level = max(0, min(3, vent))
    return _ok(
        f"座椅调节完成：加热 {world.vehicle.seat_heat_level} 档 / 通风 {world.vehicle.seat_vent_level} 档",
        heat_level=world.vehicle.seat_heat_level,
        vent_level=world.vehicle.seat_vent_level,
    )


def play_media(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    content = str(args.get("content", "轻松电台"))
    volume = int(args.get("volume", 3))
    return _ok(f"开始播放：{content}，音量 {volume}", content=content, volume=volume)


def enable_fatigue_assist(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    intensity = str(args.get("intensity", "standard"))
    world.vehicle.driver_fatigue_score = max(0.0, world.vehicle.driver_fatigue_score - 0.15)
    return _ok(
        "已开启疲劳驾驶辅助：座舱通风加强、提示音间隔缩短、建议 ASAP 休息",
        intensity=intensity,
        fatigue_score=world.vehicle.driver_fatigue_score,
    )


def navigate_to(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    dest = str(args.get("destination", ""))
    avoid = args.get("avoid", [])
    return _ok(f"导航已更新至「{dest}」", destination=dest, avoid=avoid, eta_min=args.get("eta_min", 18))


def find_rest_area(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    prefer = str(args.get("prefer", "最近安全停车点"))
    spots = [
        {"name": "南光高速 · 观澜服务区", "eta_min": 8, "safe": True},
        {"name": "松岗临停点 A", "eta_min": 4, "safe": False},
        {"name": "民治路边临时停车位", "eta_min": 3, "safe": False},
    ]
    safe = [s for s in spots if s["safe"]]
    chosen = safe[0] if safe else spots[0]
    return _ok(f"推荐休息点：{chosen['name']}（约 {chosen['eta_min']} 分钟）", prefer=prefer, candidates=spots, chosen=chosen)


def find_charging_station(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    min_power = int(args.get("min_power_kw", 120))
    stations = [
        {"name": "小鹏超充 · 深圳湾", "power_kw": 480, "eta_min": 12, "available": 3},
        {"name": "小鹏超充 · 科技园", "power_kw": 180, "eta_min": 6, "available": 1},
        {"name": "公共快充 · 西丽", "power_kw": 60, "eta_min": 5, "available": 2},
    ]
    filtered = [s for s in stations if s["power_kw"] >= min_power and s["available"] > 0]
    chosen = filtered[0] if filtered else stations[0]
    return _ok(
        f"推荐补能站：{chosen['name']}（{chosen['power_kw']}kW，约 {chosen['eta_min']} 分钟）",
        min_power_kw=min_power,
        candidates=stations,
        chosen=chosen,
    )


def prep_arrival(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    actions = args.get(
        "actions",
        ["降温至舒适温度", "座椅回正", "关闭冥想音效", "打开车门欢迎灯"],
    )
    world.vehicle.cabin_temp_c = float(args.get("temp_c", 23))
    return _ok("到达前准备已启动", actions=actions)


def child_safety_check(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    occupied = world.vehicle.child_seat_occupied or bool(args.get("force_occupied", False))
    world.vehicle.child_seat_occupied = occupied
    issues = []
    if occupied and world.vehicle.speed_kmh > 0 and not world.vehicle.doors_locked:
        issues.append("车门未锁，存在儿童误开车门风险")
    if occupied and world.vehicle.cabin_temp_c >= 28:
        issues.append("舱内偏热，儿童热应激风险上升")
    return _ok(
        "儿童安全检查完成",
        child_seat_occupied=occupied,
        issues=issues,
        locked=world.vehicle.doors_locked,
    )


def lock_doors(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    world.vehicle.doors_locked = True
    return _ok("车门已锁定，儿童锁已确认开启")


def get_order_status(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    if not world.order:
        return {"ok": False, "message": "当前无 Robotaxi 订单"}
    return _ok("订单状态已同步", order=world.order.model_dump())


def locate_vehicle_and_passenger(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    if not world.order:
        return {"ok": False, "message": "当前无 Robotaxi 订单"}
    return _ok(
        "已定位车辆与乘客相对位置",
        vehicle_at=world.order.pickup,
        passenger_side=world.order.passenger_side,
        plate=world.order.vehicle_plate,
        distance_hint="乘客在马路对面，直线约 35 米，中间有隔离栏",
    )


def suggest_safe_pickup(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    points = [
        {"name": "科技园地铁站出租车落客区", "walk_min": 2, "crossing": False, "safe": True},
        {"name": "当前上车点（马路边）", "walk_min": 0, "crossing": True, "safe": False},
        {"name": "科苑南路辅路港湾", "walk_min": 3, "crossing": False, "safe": True},
    ]
    chosen = next(p for p in points if p["safe"])
    return _ok("已生成安全上车点方案", candidates=points, chosen=chosen)


def change_pickup_point(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    if not world.order:
        return {"ok": False, "message": "当前无 Robotaxi 订单"}
    new_point = str(args.get("pickup", "科技园地铁站出租车落客区"))
    world.order.pickup = new_point
    world.order.status = "en_route"
    world.order.eta_min = int(args.get("eta_min", 4))
    world.order.passenger_side = "同侧落客区"
    return _ok(f"上车点已改为「{new_point}」", order=world.order.model_dump())


def change_destination(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    if not world.order:
        return {"ok": False, "message": "当前无 Robotaxi 订单"}
    dest = str(args.get("destination", ""))
    world.order.dropoff = dest
    world.order.eta_min = int(args.get("eta_min", 22))
    return _ok(f"目的地已更新为「{dest}」", order=world.order.model_dump())


def comfort_assist(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    mode = str(args.get("mode", "calm"))
    world.vehicle.cabin_temp_c = 23.0
    world.vehicle.ac_on = True
    return _ok(
        "已启用乘客舒适辅助：空调柔风、座椅微倾、播放舒缓提示",
        mode=mode,
        temp_c=world.vehicle.cabin_temp_c,
    )


def transfer_to_human(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    reason = str(args.get("reason", "需要人工介入"))
    priority = str(args.get("priority", "normal"))
    return _ok("已转接人工客服 / 安全坐席", reason=reason, priority=priority, ticket_id="HS-77821")


def announce_to_passenger(world: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    text = str(args.get("text", ""))
    return _ok("已通过车内/手机播报通知乘客", text=text)


TOOL_SPECS: dict[str, dict[str, Any]] = {
    "set_ac": {
        "desc": "调节空调开关与目标温度",
        "fn": set_ac,
        "modes": {"owner", "robotaxi"},
    },
    "set_seat": {
        "desc": "调节座椅加热/通风",
        "fn": set_seat,
        "modes": {"owner", "robotaxi"},
    },
    "play_media": {
        "desc": "播放媒体内容（非疲劳场景慎用）",
        "fn": play_media,
        "modes": {"owner", "robotaxi"},
    },
    "enable_fatigue_assist": {
        "desc": "开启疲劳驾驶辅助组合策略",
        "fn": enable_fatigue_assist,
        "modes": {"owner"},
    },
    "navigate_to": {
        "desc": "更新导航目的地或途经点",
        "fn": navigate_to,
        "modes": {"owner", "robotaxi"},
    },
    "find_rest_area": {
        "desc": "查找安全休息/停车点",
        "fn": find_rest_area,
        "modes": {"owner"},
    },
    "find_charging_station": {
        "desc": "查找可用补能站并推荐",
        "fn": find_charging_station,
        "modes": {"owner"},
    },
    "prep_arrival": {
        "desc": "到达前座舱准备",
        "fn": prep_arrival,
        "modes": {"owner"},
    },
    "child_safety_check": {
        "desc": "儿童乘车安全检查",
        "fn": child_safety_check,
        "modes": {"owner"},
    },
    "lock_doors": {
        "desc": "锁定车门并确认儿童锁",
        "fn": lock_doors,
        "modes": {"owner", "robotaxi"},
    },
    "get_order_status": {
        "desc": "查询 Robotaxi 订单状态",
        "fn": get_order_status,
        "modes": {"robotaxi"},
    },
    "locate_vehicle_and_passenger": {
        "desc": "定位车辆与乘客相对位置",
        "fn": locate_vehicle_and_passenger,
        "modes": {"robotaxi"},
    },
    "suggest_safe_pickup": {
        "desc": "推荐安全上车点",
        "fn": suggest_safe_pickup,
        "modes": {"robotaxi"},
    },
    "change_pickup_point": {
        "desc": "修改 Robotaxi 上车点",
        "fn": change_pickup_point,
        "modes": {"robotaxi"},
    },
    "change_destination": {
        "desc": "修改 Robotaxi 目的地",
        "fn": change_destination,
        "modes": {"robotaxi"},
    },
    "comfort_assist": {
        "desc": "乘客不适时的舒适辅助",
        "fn": comfort_assist,
        "modes": {"robotaxi"},
    },
    "transfer_to_human": {
        "desc": "转人工客服/安全坐席",
        "fn": transfer_to_human,
        "modes": {"owner", "robotaxi"},
    },
    "announce_to_passenger": {
        "desc": "向乘客播报通知",
        "fn": announce_to_passenger,
        "modes": {"robotaxi"},
    },
}


def list_tools(mode: str) -> list[dict[str, str]]:
    return [
        {"name": name, "description": spec["desc"]}
        for name, spec in TOOL_SPECS.items()
        if mode in spec["modes"]
    ]


def execute_tool(name: str, world: WorldState, args: dict[str, Any] | None = None) -> dict[str, Any]:
    if name not in TOOL_SPECS:
        return {"ok": False, "message": f"未知工具: {name}"}
    fn: ToolFn = TOOL_SPECS[name]["fn"]
    return fn(world, args or {})


def clone_world(world: WorldState) -> WorldState:
    return WorldState.model_validate(deepcopy(world.model_dump()))
