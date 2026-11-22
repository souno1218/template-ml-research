"""SessionStart: 今どこにいるかを Claude に読ませる。

ブランチ、未コミットの変更、今の施策、.okf/status.md を表示する。

標準出力に書いたものが、セッションの最初の文脈に入る。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import current_proposal, frontmatter_value, git, read_input, repo_root

MAX_STATUS_LINES = 120


def main() -> int:
    data = read_input()
    root = repo_root(data.get("cwd"))
    if root is None:
        return 0
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = git(root, "rev-parse", "--short", "HEAD")
    dirty = git(root, "status", "--porcelain")
    version_file = root / "docs" / "rules" / "VERSION"
    version = version_file.read_text().strip() if version_file.exists() else "?"

    print("# 今どこにいるか (SessionStart hook が自動で表示)")
    print()
    print(f"- ルール v{version}。作業の前に CLAUDE.md に書かれた順に読む")
    print(
        f"- ブランチ {branch} / commit {commit} / 未コミットの変更: {'あり' if dirty else 'なし'}"
    )
    found = current_proposal(root)
    if found is not None:
        path, text = found
        fields = ("id", "title", "state", "kind", "tier")
        info = ", ".join(f"{k}: {frontmatter_value(text, k)}" for k in fields)
        print(f"- 今の施策: {info} ({path.relative_to(root)})")
    else:
        print("- 施策のブランチではない")
    status = root / ".okf" / "status.md"
    if status.exists():
        body = re.sub(r"^---\n.*?\n---\n?", "", status.read_text(), count=1, flags=re.S)
        lines = body.strip().splitlines()
        print()
        print(".okf/status.md:")
        print()
        print("\n".join(lines[:MAX_STATUS_LINES]))
        if len(lines) > MAX_STATUS_LINES:
            print(f"(以下 {len(lines) - MAX_STATUS_LINES} 行は省略。ファイルを読む)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
