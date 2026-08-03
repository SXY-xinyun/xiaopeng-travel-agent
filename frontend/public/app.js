const JUDGE_SCRIPT = [
  { id: "fatigue_driving", title: "疲劳驾驶提醒" },
  { id: "family_trip", title: "亲子出行" },
  { id: "pickup_abnormal", title: "上车点异常" },
  { id: "passenger_help", title: "乘客不适求助" },
];

const KEY_STORAGE = "xp_demo_api_key";

const state = {
  mode: "owner",
  scenarioId: null,
  world: null,
  scenarios: [],
  demoRunning: false,
  apiKey: sessionStorage.getItem(KEY_STORAGE) || "",
};

const els = {
  scenarioList: document.getElementById("scenarioList"),
  messages: document.getElementById("messages"),
  form: document.getElementById("chatForm"),
  input: document.getElementById("userInput"),
  modeOwner: document.getElementById("modeOwner"),
  modeTaxi: document.getElementById("modeTaxi"),
  riskBadge: document.getElementById("riskBadge"),
  plannerBadge: document.getElementById("plannerBadge"),
  sceneType: document.getElementById("sceneType"),
  modelName: document.getElementById("modelName"),
  modeLabel: document.getElementById("modeLabel"),
  intentText: document.getElementById("intentText"),
  planList: document.getElementById("planList"),
  toolTimeline: document.getElementById("toolTimeline"),
  safetyList: document.getElementById("safetyList"),
  worldDiff: document.getElementById("worldDiff"),
  speedVal: document.getElementById("speedVal"),
  batteryVal: document.getElementById("batteryVal"),
  tempVal: document.getElementById("tempVal"),
  locVal: document.getElementById("locVal"),
  orderVal: document.getElementById("orderVal"),
  healthChip: document.getElementById("healthChip"),
  autoDemoBtn: document.getElementById("autoDemoBtn"),
  mapHint: document.getElementById("mapHint"),
  mapCaption: document.getElementById("mapCaption"),
  apiKeyInput: document.getElementById("apiKeyInput"),
  apiKeySave: document.getElementById("apiKeySave"),
  apiKeyClear: document.getElementById("apiKeyClear"),
};

function refreshKeyUi() {
  if (els.apiKeyInput) {
    els.apiKeyInput.value = state.apiKey ? "••••••••••••" : "";
    els.apiKeyInput.dataset.masked = state.apiKey ? "1" : "0";
  }
  updateHealthChip();
}

