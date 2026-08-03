"""Upload project files to GitHub via Contents API (when git push is blocked)."""
from __future__ import annotations

import base64
import json
import pathlib
import subprocess
import time

REPO = "SXY-xinyun/xiaopeng-travel-agent"
ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", ".cursor", "__pycache__", "submission"}
SKIP_NAMES = {".env", ".env.local"}
SKIP_PATHS = {"README.md"}  # already seeded


def gh_api(method: str, path: str, payload: dict | None = None, retries: int = 6) -> dict:
    for attempt in range(retries):
        cmd = ["gh", "api", "--method", method, path]
        if payload is not None:
            cmd += ["--input", "-"]
        proc = subprocess.run(
            cmd,
            input=None if payload is None else json.dumps(payload).encode(),
            capture_output=True,
        )
        if proc.returncode == 0:
            out = proc.stdout.decode("utf-8")
            return json.loads(out) if out.strip() else {}
        err = (proc.stderr or proc.stdout).decode("utf-8", errors="replace")
        print(f"  retry {attempt + 1}: {err[:200].strip()}")
        time.sleep(1.2 * (attempt + 1))
    raise SystemExit(f"failed {method} {path}")


def collect_files() -> list[tuple[str, bytes]]:
    files: list[tuple[str, bytes]] = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        if p.name in SKIP_NAMES or rel in SKIP_PATHS:
            continue
        if p.suffix == ".pyc":
            continue
        data = p.read_bytes()
        if len(data) > 900_000:
            print("skip large", rel)
            continue
        files.append((rel, data))
    return files


def main() -> None:
    files = collect_files()
    print("to upload", len(files))
    for i, (rel, data) in enumerate(files, 1):
        b64 = base64.b64encode(data).decode("ascii")
        sha = None
        check = subprocess.run(
            ["gh", "api", f"/repos/{REPO}/contents/{rel}?ref=main"],
            capture_output=True,
        )
        if check.returncode == 0:
            try:
                sha = json.loads(check.stdout.decode())["sha"]
            except Exception:
                sha = None
        payload: dict = {"message": f"chore: add {rel}", "content": b64, "branch": "main"}
        if sha:
            payload["sha"] = sha
        gh_api("PUT", f"/repos/{REPO}/contents/{rel}", payload)
        print(f"[{i}/{len(files)}] {rel}")
    print("DONE")


if __name__ == "__main__":
    main()
