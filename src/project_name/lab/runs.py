"""実行 (runs/<run_id>/) の記録と検索。"""

from __future__ import annotations

import contextlib
import datetime as dt
import importlib.metadata
import json
import platform
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# meta.json に版を記録するライブラリ (入っていなければ飛ばす)。プロジェクト名を変えたら先頭も直す
TRACKED_PACKAGES = ("project-name", "numpy", "torch")


def make_run_id(experiment: str, variant: str, seed: int, now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now()
    return f"{now:%Y%m%d-%H%M%S}-{experiment}-{variant}-s{seed}"


def environment() -> dict[str, Any]:
    """マシン名、OS、Python とライブラリの版、計算デバイス。"""
    pkgs = {}
    for name in TRACKED_PACKAGES:
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            pkgs[name] = importlib.metadata.version(name)
    env: dict[str, Any] = {
        "machine": socket.gethostname(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "packages": pkgs,
    }
    try:
        import torch

        if torch.cuda.is_available():
            env["device"] = torch.cuda.get_device_name(0)
        else:
            env["device"] = "mps" if torch.backends.mps.is_available() else "cpu"
    except ImportError:
        pass
    return env


@dataclass
class RunInfo:
    dir: Path
    meta: dict[str, Any]

    @property
    def run_id(self) -> str:
        return self.meta["run_id"]


def find_runs(runs_dir: Path, experiment: str, finished_only: bool = True) -> list[RunInfo]:
    """その施策の run を古い順に返す。dev の run (runs/dev/) は含めない。"""
    out: list[RunInfo] = []
    if not runs_dir.is_dir():
        return out
    for d in sorted(runs_dir.iterdir()):
        mf = d / "meta.json"
        if d.name == "dev" or not mf.exists():
            continue
        meta = json.loads(mf.read_text())
        if meta.get("experiment") != experiment:
            continue
        if finished_only and meta.get("status") != "ok":
            continue
        out.append(RunInfo(d, meta))
    return out


def latest_by_variant_seed(runs: list[RunInfo]) -> dict[tuple[str, int], RunInfo]:
    """(案, seed) ごとに最も新しい run。"""
    out: dict[tuple[str, int], RunInfo] = {}
    for r in runs:  # 古い順なので、後のもので上書きされる
        out[(r.meta["variant"], int(r.meta["seed"]))] = r
    return out
