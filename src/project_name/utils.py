"""機械学習の共通部品: デバイス選択と seed 固定。"""

import os
import random

import numpy as np
import torch


def get_device() -> torch.device:
    """cuda -> mps -> cpu の順で使えるデバイスを返す。"""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_seed(seed: int, deterministic: bool = False) -> None:
    """random / numpy / torch の seed を固定する。

    deterministic=True なら、決定的な実装だけを使うよう torch に頼む。決定的な実装のない演算は
    警告を出す (warn_only)。警告が出た演算は、同じ seed でも結果が揺れうる。
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.benchmark = False
