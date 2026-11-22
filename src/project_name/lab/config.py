"""設定ファイル (TOML) の読み込み。

設定は inherit で別の設定を継承し、違うところだけを書く。

    inherit = "../../../configs/base/standard.toml"   # このファイルからの相対パス
    [model]
    encoder = "tied_gated"

表 (辞書) は再帰的に上書きし、それ以外 (数値、文字列、配列) は丸ごと置き換える。
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w


def load_config(path: str | Path) -> dict[str, Any]:
    """inherit を展開した設定を返す。循環した継承はエラー。"""
    return _load(Path(path).resolve(), ())


def _load(path: Path, seen: tuple[Path, ...]) -> dict[str, Any]:
    if path in seen:
        raise ValueError(f"設定の継承が循環している: {' -> '.join(map(str, (*seen, path)))}")
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    parent = cfg.pop("inherit", None)
    if parent is None:
        return cfg
    base = _load((path.parent / parent).resolve(), (*seen, path))
    return merge(base, cfg)


def merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    """base に over を重ねた新しい辞書。表は再帰的に、それ以外は置き換え。"""
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def dump_config(cfg: dict[str, Any], path: str | Path) -> None:
    with open(path, "wb") as f:
        tomli_w.dump(cfg, f)
