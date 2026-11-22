"""Proposal の検査と索引が効いていること (わざと壊した施策で誤りが出る)。"""

from __future__ import annotations

from pathlib import Path

from project_name.lab.proposals import read_doc, render_indexes, validate

GOOD_BODY = """
# 問いと仮説

学習率を上げると収束が速くなる。

# 変えること

| 案 | 変えること |
|---|---|
| baseline | なし |

# 予測

test_mse が 0〜10% 下がる。

# 合格の基準

test_mse の 95% 区間が基準線と重ならない。

# 予算

screen、CPU で数分。
"""


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "docs" / "rules").mkdir(parents=True)
    (tmp_path / "docs" / "rules" / "VERSION").write_text("1\n")
    for sub in ("proposals", "experiments", "decisions", "questions"):
        (tmp_path / ".okf" / sub).mkdir(parents=True)
    (tmp_path / ".okf" / "questions" / "Q1-speed.md").write_text(
        "---\ntype: Question\ntitle: 速くなるか\ndescription: d\nid: Q1\nstate: open\n---\n"
        "\n# 問い\n\nx\n"
    )
    (tmp_path / "bench" / "suites" / "v1").mkdir(parents=True)
    (tmp_path / "bench" / "suites" / "v1" / "suite.toml").write_text('version = "v1"\n')
    return tmp_path


def _write(root: Path, stem: str, meta: str, body: str = GOOD_BODY) -> Path:
    path = root / ".okf" / "proposals" / f"{stem}.md"
    path.write_text(f"---\n{meta}\n---\n{body}")
    return path


META = (
    "type: Proposal\ntitle: t\ndescription: d\nstatus: draft\nid: E0001\n"
    "state: proposed\nkind: model\nquestion: Q1\nbranch: exp/E0001-lr\n"
    "rules_version: 1\nsuite: v1\nbaseline: b\nvariants: [baseline]\n"
    "tier: screen"
)


def test_good_proposal_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert validate(read_doc(_write(root, "E0001-lr", META)), root) == []


def test_validate_catches_problems(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    bad = (
        META.replace("question: Q1", "question: Q9")
        .replace("branch: exp/E0001-lr", "branch: exp/wrong")
        .replace("tier: screen", "tier: huge")
        .replace("state: proposed", "state: adopted")
        .replace("rules_version: 1", "rules_version: 3")
    )
    errs = "\n".join(
        validate(read_doc(_write(root, "E0001-lr", bad, "\n# 問いと仮説\n\n<説明>\n")), root)
    )
    for needle in ("branch", "tier", "Q9", "rules_version", "status", "予測", "空", "decisions"):
        assert needle in errs, needle


def test_infra_needs_dash_question(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    meta = META.replace("kind: model", "kind: infra").replace("suite: v1", 'suite: "-"')
    errs = validate(read_doc(_write(root, "E0001-lr", meta)), root)
    assert any("infra" in e for e in errs)


def test_index_lists_rejected_ideas(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    meta = META.replace("state: proposed", "state: rejected").replace(
        "status: draft", "status: stable"
    )
    _write(root, "E0001-lr", meta)
    (root / ".okf" / "decisions" / "E0001-lr.md").write_text(
        "---\ntype: Decision\ntitle: t\ndescription: 差が誤差の範囲だったので不採用\n---\n"
    )
    text = render_indexes(root)[root / ".okf" / "proposals" / "index.md"]
    failed = text.split("## 試して採用しなかったこと")[1]
    assert "E0001" in failed and "誤差の範囲" in failed
    questions = render_indexes(root)[root / ".okf" / "questions" / "index.md"]
    assert "E0001" in questions
