"""本体のジョブ。scripts/run.py は設定の [run] job の名前でここ (またはプラグイン) から選ぶ。

ジョブの形: job(cfg: dict, run_dir: Path, seed: int) -> None
    metrics.json (集計) を run_dir に必ず書く。評価をするジョブは per_sample.jsonl も書く。
    per_sample.jsonl の各行に真偽値の "ok" があれば、
    collect.py が成功率のブートストラップ区間を出す。

example は、仕組みが端から端まで動くことを確かめるための小さな例。実際の研究のジョブに置き換える。
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
from torch import nn

from project_name.eval import squared_errors
from project_name.lab.progress import ProgressWriter
from project_name.registry import register
from project_name.utils import get_device, set_seed


def _synthetic(
    n: int, d_in: int, noise: float, gen: torch.Generator
) -> tuple[torch.Tensor, torch.Tensor]:
    """y = x w + noise の合成データ。

    x: (n, d_in)、y: (n,)
    """
    w = torch.arange(1, d_in + 1, dtype=torch.float32) / d_in  # (d_in,)
    x = torch.randn(n, d_in, generator=gen)  # (n, d_in)
    y = x @ w + noise * torch.randn(n, generator=gen)  # (n,)
    return x, y


@register("job", "example")
def example(cfg: dict, run_dir: Path, seed: int) -> None:
    """合成データで線形回帰を学習し、テストデータで評価する。"""
    data, train = cfg["data"], cfg["train"]
    # データは data_seed で固定し、学習の乱数だけを seed で変える (案の比較で同じデータを使うため)
    gen = torch.Generator().manual_seed(int(data.get("data_seed", 0)))
    x, y = _synthetic(int(data["n_train"]), int(data["d_in"]), float(data["noise"]), gen)
    xt, yt = _synthetic(int(data["n_test"]), int(data["d_in"]), float(data["noise"]), gen)

    set_seed(seed, deterministic=bool(cfg.get("run", {}).get("deterministic", True)))
    device = (
        get_device() if cfg.get("run", {}).get("device", "cpu") == "auto" else torch.device("cpu")
    )
    model = nn.Linear(int(data["d_in"]), 1).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=float(train["lr"]))
    progress = ProgressWriter(run_dir)
    steps = int(train["steps"])
    for step in range(steps):
        loss = nn.functional.mse_loss(model(x.to(device)).squeeze(-1), y.to(device))
        opt.zero_grad()
        loss.backward()
        opt.step()
        progress.update(step=step + 1, total=steps, phase="train")

    with torch.no_grad():
        err = squared_errors(model(xt.to(device)).squeeze(-1).cpu(), yt)  # (n_test,)
    threshold = float(cfg.get("eval", {}).get("ok_threshold", 0.05))
    with open(run_dir / "per_sample.jsonl", "w") as f:
        for i, e in enumerate(err.tolist()):
            f.write(json.dumps({"i": i, "sq_err": e, "ok": e < threshold}) + "\n")
    metrics = {"test_mse": float(err.mean()), "train_loss": float(loss.item()), "steps": steps}
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=1))
    progress.update(force=True, step=steps, total=steps, phase="done")
    print(f"test_mse {metrics['test_mse']:.4f}")
