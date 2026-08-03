"""Create/update a public Hugging Face Space (Docker) for this demo.

Usage:
  set HF_TOKEN=hf_xxx
  .\\.venv\\Scripts\\python scripts\\deploy_hf_space.py --username YOUR_HF_USERNAME

Or:
  .\\.venv\\Scripts\\python scripts\\deploy_hf_space.py --username YOUR_HF_USERNAME --token hf_xxx
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, create_repo, upload_folder

ROOT = Path(__file__).resolve().parents[1]
SPACE_NAME = "xiaopeng-travel-agent"

INCLUDE = [
    "Dockerfile",
    "requirements.txt",
    ".env.example",
    ".dockerignore",
    "backend",
    "frontend",
]


def build_staging(staging: Path) -> None:
    staging.mkdir(parents=True, exist_ok=True)
    # Space README must carry YAML frontmatter
    shutil.copy2(ROOT / "README.hf.md", staging / "README.md")
    for name in INCLUDE:
        src = ROOT / name
        dst = staging / name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            shutil.copy2(src, dst)
        else:
            raise FileNotFoundError(src)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, help="Hugging Face username")
    parser.add_argument("--token", default=None, help="HF write token (or set HF_TOKEN)")
    parser.add_argument("--space", default=SPACE_NAME)
    args = parser.parse_args()

    import os

    token = args.token or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token:
        raise SystemExit("Missing token. Pass --token or set HF_TOKEN.")

    api = HfApi(token=token)
    who = api.whoami()
    print("logged in as:", who.get("name") or who.get("fullname"))

    repo_id = f"{args.username}/{args.space}"
    create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        private=False,
        exist_ok=True,
        token=token,
    )
    print("space ready:", f"https://huggingface.co/spaces/{repo_id}")

    with tempfile.TemporaryDirectory(prefix="xp-hf-") as tmp:
        staging = Path(tmp) / "space"
        build_staging(staging)
        upload_folder(
            repo_id=repo_id,
            repo_type="space",
            folder_path=str(staging),
            token=token,
            commit_message="Deploy XPENG travel agent demo (Docker Space)",
        )

    direct = f"https://{args.username.lower().replace('_', '-')}-{args.space}.hf.space"
    print("\nDONE")
    print("Space page :", f"https://huggingface.co/spaces/{repo_id}")
    print("Direct app :", direct)
    print("Wait 2–5 min for Building → Running, then open the link.")


if __name__ == "__main__":
    main()
