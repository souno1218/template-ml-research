"""評価一式 (bench/suites/<版>/) の読み込みと照合。

suite.toml に評価データのファイルと sha256 を書き、読み込むたびに照合する。
一度使い始めた版 (suite.toml を commit した版) は変更しない。変えるときは次の版を作る。

    version = "v1"
    description = "..."

    [sets.test]
    file = "test.npz"
    sha256 = "..."
    n = 1000            # サンプル数 (任意。データの読み方はプロジェクトごとに書く)

データの中身の読み方はプロジェクトによって違うので、ここでは場所と照合だけを扱う。
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project_name.lab.gitstate import repo_root


@dataclass
class Suite:
    version: str
    root: Path
    spec: dict[str, Any]

    def set_names(self) -> list[str]:
        return list(self.spec.get("sets", {}))

    def path(self, name: str) -> Path:
        """評価データのファイルの場所。照合してから返す。"""
        self.verify(name)
        return self.root / self.spec["sets"][name]["file"]

    def verify(self, name: str | None = None) -> None:
        """評価データのハッシュを suite.toml と照合する。合わなければエラー。"""
        for set_name in [name] if name is not None else self.set_names():
            s = self.spec["sets"][set_name]
            digest = sha256(self.root / s["file"])
            if digest != s["sha256"]:
                raise ValueError(
                    f"評価一式 {self.version} の {set_name} が変更されている "
                    f"(sha256 {digest[:12]}…、記録は {s['sha256'][:12]}…)。"
                    "版は変更せず、次の版を作る"
                )

    def fingerprint(self) -> str:
        """この版を表すハッシュ (suite.toml の sha256)。suite.toml は各ファイルのハッシュを含む。"""
        return sha256(self.root / "suite.toml")


def load_suite(version: str, root: str | Path | None = None) -> Suite:
    """bench/suites/<version>/suite.toml を読む。

    root はリポジトリの根 (省略すると今いる場所から探す)。
    """
    base = Path(root) if root is not None else repo_root()
    d = base / "bench" / "suites" / version
    with open(d / "suite.toml", "rb") as f:
        spec = tomllib.load(f)
    if spec.get("version") != version:
        raise ValueError(
            f"{d}/suite.toml の version が {spec.get('version')!r} (ディレクトリは {version})"
        )
    return Suite(version, d, spec)


def list_suites(root: Path) -> list[str]:
    d = root / "bench" / "suites"
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if (p / "suite.toml").exists())


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
