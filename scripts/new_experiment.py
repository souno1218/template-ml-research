"""新しい施策をテンプレート (experiments/_template/) から作り、そのブランチに切り替える。

  uv run scripts/new_experiment.py --title "学習率を上げる" --slug larger-lr \
      --kind model --question Q1 --by claude/<model>

作るもの:
  .okf/proposals/Exxxx-<slug>.md     提案 (承認を受けるもの)
  .okf/experiments/Exxxx-<slug>.md   結果と考察 (計算の後に埋める)
  experiments/Exxxx-<slug>/          configs/baseline.toml、code/、sweep.toml
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys

from project_name.lab import gitstate
from project_name.lab.proposals import KINDS, next_id, okf, render_indexes, rules_version
from project_name.lab.suite import list_suites


def fill(text: str, values: dict[str, str]) -> str:
    """テンプレートの {{name}} を置き換える。

    OKF の frontmatter の { } とぶつからないように二重括弧にしている。
    """
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--title", required=True)
    ap.add_argument("--slug", required=True, help="名前の後半 (英小文字・数字・ハイフン)")
    ap.add_argument("--kind", required=True, choices=KINDS)
    ap.add_argument("--question", default="-", help="Q1 など。infra は -")
    ap.add_argument("--suite", help="評価一式の版。省略すると最新の版 (infra は -)")
    ap.add_argument(
        "--by", required=True, help="書き手 (claude/<model> か human:<id>)。OKF の generated.by"
    )
    ap.add_argument("--no-branch", action="store_true", help="ブランチを作らない")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.slug):
        print("slug は英小文字・数字・ハイフンだけ", file=sys.stderr)
        return 2
    root = gitstate.repo_root()
    exp_id = next_id(root)
    stem = f"{exp_id}-{args.slug}"
    suites = list_suites(root)
    if args.kind == "infra":
        suite = "-"
    elif args.suite:
        suite = args.suite
    elif suites:
        suite = suites[-1]
    else:
        print(
            "bench/suites/ に評価一式がない。先に kind: bench の施策で評価一式を作る",
            file=sys.stderr,
        )
        return 2
    question = "-" if args.kind == "infra" else args.question

    if not args.no_branch:
        r = subprocess.run(["git", "switch", "-c", f"exp/{stem}"], cwd=root, check=False)
        if r.returncode != 0:
            return r.returncode

    tpl = root / "experiments" / "_template"
    # YAML では裸の "-" が並びの始まりと読まれるので、引用符で囲む
    values = {
        "id": exp_id,
        "stem": stem,
        "title": args.title,
        "kind": args.kind,
        "question": f'"{question}"' if question == "-" else question,
        "suite": f'"{suite}"' if suite == "-" else suite,
        "rules_version": str(rules_version(root)),
        "by": args.by,
        "at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    targets = {
        tpl / "proposal.md": okf(root) / "proposals" / f"{stem}.md",
        tpl / "experiment.md": okf(root) / "experiments" / f"{stem}.md",
    }
    for src, dst in targets.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(fill(src.read_text(), values))
    dest = root / "experiments" / stem
    shutil.copytree(tpl / "configs", dest / "configs")
    (dest / "code").mkdir(parents=True)
    (dest / "code" / ".gitkeep").touch()
    (dest / "sweep.toml").write_text(fill((tpl / "sweep.toml").read_text(), values))
    for path, text in render_indexes(root).items():
        path.write_text(text)
    print(f"作った: .okf/proposals/{stem}.md と experiments/{stem}/ (ブランチ exp/{stem})")
    print("次は Proposal の本文と frontmatter (baseline、variants、tier) を埋め、")
    print(".okf/log.md に 1 行足して、commit・push し、PR を作る (docs/rules/lifecycle.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
