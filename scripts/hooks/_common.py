"""Claude Code の hooks が共通で使う小道具。

標準ライブラリだけで書く (uv を通さず速く動かすため)。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return out.stdout.strip() if out.returncode == 0 else ""


def repo_root(cwd: str | None) -> Path | None:
    top = git(Path(cwd or "."), "rev-parse", "--show-toplevel")
    return Path(top) if top else None


def frontmatter_value(text: str, key: str) -> str | None:
    """frontmatter の 1 行の値 (key: value) を素朴に読む。引用符は外す。"""
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def current_proposal(root: Path) -> tuple[Path, str] | None:
    """今のブランチの施策の Proposal (パス, 本文)。なければ None。"""
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    d = root / ".okf" / "proposals"
    if not branch or not d.is_dir():
        return None
    for p in sorted(d.glob("E*.md")):
        text = p.read_text()
        if frontmatter_value(text, "branch") == branch:
            return p, text
    return None


def block(message: str) -> None:
    """操作を止める。stderr の内容は Claude に返される。"""
    print(message, file=sys.stderr)
    sys.exit(2)
