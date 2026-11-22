"""差し込み口: 種類と名前で部品を登録し、設定ファイルから選べるようにする。"""

import importlib.util
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

_REGISTRY: dict[str, dict[str, Any]] = {}


def register(kind: str, name: str) -> Callable[[Any], Any]:
    """クラスや関数を (kind, name) で登録するデコレータ。同じ名前の二重登録は拒否する。"""

    def decorator(obj: Any) -> Any:
        entries = _REGISTRY.setdefault(kind, {})
        if name in entries:
            raise ValueError(f"already registered: {kind}/{name}")
        entries[name] = obj
        return obj

    return decorator


def get(kind: str, name: str) -> Any:
    """登録済みの部品を返す。なければ、登録済みの名前の一覧つきでエラーにする。"""
    entries = _REGISTRY.get(kind, {})
    if name not in entries:
        raise KeyError(f"unknown {kind}: {name} (registered: {sorted(entries)})")
    return entries[name]


def names(kind: str) -> list[str]:
    """登録済みの名前の一覧。"""
    return sorted(_REGISTRY.get(kind, {}))


def load_plugins(directories: Iterable[Path]) -> None:
    """施策の試作 (experiments/Exxxx-*/code/*.py) を読み込み、登録させる。"""
    for directory in directories:
        for path in sorted(Path(directory).glob("*.py")):
            spec = importlib.util.spec_from_file_location(f"plugin_{path.stem}", path)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load plugin: {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
