"""機械学習の共通部品: デバイス選択と seed 固定。"""

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


def set_seed(seed: int) -> None:
    """random / numpy / torch の seed を固定する。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
