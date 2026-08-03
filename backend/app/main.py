from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent.orchestrator import run_agent
from .agent.scenarios import all_scenarios, get_scenario
from .models.schemas import ChatRequest, Mode
from .tools.registry import list_tools

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "public"

app = FastAPI(
    title="小鹏 AI 出行服务编排 Agent",
    description="Qoder码力星期四·小鹏 AI 出行Agent — Owner / Robotaxi orchestration demo",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    llm = bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"))
    return {
        "ok": True,
        "service": "xiaopeng-travel-agent",
        "llm_configured": llm,
        "planner_default": "llm" if llm else "rules",
        "model": (
            os.getenv("DASHSCOPE_MODEL")
            or os.getenv("OPENAI_MODEL")
            or ("qwen-plus" if llm else "")
        ),
    }


@app.get("/api/scenarios")
def scenarios():
    return [s.model_dump(mode="json") for s in all_scenarios()]


@app.get("/api/scenarios/{scenario_id}")
def scenario_detail(scenario_id: str):
    card = get_scenario(scenario_id)
    if not card:
        return {"ok": False, "message": "scenario not found"}
    return card.model_dump(mode="json")


@app.get("/api/tools")
def tools(mode: Mode = Mode.OWNER):
    return list_tools(mode.value)


@app.post("/api/chat")
async def chat(req: ChatRequest):
    result = await run_agent(
        message=req.message,
        mode=req.mode,
        scenario_id=req.scenario_id,
        world=req.world,
        use_llm=req.use_llm,
    )
    return result.model_dump(mode="json")


if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND / "index.html")
