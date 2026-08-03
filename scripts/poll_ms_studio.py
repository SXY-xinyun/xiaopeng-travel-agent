import json, time, urllib.request, os

TOKEN = os.environ.get("MODELSCOPE_API_KEY") or os.environ.get("MS_TOKEN") or ""
OWNER = os.environ.get("MS_OWNER", "xxkingxxking")
REPO = os.environ.get("MS_REPO", "xiaopeng-travel-agent")
BASE = f"https://modelscope.cn/openapi/v1/studios/{OWNER}/{REPO}"

if not TOKEN:
    raise SystemExit("Set MS_TOKEN or MODELSCOPE_API_KEY")


def get(path=""):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


for i in range(30):
    data = get().get("data") or {}
    runtime = data.get("runtime") or {}
    status = runtime.get("status") or data.get("status")
    print(f"[{i+1}] {status}")
    if status in {"Running", "DeployFailed", "Failed", "Error", "stopped", "Stopped"}:
        print("HOST", data.get("host"))
        print("PAGE", f"https://modelscope.cn/studios/{OWNER}/{REPO}")
        break
    time.sleep(20)
else:
    print("timeout still deploying")
