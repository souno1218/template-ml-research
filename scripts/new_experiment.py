"""施策を提案する: 提案書・施策ディレクトリ・ブランチを作る。

uv run scripts/new_experiment.py --title "..." --slug my-slug --kind model --question Q1
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from string import Template

KINDS = ("model", "bench", "infra")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    )
    return Path(out.stdout.strip())


def next_id(root: Path) -> str:
    """既存の提案書と施策ディレクトリから、次の ID (E0000 から連番) を決める。"""
    numbers: list[int] = []
    for path in [*(root / ".okf/proposals").glob("E*.md"), *(root / "experiments").glob("E*")]:
        match = re.match(r"E(\d{4})", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"E{(max(numbers) + 1) if numbers else 0:04d}"


def _add_index_entry(index: Path, title: str, filename: str, heading: str) -> None:
    entry = f"* [{title}]({filename}) - <この施策で何を試すかを1文で。>\n"
    if not index.exists():
        index.write_text(f"# {heading}\n\n{entry}")
        return
    text = index.read_text()
    index.write_text(text.rstrip("\n") + "\n" + entry)


def _add_log_entry(log: Path, today: str, line: str) -> None:
    text = log.read_text()
    heading = f"## {today}"
    if heading in text:
        text = text.replace(heading + "\n", heading + "\n\n" + line + "\n", 1)
        text = text.replace(heading + "\n\n" + line + "\n\n", heading + "\n\n" + line + "\n", 1)
    else:
        head, _, rest = text.partition("\n## ")
        rest = ("## " + rest) if rest else ""
        text = head.rstrip("\n") + f"\n\n{heading}\n\n{line}\n" + ("\n" + rest if rest else "")
    log.write_text(text)


def create(root: Path, title: str, slug: str, kind: str, question: str) -> tuple[str, Path]:
    """提案書と施策ディレクトリを作る。(施策 ID, 提案書のパス) を返す。"""
    if not SLUG_RE.match(slug):
        raise ValueError("slug は小文字の英数字とハイフンだけにする")
    if kind not in KINDS:
        raise ValueError(f"kind は {KINDS} のどれか")
    exp_id = next_id(root)
    name = f"{exp_id}-{slug}"
    version = (root / "docs/rules/VERSION").read_text().strip()
    now = datetime.now(UTC)
    template = Template((root / "tools/okf/templates/proposal.md.tmpl").read_text())
    text = template.safe_substitute(
        id=exp_id,
        slug=slug,
        title=json.dumps(f"{exp_id}: {title}", ensure_ascii=False),
        kind=kind,
        question=question,
        branch=f"exp/{name}",
        rules_version=version,
        now=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    proposal = root / ".okf/proposals" / f"{name}.md"
    proposal.parent.mkdir(parents=True, exist_ok=True)
    proposal.write_text(text)
    for sub in ("configs", "code", "results"):
        directory = root / "experiments" / name / sub
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch()
    _add_index_entry(
        root / ".okf/proposals/index.md", f"{exp_id}: {title}", f"{name}.md", "Proposal"
    )
    log = root / ".okf/log.md"
    if log.exists():
        line = f"* **Creation**: 施策の提案書 [{exp_id}](proposals/{name}.md) を追加した。"
        _add_log_entry(log, now.strftime("%Y-%m-%d"), line)
    return exp_id, proposal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--title", required=True, help="何をする施策か")
    parser.add_argument("--slug", required=True, help="英小文字とハイフン")
    parser.add_argument("--kind", required=True, choices=KINDS)
    parser.add_argument("--question", default="-", help="docs/questions.md の問いの番号")
    parser.add_argument("--no-branch", action="store_true", help="ブランチを作らない")
    args = parser.parse_args(argv)
    root = repo_root()
    exp_id, proposal = create(root, args.title, args.slug, args.kind, args.question)
    print(f"作成: {proposal.relative_to(root)}")
    if not args.no_branch:
        branch = f"exp/{exp_id}-{args.slug}"
        result = subprocess.run(["git", "switch", "-c", branch], cwd=root, check=False)
        if result.returncode != 0:
            print(f"ブランチ {branch} を作れなかった。手で作ること。", file=sys.stderr)
    print("次: 提案書を埋め、commit・push して PR を作る (docs/rules/lifecycle.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
