import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.orchestrator import run_agent  # noqa: E402
from app.agent.scenarios import all_scenarios  # noqa: E402
from app.models.schemas import Mode, SceneType  # noqa: E402


def _run(coro):
    return asyncio.run(coro)


def test_fatigue_blocks_media_and_rest_path():
    r = _run(
        run_agent(
            "有点困了，给我放点歌提提神吧",
            Mode.OWNER,
            scenario_id="fatigue_driving",
            use_llm=False,
        )
    )
    assert r.scene_type == SceneType.FATIGUE_DRIVING
    assert r.risk_level.value in {"high", "critical"}
    assert "疲劳" in r.user_intent or "困" in r.user_intent
    tools_exec = {t.tool for t in r.tool_calls if t.status == "executed"}
    assert "enable_fatigue_assist" in tools_exec
    assert "find_rest_area" in tools_exec or "navigate_to" in tools_exec
    assert "play_media" not in tools_exec
    assert r.mode_label == "车主自驾"


def test_family_forces_lock_doors():
    r = _run(
        run_agent(
            "后排宝宝有点热，开一下车窗透透气",
            Mode.OWNER,
            scenario_id="family_trip",
            use_llm=False,
        )
    )
    assert r.scene_type == SceneType.FAMILY_TRIP
    tools_exec = {t.tool for t in r.tool_calls if t.status == "executed"}
    assert "lock_doors" in tools_exec
    assert "child_safety_check" in tools_exec
    assert "set_ac" in tools_exec


def test_pickup_abnormal_changes_point():
    r = _run(
        run_agent(
            "车在对面，我现在跑过去行吗？",
            Mode.ROBOTAXI,
            scenario_id="pickup_abnormal",
            use_llm=False,
        )
    )
    assert r.scene_type == SceneType.PICKUP_ABNORMAL
    assert r.mode_label.startswith("Robotaxi")
    assert any(t.tool == "change_pickup_point" and t.status == "executed" for t in r.tool_calls)
    assert any("横穿" in x or "马路" in x for x in r.forbidden_actions + r.safety_tips)
    assert r.world_before is not None
    assert r.world_after.order is not None
    assert "落客" in r.world_after.order.pickup or r.world_after.order.pickup != r.world_before.order.pickup


def test_passenger_help_transfers():
    r = _run(
        run_agent(
            "我有点头晕想吐，能不能先停一下",
            Mode.ROBOTAXI,
            scenario_id="passenger_help",
            use_llm=False,
        )
    )
    assert r.scene_type == SceneType.PASSENGER_HELP
    assert r.transfer_to_human
    assert any(t.tool == "transfer_to_human" and t.status == "executed" for t in r.tool_calls)
    assert any(t.tool == "comfort_assist" and t.status == "executed" for t in r.tool_calls)


def test_charging_and_commute_closed_loop():
    charge = _run(
        run_agent(
            "还要开两个小时，电好像不太够，帮我看看怎么补能",
            Mode.OWNER,
            scenario_id="long_range_charging",
            use_llm=False,
        )
    )
    assert charge.scene_type == SceneType.LONG_RANGE_CHARGING
    tools = {t.tool for t in charge.tool_calls if t.status == "executed"}
    assert "find_charging_station" in tools
    assert "navigate_to" in tools

    commute = _run(
        run_agent(
            "快到公司了，帮我准备一下下车",
            Mode.OWNER,
            scenario_id="commute_arrival",
            use_llm=False,
        )
    )
    assert commute.scene_type == SceneType.COMMUTE_ARRIVAL
    assert any(t.tool == "prep_arrival" and t.status == "executed" for t in commute.tool_calls)


def test_robotaxi_cant_find_and_dest_change():
    find = _run(
        run_agent(
            "我到上车点了，怎么没看到车？",
            Mode.ROBOTAXI,
            scenario_id="robotaxi_cant_find",
            use_llm=False,
        )
    )
    assert find.scene_type == SceneType.ROBOTAXI_CANT_FIND
    tools = {t.tool for t in find.tool_calls if t.status == "executed"}
    assert "get_order_status" in tools
    assert "locate_vehicle_and_passenger" in tools

    dest = _run(
        run_agent(
            "不回公司了，改去深圳湾万象城吧",
            Mode.ROBOTAXI,
            scenario_id="dest_change",
            use_llm=False,
        )
    )
    assert dest.scene_type == SceneType.DEST_CHANGE
    assert any(t.tool == "change_destination" and t.status == "executed" for t in dest.tool_calls)


def test_all_preset_scenarios_run():
    for s in all_scenarios():
        r = _run(
            run_agent(
                s.sample_utterance,
                s.mode,
                scenario_id=s.id,
                use_llm=False,
            )
        )
        assert r.reply
        assert r.service_plan
        assert r.tool_calls
        assert r.forbidden_actions is not None
        assert r.safety_tips
        assert r.world_before is not None


def test_announce_cross_road_blocked():
    from app.agent.safety import should_block_tool
    from app.models.schemas import RiskLevel, SceneType, WorldState

    world = WorldState(mode=Mode.ROBOTAXI)
    blocked, why = should_block_tool(
        "announce_to_passenger",
        {"text": "你直接跑过去横穿马路上车吧"},
        [],
        RiskLevel.HIGH,
        SceneType.PICKUP_ABNORMAL,
        world,
    )
    assert blocked
    assert "横穿" in why

    safe, _ = should_block_tool(
        "announce_to_passenger",
        {"text": "请不要横穿马路。我已把上车点改到落客区。"},
        [],
        RiskLevel.HIGH,
        SceneType.PICKUP_ABNORMAL,
        world,
    )
    assert not safe


if __name__ == "__main__":
    test_fatigue_blocks_media_and_rest_path()
    test_family_forces_lock_doors()
    test_pickup_abnormal_changes_point()
    test_passenger_help_transfers()
    test_charging_and_commute_closed_loop()
    test_robotaxi_cant_find_and_dest_change()
    test_all_preset_scenarios_run()
    test_announce_cross_road_blocked()
    print("ALL TESTS PASSED")
