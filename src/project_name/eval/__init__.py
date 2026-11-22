"""評価コード。施策のコードから分離して置く。

評価の方法を変えるときは、それ自体を kind: bench の施策にし、評価一式の新しい版を作る
(docs/rules/evaluation.md)。1 つの施策の中で評価を変えない。
"""

from __future__ import annotations

import torch


def squared_errors(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """サンプルごとの二乗誤差。

    pred: (n,)、target: (n,) -> (n,)
    """
    return (pred - target) ** 2
