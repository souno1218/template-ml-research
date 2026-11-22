"""PreToolUse (Bash): 取り返しのつかない git の操作と、main への直接の push を止める。

止めるもの: main / master への push、force push、git reset --hard、git clean -f、git branch -D、
--no-verify (pre-commit の検査を飛ばす)。どうしても要るときは、人間に頼む。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import block, read_input

RULES = (
    (
        r"\bgit\s+push\b[^;&|]*\s(origin\s+)?(HEAD:)?(main|master)\b",
        "main に直接 push しない (PR を作る)",
    ),
    (r"\bgit\s+push\b[^;&|]*\s(-f|--force|--force-with-lease)\b", "force push しない"),
    (r"\bgit\s+reset\b[^;&|]*--hard\b", "git reset --hard しない (変更が消える)"),
    (
        r"\bgit\s+clean\b[^;&|]*\s-[a-zA-Z]*f",
        "git clean -f しない (追跡していないファイルが消える)",
    ),
    (
        r"\bgit\s+branch\b[^;&|]*\s-D\b",
        "git branch -D しない (施策のブランチは archive タグを付けてから消す)",
    ),
    (r"--no-verify\b", "--no-verify で検査を飛ばさない"),
)


def main() -> int:
    data = read_input()
    command = (data.get("tool_input") or {}).get("command") or ""
    for pattern, reason in RULES:
        if re.search(pattern, command):
            block(
                f"止めました: {reason}。必要なら人間に頼む (docs/rules/ai.md)。コマンド: {command}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
