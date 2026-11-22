"""集計の統計。"""

from __future__ import annotations

import numpy as np


def bootstrap_rate(
    flags: list[bool] | np.ndarray, n_boot: int = 10_000, seed: int = 0
) -> tuple[float, float, float]:
    """成功の割合と、そのブートストラップの 95% 区間 (割合, 下限, 上限)。

    flags: (n_problems,)  問題ごとの成否
    """
    x = np.asarray(flags, dtype=np.float64)
    if x.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, x.size, size=(n_boot, x.size))
    means = x[idx].mean(axis=1)  # (n_boot,)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(x.mean()), float(lo), float(hi)
