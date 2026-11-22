"""PreToolUse (Edit / Write / MultiEdit / NotebookEdit)。

施策の中で変えてはいけないファイルの編集を止める。

- 使い始めた評価一式 (bench/suites/<版>/ で suite.toml が commit 済み) は、どの施策でも変えない。
- 新しい評価一式 (bench/suites/ の新しい版) は、kind: bench の施策でだけ作る。
- ルール (docs/rules/、CLAUDE.md、AGENTS.md) と hooks (.claude/、scripts/hooks/) は、
  kind: infra の施策でだけ変える。

施策のブランチ (exp/...) でないときは、評価一式の凍結だけを守らせる。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import block, current_proposal, frontmatter_value, git, read_input, repo_root

RULE_PATHS = ("docs/rules/", "CLAUDE.md", "AGENTS.md", ".claude/", "scripts/hooks/")


def main() -> int:
    data = read_input()
    tool_input = data.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    root = repo_root(data.get("cwd"))
    if not target or root is None:
        return 0
    path = Path(target)
    if not path.is_absolute():
        path = Path(data.get("cwd") or ".") / path
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return 0

    parts = rel.split("/")
    if rel.startswith("bench/suites/") and len(parts) >= 4:
        suite_toml = f"bench/suites/{parts[2]}/suite.toml"
        if git(root, "ls-files", suite_toml):
            block(
                f"{rel} は使い始めた評価一式 {parts[2]} のファイル。版は変更しない。"
                "評価を変えるときは kind: bench の施策で次の版を作る (docs/rules/evaluation.md)"
            )

    found = current_proposal(root)
    if found is None:
        return 0  # 施策のブランチでない
    kind = frontmatter_value(found[1], "kind")
    if rel.startswith("bench/") and kind != "bench":
        block(
            f"{rel}: 評価は kind: bench の施策でだけ変える (今の施策は kind: {kind})。"
            "1 つの施策の中で評価を変えない。"
            "必要なら別の施策として提案する (docs/rules/evaluation.md)"
        )
    if rel.startswith(RULE_PATHS) and kind != "infra":
        block(
            f"{rel}: ルールと hooks は kind: infra の施策でだけ変える (今の施策は kind: {kind})。"
            "必要なら別の施策として提案する (docs/rules/ai.md)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
