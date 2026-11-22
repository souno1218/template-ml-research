"""実行中・最近の run の進み具合を表示する。更新が止まった run には印を付ける。

uv run scripts/progress.py            # 全部の施策
uv run scripts/progress.py E0001      # その施策だけ
uv run scripts/progress.py --watch 60 # 60 秒ごとに表示し直す
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from project_name.lab import gitstate
from project_name.lab.progress import STALE_SEC, read_progress


def show_launches(runs_dir, experiment: str | None) -> None:
    """scripts/launch.py で裏に回した処理の段階 (最新 5 件)。"""
    d = runs_dir / "_launch"
    if not d.is_dir():
        return
    items = [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))]
    items = [i for i in items if not experiment or i.get("experiment") == experiment][-5:]
    for i in items:
        print(
            f"[launch] {i.get('experiment')}  {i.get('phase')}  {i.get('state')}  "
            f"更新 {i.get('updated', '')}  ログ {i.get('log', '')}"
        )


def show(runs_dir, experiment: str | None, limit: int) -> None:
    show_launches(runs_dir, experiment)
    rows = []
    for d in (
        sorted(p for p in runs_dir.iterdir() if (p / "meta.json").exists() and p.name != "dev")
        if runs_dir.is_dir()
        else []
    ):
        meta = json.loads((d / "meta.json").read_text())
        if experiment and meta.get("experiment") != experiment:
            continue
        rows.append((d, meta, read_progress(d)))
    now = time.time()
    for d, meta, prog in rows[-limit:]:
        status = meta.get("status", "?")
        line = f"{d.name}  {status}"
        if prog:
            if "step" in prog and "total" in prog:
                line += (
                    f"  {prog['step']}/{prog['total']} ({prog['step'] / max(prog['total'], 1):.0%})"
                )
            line += f"  {prog.get('phase', '')}  更新 {prog.get('updated', '')}"
            if status == "running" and now - float(prog.get("updated_unix", now)) > STALE_SEC:
                line += "  ← 止まっている? (固まった・落ちた疑い)"
        print(line)
    if not rows:
        print("run がない")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("experiment", nargs="?")
    ap.add_argument("--watch", type=int, help="この秒数ごとに表示し直す")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()
    runs_dir = gitstate.repo_root() / args.runs_dir
    while True:
        show(runs_dir, args.experiment, args.limit)
        if not args.watch:
            return 0
        time.sleep(args.watch)
        print("-" * 40)


if __name__ == "__main__":
    sys.exit(main())
