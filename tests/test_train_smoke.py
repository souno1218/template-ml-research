import torch
from torch import nn

from project_name.runinfo import collect_run_info
from project_name.utils import set_seed


def test_one_train_step_on_tiny_data() -> None:
    """tiny データで学習1ステップが動き、loss が有限であることを確かめる（CPU、数秒以内）。"""
    set_seed(0)
    model = nn.Linear(4, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    x = torch.randn(8, 4)  # (batch, d_in)
    y = torch.randn(8, 2)  # (batch, d_out)
    loss = nn.functional.mse_loss(model(x), y)
    loss.backward()
    optimizer.step()
    assert torch.isfinite(loss)


def test_collect_run_info_has_keys() -> None:
    info = collect_run_info(seed=0)
    assert {"commit", "seed", "device", "torch", "at"} <= info.keys()
