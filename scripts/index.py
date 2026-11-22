""".okf/ の各ディレクトリの index.md (施策・結果・判断・問いなどの一覧) を作り直す。

--check なら、作り直しが要るかだけを調べる (テストと同じ検査)。

  uv run scripts/index.py
"""

from __future__ import annotations

import argparse
import sys

from project_name.lab import gitstate
from project_name.lab.proposals import render_indexes


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = gitstate.repo_root()
    stale = []
    for path, text in render_indexes(root).items():
        if path.exists() and path.read_text() == text:
            continue
        stale.append(path)
        if not args.check:
            path.write_text(text)
            print(f"書いた: {path.relative_to(root)}")
    if args.check and stale:
        for path in stale:
            print(f"古い: {path.relative_to(root)}", file=sys.stderr)
        print("uv run scripts/index.py で作り直す", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
