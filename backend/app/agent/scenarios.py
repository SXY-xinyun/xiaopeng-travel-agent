from __future__ import annotations

from ..models.schemas import (
    EnvEvent,
    Mode,
    OrderState,
    ScenarioCard,
    VehicleState,
    WorldState,
)


def all_scenarios() -> list[ScenarioCard]:
    return [
        ScenarioCard(
            id="fatigue_driving",
            title="疲劳驾驶提醒",
            mode=Mode.OWNER,
            description="车主深夜高速返程表示犯困，Agent 需识别疲劳风险并编排休息点+座舱辅助，而非只放音乐。",
            sample_utterance="有点困了，给我放点歌提提神吧",
            world=WorldState(
                mode=Mode.OWNER,
                vehicle=VehicleState(
                    speed_kmh=98,
                    battery_pct=41,
                    cabin_temp_c=24,
                    driver_fatigue_score=0.72,
                    location="沈海高速往深圳方向 K128",
                ),
                env=EnvEvent(weather="多云，22°C", time_of_day="夜间 23:40", traffic="畅通"),
                user_profile={"name": "车主阿鹏", "preference": "安全优先"},
            ),
        ),
        ScenarioCard(
            id="family_trip",
            title="亲子出行",
            mode=Mode.OWNER,
            description="后排有儿童，车主请求开窗透气；Agent 需做儿童安全检查并给出更安全的温控方案。",
            sample_utterance="后排宝宝有点热，开一下车窗透透气",
            world=WorldState(
                mode=Mode.OWNER,
                vehicle=VehicleState(
                    speed_kmh=52,
                    battery_pct=66,
                    cabin_temp_c=29,
                    child_seat_occupied=True,
                    doors_locked=False,
                    location="深圳市南山区白石路",
                ),
                env=EnvEvent(weather="晴，31°C", time_of_day="午后", traffic="缓行"),
            ),
        ),
        ScenarioCard(
            id="long_range_charging",
            title="长途补能",
            mode=Mode.OWNER,
            description="电量下降且目的地较远，Agent 组合导航与超充站形成补能闭环。",
            sample_utterance="还要开两个小时，电好像不太够，帮我看看怎么补能",
            world=WorldState(
                mode=Mode.OWNER,
                vehicle=VehicleState(
                    speed_kmh=86,
                    battery_pct=17,
                    location="广深沿江高速",
                    cabin_temp_c=25,
                ),
                env=EnvEvent(weather="晴，29°C", time_of_day="下午", traffic="畅通"),
            ),
        ),
        ScenarioCard(
            id="commute_arrival",
            title="通勤到达前准备",
            mode=Mode.OWNER,
            description="即将到达公司，Agent 做到达前座舱准备与日程衔接。",
            sample_utterance="快到公司了，帮我准备一下下车",
            world=WorldState(
                mode=Mode.OWNER,
                vehicle=VehicleState(
                    speed_kmh=28,
                    battery_pct=54,
                    cabin_temp_c=22,
                    seat_vent_level=2,
                    location="科技园高新区路口",
                ),
                env=EnvEvent(weather="阴，26°C", time_of_day="上班高峰", traffic="拥堵"),
            ),
        ),
        ScenarioCard(
            id="robotaxi_cant_find",
            title="Robotaxi 找不到车",
            mode=Mode.ROBOTAXI,
            description="车辆已到达，乘客找不到车；Agent 定位并播报车牌/相对位置，必要时改点。",
            sample_utterance="我到上车点了，怎么没看到车？",
            world=WorldState(
                mode=Mode.ROBOTAXI,
                vehicle=VehicleState(speed_kmh=0, location="科技园地铁站附近", battery_pct=78),
                order=OrderState(
                    status="arrived",
                    pickup="科技园地铁站 B 出口",
                    passenger_side="出口内侧广场",
                    eta_min=0,
                ),
                env=EnvEvent(weather="晴，27°C", time_of_day="晚高峰", traffic="拥堵", notes=["站前车流密集"]),
                user_profile={"name": "乘客小林", "preference": "尽快上车"},
            ),
        ),
        ScenarioCard(
            id="pickup_abnormal",
            title="上车点异常",
            mode=Mode.ROBOTAXI,
            description="乘客在马路对面，存在横穿风险；Agent 应拒绝危险等待并改安全上车点。",
            sample_utterance="车在对面，我现在跑过去行吗？",
            world=WorldState(
                mode=Mode.ROBOTAXI,
                vehicle=VehicleState(speed_kmh=0, location="科技园地铁站主路侧", parking_safe=False),
                order=OrderState(
                    status="arrived",
                    pickup="科技园地铁站路边临停",
                    passenger_side="马路对面",
                    eta_min=0,
                ),
                env=EnvEvent(
                    weather="小雨，24°C",
                    time_of_day="夜晚",
                    traffic="快速车流",
                    road_works_nearby=True,
                    notes=["主路隔离栏，无斑马线"],
                ),
                user_profile={"name": "乘客小林", "preference": "安全第一"},
            ),
        ),
        ScenarioCard(
            id="dest_change",
            title="临时改目的地",
            mode=Mode.ROBOTAXI,
            description="行程中乘客改目的地，Agent 校验订单状态后更新并告知新 ETA。",
            sample_utterance="不回公司了，改去深圳湾万象城吧",
            world=WorldState(
                mode=Mode.ROBOTAXI,
                vehicle=VehicleState(speed_kmh=42, location="深南大道", battery_pct=61),
                order=OrderState(
                    status="onboard",
                    pickup="高新园",
                    dropoff="深圳湾体育中心",
                    passenger_side="已上车",
                    eta_min=16,
                ),
                env=EnvEvent(weather="晴，28°C", time_of_day="午后", traffic="缓行"),
            ),
        ),
        ScenarioCard(
            id="passenger_help",
            title="乘客不适求助",
            mode=Mode.ROBOTAXI,
            description="乘客头晕不适，Agent 做舒适辅助、降速靠边策略并转人工。",
            sample_utterance="我有点头晕想吐，能不能先停一下",
            world=WorldState(
                mode=Mode.ROBOTAXI,
                vehicle=VehicleState(speed_kmh=58, location="滨海大道高架", battery_pct=55, cabin_temp_c=27),
                order=OrderState(
                    status="onboard",
                    pickup="机场",
                    dropoff="南头古城",
                    passenger_side="已上车",
                    eta_min=20,
                ),
                env=EnvEvent(weather="闷热，30°C", time_of_day="下午", traffic="畅通"),
                user_profile={"name": "乘客小林", "preference": "舒适安全"},
            ),
        ),
    ]


def get_scenario(scenario_id: str) -> ScenarioCard | None:
    for s in all_scenarios():
        if s.id == scenario_id:
            return s
    return None
