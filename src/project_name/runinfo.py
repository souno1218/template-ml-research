"""実験の再現に必要な実行情報を集める。結果は .okf/experiments/ の Experiment に貼る。"""

import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import torch

from project_name.utils import get_device


def _git(cwd: Path | None, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def collect_run_info(seed: int, cwd: Path | None = None) -> dict[str, str | int | bool]:
    """コミット・dirty の有無・seed・デバイス・環境を辞書で返す。cwd は git のリポジトリ。"""
    return {
        "commit": _git(cwd, "rev-parse", "HEAD"),
        "branch": _git(cwd, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": _git(cwd, "status", "--porcelain") != "",
        "seed": seed,
        "device": str(get_device()),
        "host": platform.node(),
        "torch": torch.__version__,
        "python": platform.python_version(),
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