function updateHealthChip(serverConfigured) {
  if (state.apiKey) {
    els.healthChip.textContent = "浏览器 Key · 将走 LLM";
    els.healthChip.className = "health-chip on";
    return;
  }
  if (serverConfigured) {
    els.healthChip.textContent = "服务端 LLM 已连接";
    els.healthChip.className = "health-chip on";
    return;
  }
  els.healthChip.textContent = "免 Key 演示 · 规则编排可用";
  els.healthChip.className = "health-chip off";
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function addBubble(role, text, tag) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  if (tag) {
    const t = document.createElement("div");
    t.className = "tag";
    t.textContent = tag;
    div.appendChild(t);
  }
  const p = document.createElement("div");
  p.textContent = text;
  div.appendChild(p);
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function renderWorld(world) {
  if (!world) return;
  const v = world.vehicle || {};
  els.speedVal.textContent = Math.round(v.speed_kmh ?? 0);
  els.batteryVal.textContent = `${Math.round(v.battery_pct ?? 0)}%`;
  els.tempVal.textContent = `${(v.cabin_temp_c ?? 0).toFixed(1)}°C`;
  els.locVal.textContent = v.location || "--";
  if (world.order) {
    els.orderVal.textContent = `${world.order.status} · ${world.order.vehicle_plate || ""}`;
    els.mapHint.classList.remove("hidden");
    const side = world.order.passenger_side || "";
    els.mapCaption.textContent = `上车点：${world.order.pickup} · 乘客位置：${side}`;
  } else {
    els.orderVal.textContent = state.mode === "robotaxi" ? "无订单" : "自驾模式";
    els.mapHint.classList.add("hidden");
  }
}

function diffWorld(before, after) {
  if (!before || !after) {
    els.worldDiff.innerHTML = `<span class="muted">暂无对比数据</span>`;
    return;
  }
  const rows = [];
  const push = (label, a, b) => {
    const chg = String(a) !== String(b);
    rows.push(
      `<div class="row"><span>${label}</span><span>${a ?? "—"}</span><span class="${chg ? "chg" : ""}">${b ?? "—"}</span></div>`
    );
  };
  push("电量", `${before.vehicle?.battery_pct}%`, `${after.vehicle?.battery_pct}%`);
  push("舱温", `${before.vehicle?.cabin_temp_c}°C`, `${after.vehicle?.cabin_temp_c}°C`);
  push("车门锁", before.vehicle?.doors_locked ? "锁定" : "未锁", after.vehicle?.doors_locked ? "锁定" : "未锁");
  push("疲劳分", before.vehicle?.driver_fatigue_score, after.vehicle?.driver_fatigue_score);
  if (before.order || after.order) {
    push("上车点", before.order?.pickup, after.order?.pickup);
    push("目的地", before.order?.dropoff, after.order?.dropoff);
    push("乘客侧", before.order?.passenger_side, after.order?.passenger_side);
  }
  els.worldDiff.innerHTML =
    `<div class="row"><span></span><span class="muted">前</span><span class="muted">后</span></div>` +
    rows.join("");
}

function renderInsight(data) {
  const risk = (data.risk_level || "low").toLowerCase();
  els.riskBadge.textContent = `风险 ${risk.toUpperCase()}`;
  els.riskBadge.className = `badge ${risk}`;
  const planner = (data.planner || "rules").toLowerCase();
  els.plannerBadge.textContent = `规划器 ${planner.toUpperCase()}`;
  els.plannerBadge.className = `badge ${planner === "llm" ? "llm" : "low"}`;
  els.sceneType.textContent = `${data.scene_type || "—"} · 轮次 ${data.agent_rounds || 1}`;
  els.modelName.textContent = data.model ? `模型 ${data.model}` : "";
  els.modeLabel.textContent = data.mode_label || (data.mode === "robotaxi" ? "Robotaxi 乘客服务" : "车主自驾");
  els.intentText.textContent = data.user_intent || "—";

  els.toolTimeline.innerHTML = "";
  (data.tool_calls || []).forEach((t, idx) => {
    const li = document.createElement("li");
    if (t.status === "blocked") li.classList.add("blocked");
    li.innerHTML = `<div class="t-name">${idx + 1}. <span class="${t.status === "executed" ? "tool-ok" : "tool-blocked"}">[${t.status}]</span> ${t.tool}</div><div class="t-reason">${t.reason || ""}</div>`;
    els.toolTimeline.appendChild(li);
  });
  if (!(data.tool_calls || []).length) {
    els.toolTimeline.innerHTML = `<li class="muted">暂无工具调用</li>`;
  }

  els.planList.innerHTML = "";
  (data.service_plan || []).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = `${step.action} — ${step.detail}`;
    els.planList.appendChild(li);
  });

  els.safetyList.innerHTML = "";
  const forbidden = data.forbidden_actions || [];
  const tips = data.safety_tips || [];
  if (!forbidden.length && !tips.length) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "暂无额外安全拦截";
    els.safetyList.appendChild(li);
  }
  forbidden.forEach((f) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="tool-blocked">禁止</span> ${f}`;
    els.safetyList.appendChild(li);
  });
  tips.forEach((tip) => {
    const li = document.createElement("li");
    li.textContent = tip;
    els.safetyList.appendChild(li);
  });

  diffWorld(data.world_before, data.world_after);
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    updateHealthChip(Boolean(data.llm_configured));
  } catch {
    els.healthChip.textContent = "服务未连接";
    els.healthChip.className = "health-chip off";
  }
}

async function loadScenarios() {
  const res = await fetch("/api/scenarios");
  state.scenarios = await res.json();
  els.scenarioList.innerHTML = "";
  state.scenarios
    .filter((s) => s.mode === state.mode)
    .forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "scenario-item" + (state.scenarioId === s.id ? " active" : "");
      btn.innerHTML = `<strong>${s.title}</strong><small>${s.description}</small>`;
      btn.addEventListener("click", () => selectScenario(s));
      els.scenarioList.appendChild(btn);
    });
}

function selectScenario(s) {
  state.scenarioId = s.id;
  state.world = s.world;
  state.mode = s.mode;
  els.input.value = s.sample_utterance;
  els.messages.innerHTML = "";
  addBubble("agent", `场景已加载：${s.title}。可以直接发送示例指令，或修改后再编排。`, "SCENARIO");
  renderWorld(s.world);
  renderInsight({
    risk_level: "low",
    scene_type: s.id,
    user_intent: s.description,
    mode_label: s.mode === "robotaxi" ? "Robotaxi 乘客服务" : "车主自驾",
    service_plan: [],
    tool_calls: [],
    forbidden_actions: [],
    safety_tips: [],
    world_before: s.world,
    world_after: s.world,
  });
  loadScenarios();
  syncModeButtons();
}

function syncModeButtons() {
  els.modeOwner.classList.toggle("active", state.mode === "owner");
  els.modeTaxi.classList.toggle("active", state.mode === "robotaxi");
}

async function sendChat(message, scenarioId) {
  const payload = {
    message,
    mode: state.mode,
    scenario_id: scenarioId ?? state.scenarioId,
    world: state.world,
    use_llm: true,
  };
  if (state.apiKey) payload.api_key = state.apiKey;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

els.modeOwner.addEventListener("click", () => {
  if (state.demoRunning) return;
  state.mode = "owner";
  state.scenarioId = null;
  state.world = null;
  syncModeButtons();
  loadScenarios();
  addBubble("agent", "已切换到车主自驾模式。可从左侧选择场景，或直接输入指令。", "MODE");
});

els.modeTaxi.addEventListener("click", () => {
  if (state.demoRunning) return;
  state.mode = "robotaxi";
  state.scenarioId = null;
  state.world = null;
  syncModeButtons();
  loadScenarios();
  addBubble("agent", "已切换到 Robotaxi 乘客服务模式。可从左侧选择场景，或直接输入指令。", "MODE");
});

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (state.demoRunning) return;
  const message = els.input.value.trim();
  if (!message) return;

  addBubble("user", message);
  els.input.value = "";
  const btn = els.form.querySelector("button");
  btn.disabled = true;

  try {
    const data = await sendChat(message);
    addBubble("agent", data.reply, data.transfer_to_human ? "TRANSFER" : "AGENT");
    renderInsight(data);
    state.world = data.world_after;
    state.mode = data.mode;
    renderWorld(data.world_after);
    syncModeButtons();
  } catch (err) {
    addBubble("agent", `请求失败：${err.message}`, "ERROR");
  } finally {
    btn.disabled = false;
  }
});

els.autoDemoBtn.addEventListener("click", async () => {
  if (state.demoRunning) return;
  state.demoRunning = true;
  els.autoDemoBtn.disabled = true;
  els.form.querySelector("button").disabled = true;
  els.messages.innerHTML = "";
  addBubble("agent", "开始评委剧本自动演示：将依次跑通 4 个高风险闭环场景。", "DEMO");

  try {
    for (const step of JUDGE_SCRIPT) {
      const card = state.scenarios.find((s) => s.id === step.id);
      if (!card) continue;
      selectScenario(card);
      await sleep(600);
      addBubble("user", card.sample_utterance, step.title);
      const data = await sendChat(card.sample_utterance, card.id);
      addBubble(
        "agent",
        data.reply,
        `${data.planner?.toUpperCase() || "AGENT"} · ${data.risk_level}`
      );
      renderInsight(data);
      state.world = data.world_after;
      state.mode = data.mode;
      renderWorld(data.world_after);
      syncModeButtons();
      await sleep(900);
    }
    addBubble("agent", "四个评委场景演示完成。可继续手动点选其他场景深入体验。", "DONE");
  } catch (err) {
    addBubble("agent", `自动演示中断：${err.message}`, "ERROR");
  } finally {
    state.demoRunning = false;
    els.autoDemoBtn.disabled = false;
    els.form.querySelector("button").disabled = false;
  }
});

if (els.apiKeyInput) {
  els.apiKeyInput.addEventListener("focus", () => {
    if (els.apiKeyInput.dataset.masked === "1") {
      els.apiKeyInput.value = "";
      els.apiKeyInput.dataset.masked = "0";
    }
  });
}

if (els.apiKeySave) {
  els.apiKeySave.addEventListener("click", () => {
    const raw = (els.apiKeyInput.value || "").trim();
    if (!raw || raw.startsWith("•")) {
      addBubble("agent", "请先粘贴有效的百炼 API Key（sk- 开头），或直接无 Key 体验演示。", "KEY");
      return;
    }
    state.apiKey = raw;
    sessionStorage.setItem(KEY_STORAGE, raw);
    refreshKeyUi();
    addBubble("agent", "已在本机浏览器保存 Key。后续编排将优先走千问 LLM；清除后仍可无 Key 演示。", "KEY");
  });
}

if (els.apiKeyClear) {
  els.apiKeyClear.addEventListener("click", () => {
    state.apiKey = "";
    sessionStorage.removeItem(KEY_STORAGE);
    refreshKeyUi();
    loadHealth();
    addBubble("agent", "已清除浏览器 Key。当前可继续用规则编排完整体验。", "KEY");
  });
}

(async function init() {
  refreshKeyUi();
  addBubble(
    "agent",
    "你好，我是小鹏 AI 出行服务管家。无需 API Key 也可直接点顶部「自动演示 4 场景」。有百炼 Key 时可粘贴以启用千问多轮编排。",
    "BOOT"
  );
  await loadHealth();
  await loadScenarios();
  renderWorld({
    vehicle: { speed_kmh: 0, battery_pct: 72, cabin_temp_c: 26.5, location: "待命" },
    order: null,
  });
})();
