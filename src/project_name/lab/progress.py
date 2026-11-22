"""進み具合のファイル runs/<run_id>/progress.json。

学習と評価が一定の間隔で書き、scripts/progress.py が読む。書くたびに時刻を入れるので、
更新が止まっていれば (= プロセスが固まった・落ちた) 読む側で分かる。
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

INTERVAL_SEC = 30.0  # 書く間隔
STALE_SEC = 300.0  # これより長く更新がなければ、止まっている疑い (書く間隔の 10 倍)


class ProgressWriter:
    def __init__(self, run_dir: Path | None, interval: float = INTERVAL_SEC):
        self.path = None if run_dir is None else Path(run_dir) / "progress.json"
        self.interval = interval
        self.last = 0.0

    def update(self, force: bool = False, **fields) -> None:
        """前回から interval 秒たっていれば (または force)、fields に時刻を足して書く。"""
        now = time.time()
        if self.path is None or (not force and now - self.last < self.interval):
            return
        self.last = now
        data = {**fields, "updated_unix": now, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False))
        os.replace(tmp, self.path)  # 書きかけを読まれないように、置き換えで書く


def read_progress(run_dir: Path) -> dict | None:
    p = Path(run_dir) / "progress.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None
