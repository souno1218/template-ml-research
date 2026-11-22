import torch

from project_name.utils import get_device, set_seed


def test_get_device_returns_device() -> None:
    assert isinstance(get_device(), torch.device)


def test_set_seed_is_reproducible() -> None:
    set_seed(0)
    a = torch.rand(3)
    set_seed(0)
    b = torch.rand(3)
    assert torch.equal(a, b)
