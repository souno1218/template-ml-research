"""施策の Proposal (.okf/proposals/Exxxx-*.md) の読み込みと検査、OKF の索引 (index.md) の作成。

1 つの施策は、同じ名前 (Exxxx-<slug>) の次のファイルとディレクトリを持つ。

    .okf/proposals/Exxxx-<slug>.md     提案 (施策の状態はここの frontmatter に書く)
    .okf/experiments/Exxxx-<slug>.md   結果と考察
    .okf/decisions/Exxxx-<slug>.md     採用・不採用・保留の判定 (判定のときに書く)
    experiments/Exxxx-<slug>/          設定 (configs/)、試作 (code/)、集計 (results/)
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

KINDS = ("model", "bench", "infra")
STATES = ("proposed", "approved", "running", "adopted", "rejected", "parked")
ACTIVE = ("proposed", "approved", "running")  # 進行中。今のルールの版で進める
JUDGED = ("adopted", "rejected", "parked")
TIERS = ("smoke", "screen", "confirm")
REQUIRED_FIELDS = (
    "type",
    "title",
    "description",
    "id",
    "state",
    "kind",
    "question",
    "branch",
    "rules_version",
    "suite",
    "baseline",
    "variants",
    "tier",
)
REQUIRED_SECTIONS = ("問いと仮説", "変えること", "予測", "合格の基準", "予算")
STEM_RE = re.compile(r"^(E\d{4})-[a-z0-9][a-z0-9-]*$")
QUESTION_RE = re.compile(r"^Q\d+$")

# OKF の索引を作るディレクトリと、その見出し
INDEXED_DIRS = {
    "proposals": "Proposal",
    "experiments": "Experiment",
    "decisions": "Decision",
    "questions": "Question",
    "architecture": "Architecture",
    "references": "Reference",
}
GENERATED_NOTE = "`uv run scripts/index.py` が作る (手で編集しない)。"


@dataclass
class Doc:
    """frontmatter つきの Markdown 1 つ。"""

    path: Path
    meta: dict[str, Any]
    body: str
    errors: list[str] = field(default_factory=list)

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def id(self) -> str:
        return str(self.meta.get("id", ""))


def read_doc(path: Path) -> Doc:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return Doc(path, {}, text, ["先頭に --- で囲んだ frontmatter がない"])
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return Doc(path, {}, m.group(2), [f"frontmatter を読めない: {e}"])
    if not isinstance(meta, dict):
        return Doc(path, {}, m.group(2), ["frontmatter が辞書ではない"])
    return Doc(path, meta, m.group(2))


def okf(root: Path) -> Path:
    return root / ".okf"


def rules_version(root: Path) -> int:
    return int((root / "docs" / "rules" / "VERSION").read_text().strip())


def concept_docs(root: Path, sub: str) -> list[Doc]:
    """.okf/<sub>/ の文書 (index.md を除く) を名前順に返す。"""
    d = okf(root) / sub
    if not d.is_dir():
        return []
    return [read_doc(p) for p in sorted(d.glob("*.md")) if p.name != "index.md"]


def list_proposals(root: Path) -> list[Doc]:
    """施策の Proposal (名前が Exxxx-<slug> のもの) を ID 順に返す。"""
    return [d for d in concept_docs(root, "proposals") if STEM_RE.match(d.stem)]


def list_questions(root: Path) -> list[Doc]:
    return concept_docs(root, "questions")


def find(root: Path, exp_id: str) -> Doc:
    hits = [p for p in list_proposals(root) if p.stem.startswith(exp_id + "-")]
    if len(hits) != 1:
        raise FileNotFoundError(f"施策 {exp_id} の Proposal が {len(hits)} 個ある (1 個のはず)")
    return hits[0]


def exp_dir(root: Path, proposal: Doc) -> Path:
    """施策の設定・試作・集計を置くディレクトリ。"""
    return root / "experiments" / proposal.stem


def proposal_for_branch(root: Path, branch: str) -> Doc | None:
    for p in list_proposals(root):
        if p.meta.get("branch") == branch:
            return p
    return None


def branch_ids(root: Path) -> list[int]:
    """手元と origin の exp/Exxxx-* ブランチの番号 (別のブランチにしかない施策の番号も拾うため)。"""
    refs = ["refs/heads/exp/", "refs/remotes/origin/exp/"]
    out = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short)", *refs],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return [
        int(m.group(1)) for line in out.stdout.split() if (m := re.search(r"exp/E(\d{4})-", line))
    ]


def next_id(root: Path) -> str:
    """次の施策の番号。

    このブランチの Proposal と、手元・origin の施策のブランチの番号の最大 + 1。
    """
    ids = [int(p.stem[1:5]) for p in list_proposals(root)] + branch_ids(root)
    return f"E{(max(ids) + 1 if ids else 1):04d}"


def validate(p: Doc, root: Path) -> list[str]:
    """Proposal の誤りの一覧 (空なら問題なし)。"""
    errs = list(p.errors)
    if errs:
        return errs
    meta, stem = p.meta, p.stem
    for k in REQUIRED_FIELDS:
        if k not in meta or meta[k] in (None, ""):
            errs.append(f"frontmatter に {k} がない")
    if errs:
        return errs
    if meta["type"] != "Proposal":
        errs.append(f"type は Proposal ({meta['type']})")
    m = STEM_RE.match(stem)
    if m is None or m.group(1) != meta["id"]:
        errs.append(f"id ({meta['id']}) がファイル名 ({stem}) と合わない")
    if meta["branch"] != f"exp/{stem}":
        errs.append(f"branch は exp/{stem} のはず ({meta['branch']})")
    for key, allowed in (("kind", KINDS), ("state", STATES), ("tier", TIERS)):
        if meta[key] not in allowed:
            errs.append(f"{key} は {allowed} のどれか ({meta[key]})")
    if not isinstance(meta["variants"], list):
        errs.append("variants は案の名前のリスト")
    errs += _check_rules_version(meta, rules_version(root))
    errs += _check_question(meta, root)
    if meta["kind"] != "infra":
        suite = root / "bench" / "suites" / str(meta["suite"]) / "suite.toml"
        if not suite.exists():
            errs.append(f"評価一式 {meta['suite']} が bench/suites/ にない")
    expected_status = "draft" if meta["state"] == "proposed" else "stable"
    if meta.get("status") != expected_status:
        errs.append(f"state が {meta['state']} のとき、OKF の status は {expected_status}")
    for sec in REQUIRED_SECTIONS:
        body = section(p.body, sec)
        if body is None:
            errs.append(f"見出し「# {sec}」がない")
        elif is_placeholder(body):
            errs.append(f"「{sec}」が空 (テンプレートの説明のまま)")
    if meta["state"] != "proposed" and isinstance(meta["variants"], list):
        for v in meta["variants"]:
            if not (exp_dir(root, p) / "configs" / f"{v}.toml").exists():
                errs.append(f"案 {v} の設定 experiments/{stem}/configs/{v}.toml がない")
    if meta["state"] in JUDGED:
        for sub in ("experiments", "decisions"):
            if not (okf(root) / sub / f"{stem}.md").exists():
                errs.append(f"判定した施策には .okf/{sub}/{stem}.md が要る")
    return errs


def _check_rules_version(meta: dict[str, Any], current: int) -> list[str]:
    v = meta["rules_version"]
    if not isinstance(v, int) or v > current:
        return [f"rules_version ({v}) が不正 (今の版は {current})"]
    if meta["state"] in ACTIVE and v != current:
        return [
            f"進行中の施策が古いルール v{v} で書かれている (今は v{current})。"
            "ルールを読み直し、Proposal を見直してから rules_version を上げる"
        ]
    return []


def _check_question(meta: dict[str, Any], root: Path) -> list[str]:
    q = str(meta["question"])
    if meta["kind"] == "infra":
        return [] if q == "-" else ["infra の施策の question は -"]
    if not QUESTION_RE.match(q):
        return [f"question は Q1 のような問いの番号 ({q})"]
    if q not in {d.id for d in list_questions(root)}:
        return [f"問い {q} が .okf/questions/ にない"]
    return []


def is_placeholder(text: str) -> bool:
    """中身がない、またはテンプレートの <説明> (複数行も) と、見出しだけの空の表しかない。"""
    text = re.sub(r"<[^<>]*>", "", text)
    for line in text.strip().splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            empty = all(not c or set(c) <= set("-:") for c in cells)
            if empty or cells[:2] == ["案", "変えること"]:
                continue
        return False
    return True


def section(body: str, title: str) -> str | None:
    m = re.search(rf"^# {re.escape(title)}\s*\n(.*?)(?=^# |\Z)", body, re.S | re.M)
    return None if m is None else m.group(1)


# ---- 索引 ----------------------------------------------------------------


def render_indexes(root: Path) -> dict[Path, str]:
    """.okf/ の各ディレクトリの index.md の中身。{パス: 中身}"""
    out = {}
    for sub, label in INDEXED_DIRS.items():
        if not (okf(root) / sub).is_dir():
            continue
        if sub == "proposals":
            text = _render_proposals(root)
        elif sub == "questions":
            text = _render_questions(root)
        else:
            text = _render_list(root, sub, label)
        out[okf(root) / sub / "index.md"] = text
    return out


def _cell(v: Any) -> str:
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")


def _decision_summary(root: Path, stem: str) -> str:
    path = okf(root) / "decisions" / f"{stem}.md"
    if not path.exists():
        return ""
    return _cell(read_doc(path).meta.get("description", ""))


def _render_proposals(root: Path) -> str:
    props = list_proposals(root)
    head = (
        "| ID | 題 | 種類 | 問い | 状態 | 段階 | 評価一式 | 判定 |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    rows = []
    for p in props:
        m = p.meta
        rows.append(
            f"| [{p.id}]({p.path.name}) | {_cell(m.get('title'))} | {_cell(m.get('kind'))} | "
            f"{_cell(m.get('question'))} | {_cell(m.get('state'))} | {_cell(m.get('tier'))} | "
            f"{_cell(m.get('suite'))} | {_decision_summary(root, p.stem)} |"
        )
    failed = [p for p in props if p.meta.get("state") in ("rejected", "parked")]
    lines = ["# Proposal", "", "施策の一覧。" + GENERATED_NOTE, "", head, *rows, ""]
    lines += [
        "## 試して採用しなかったこと",
        "",
        "新しい施策を提案する前に読む。同じ案を出すときは、ここの判定の理由に答える。",
        "",
        "| ID | 題 | 状態 | 判定 |",
        "|---|---|---|---|",
    ]
    for p in failed:
        lines.append(
            f"| [{p.id}]({p.path.name}) | {_cell(p.meta.get('title'))} | "
            f"{_cell(p.meta.get('state'))} | "
            f"{_decision_summary(root, p.stem)} |"
        )
    return "\n".join(lines) + "\n"


def _render_questions(root: Path) -> str:
    by_q: dict[str, list[str]] = {}
    for p in list_proposals(root):
        by_q.setdefault(str(p.meta.get("question")), []).append(
            f"[{p.id}](../proposals/{p.path.name})"
        )
    lines = [
        "# Question",
        "",
        "研究の問い。施策 (infra を除く) は、どれか 1 つの問いに答えるために立てる。"
        + GENERATED_NOTE,
        "",
        "| 問い | 題 | 状態 | 施策 |",
        "|---|---|---|---|",
    ]
    for q in list_questions(root):
        lines.append(
            f"| [{q.id}]({q.path.name}) | {_cell(q.meta.get('title'))} | "
            f"{_cell(q.meta.get('state'))} | "
            f"{', '.join(by_q.get(q.id, []))} |"
        )
    return "\n".join(lines) + "\n"


def _render_list(root: Path, sub: str, label: str) -> str:
    lines = [f"# {label}", "", GENERATED_NOTE, ""]
    for d in concept_docs(root, sub):
        m = d.meta
        title, desc = _cell(m.get("title", d.stem)), _cell(m.get("description", ""))
        line = f"* [{title}]({d.path.name}) - {desc}"
        if m.get("status") == "deprecated":
            line += " (置き換え済み"
            line += f": {m['superseded_by']})" if m.get("superseded_by") else ")"
        elif m.get("status") == "draft":
            line += " (提案中)"
        lines.append(line)
    return "\n".join(lines) + "\n"
