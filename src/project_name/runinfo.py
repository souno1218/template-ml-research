"""実験の再現に必要な実行情報を集める。結果は .okf/experiments/ の Experiment に貼る。"""

import platform
import subprocess
from datetime import UTC, datetime

import torch

from project_name.utils import get_device


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def collect_run_info(seed: int) -> dict[str, str | int | bool]:
    """コミット・未コミット変更の有無・seed・デバイス・環境を辞書で返す。"""
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": _git("status", "--porcelain") != "",
        "seed": seed,
        "device": str(get_device()),
        "host": platform.node(),
        "torch": torch.__version__,
        "python": platform.python_version(),
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
