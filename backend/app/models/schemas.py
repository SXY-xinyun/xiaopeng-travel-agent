from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Mode(str, Enum):
    OWNER = "owner"
    ROBOTAXI = "robotaxi"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SceneType(str, Enum):
    FATIGUE_DRIVING = "fatigue_driving"
    FAMILY_TRIP = "family_trip"
    LONG_RANGE_CHARGING = "long_range_charging"
    COMMUTE_ARRIVAL = "commute_arrival"
    ROBOTAXI_CANT_FIND = "robotaxi_cant_find"
    PICKUP_ABNORMAL = "pickup_abnormal"
    DEST_CHANGE = "dest_change"
    PASSENGER_HELP = "passenger_help"
    GENERAL = "general"


class VehicleState(BaseModel):
    speed_kmh: float = 0
    battery_pct: float = 72
    cabin_temp_c: float = 26.5
    ac_on: bool = True
    seat_heat_level: int = 0
    seat_vent_level: int = 0
    child_seat_occupied: bool = False
    driver_fatigue_score: float = 0.2  # 0-1
    location: str = "深圳市南山区科技园"
    heading: str = "北"
    parking_safe: bool = True
    doors_locked: bool = True


class OrderState(BaseModel):
    order_id: str = "RTX-20260802-8842"
    status: str = "en_route"  # matching / en_route / arrived / onboard / completed / cancelled
    pickup: str = "科技园地铁站 B 出口"
    dropoff: str = "深圳湾体育中心"
    passenger_side: str = "马路对面"
    eta_min: int = 3
    vehicle_plate: str = "粤B·XP888"
    driverless: bool = True


class EnvEvent(BaseModel):
    weather: str = "晴，28°C"
    road_works_nearby: bool = False
    traffic: str = "缓行"
    time_of_day: str = "傍晚"
    notes: list[str] = Field(default_factory=list)


class WorldState(BaseModel):
    mode: Mode = Mode.OWNER
    vehicle: VehicleState = Field(default_factory=VehicleState)
    order: Optional[OrderState] = None
    env: EnvEvent = Field(default_factory=EnvEvent)
    user_profile: dict[str, Any] = Field(
        default_factory=lambda: {
            "name": "车主阿鹏",
            "preference": "偏凉爽、导航少打扰、优先安全",
        }
    )


class ChatRequest(BaseModel):
    message: str
    mode: Mode = Mode.OWNER
    scenario_id: Optional[str] = None
    world: Optional[WorldState] = None
    use_llm: bool = True


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    reason: str
    result: Optional[dict[str, Any]] = None
    status: str = "planned"  # planned / executed / blocked


class ServiceStep(BaseModel):
    step: int
    action: str
    owner: str  # agent / user / human
    detail: str


class AgentResponse(BaseModel):
    mode: Mode
    scene_type: SceneType
    risk_level: RiskLevel
    user_intent: str
    surface_instruction: str
    reply: str
    service_plan: list[ServiceStep]
    tool_calls: list[ToolCall]
    forbidden_actions: list[str]
    safety_tips: list[str]
    transfer_to_human: bool = False
    explain: str
    world_before: WorldState | None = None
    world_after: WorldState
    planner: str = "rules"  # llm | rules
    model: str = ""
    agent_rounds: int = 1
    mode_label: str = ""


class ScenarioCard(BaseModel):
    id: str
    title: str
    mode: Mode
    description: str
    sample_utterance: str
    world: WorldState
