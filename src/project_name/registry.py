"""差し込み口: 部品を名前で登録し、設定ファイルから選ぶ。

    @register("model", "mlp")
    class MLP(nn.Module): ...

    cls = get("model", "mlp")

施策の試作 (experiments/Exxxx-*/code/) も同じ register で登録し、load_plugins で読み込む。
本体 (src/project_name/) には、採用と判定された部品だけを入れる。
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

# 種類を足すときは infra の施策にする (docs/rules/code.md)
KINDS = ("job", "model", "data", "objective", "metric")

# 本体の部品を登録するモジュール。get の前に読み込む。部品のモジュールを足したらここにも書く
BUILTIN_MODULES = ("project_name.jobs",)

_REGISTRY: dict[str, dict[str, Any]] = {k: {} for k in KINDS}
_builtin_loaded = False


def register(kind: str, name: str) -> Callable[[Any], Any]:
    """部品を (種類, 名前) で登録するデコレータ。同じ名前に別の物を登録するとエラー。"""
    if kind not in _REGISTRY:
        raise KeyError(f"未知の種類: {kind!r}。使える種類: {', '.join(KINDS)}")

    def deco(obj: Any) -> Any:
        prev = _REGISTRY[kind].get(name)
        if prev is not None and prev is not obj:
            raise KeyError(f"{kind}/{name} は既に登録されている ({_qualname(prev)})")
        _REGISTRY[kind][name] = obj
        return obj

    return deco


def get(kind: str, name: str) -> Any:
    """登録された部品を取り出す。見つからなければ、登録済みの名前を添えてエラー。"""
    _load_builtin()
    if kind not in _REGISTRY:
        raise KeyError(f"未知の種類: {kind!r}。使える種類: {', '.join(KINDS)}")
    try:
        return _REGISTRY[kind][name]
    except KeyError:
        known = sorted(_REGISTRY[kind])
        raise KeyError(f"{kind}/{name} は登録されていない。登録済み: {known}") from None


def names(kind: str) -> list[str]:
    """その種類で登録済みの名前の一覧。"""
    _load_builtin()
    return sorted(_REGISTRY[kind])


def load_plugins(dirs: Iterable[str | Path]) -> list[str]:
    """ディレクトリ内の *.py を読み込み、中の register を実行させる。読み込んだモジュール名を返す。

    モジュール名はパスから一意に作るので、別の施策に同じファイル名があっても衝突しない。
    """
    loaded = []
    for d in dirs:
        d = Path(d).resolve()
        if not d.is_dir():
            raise FileNotFoundError(f"プラグインのディレクトリがない: {d}")
        # テスト (test_*.py) は読み込まない
        for path in sorted(p for p in d.glob("*.py") if not p.name.startswith("test_")):
            parts = path.with_suffix("").parts[-3:]
            mod_name = "project_plugin_" + "_".join(parts).replace("-", "_")
            if mod_name not in sys.modules:
                spec = importlib.util.spec_from_file_location(mod_name, path)
                assert spec is not None and spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
            loaded.append(mod_name)
    return loaded


def _load_builtin() -> None:
    global _builtin_loaded
    if not _builtin_loaded:
        _builtin_loaded = True
        for m in BUILTIN_MODULES:
            importlib.import_module(m)


def _qualname(obj: Any) -> str:
    return f"{getattr(obj, '__module__', '?')}.{getattr(obj, '__qualname__', repr(obj))}"
