"""施策の管理ルールの検査: 提案書の frontmatter、ID とファイル名の対応、実行ガード、集計。"""

import json
import shutil
import subprocess
from pathlib import Path

import yaml

import collect
import new_experiment
import run as run_script

ROOT = Path(__file__).resolve().parent.parent
PHASES = {"proposed", "approved", "running", "adopted", "rejected", "parked"}
REQUIRED = [
    "type", "title", "description", "status", "x-id", "x-kind", "x-phase", "x-question",
    "x-branch", "x-rules-version", "x-suite", "x-baseline", "x-variants", "x-tier",
]  # fmt: skip


def frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text()
    assert text.startswith("---\n"), f"{path}: frontmatter がない"
    return yaml.safe_load(text.split("---\n", 2)[1])


def check_proposals(root: Path) -> None:
    for path in sorted((root / ".okf/proposals").glob("E*.md")):
        meta = frontmatter(path)
        for key in REQUIRED:
            assert key in meta, f"{path.name}: {key} がない"
        assert meta["type"] == "Proposal"
        assert meta["x-phase"] in PHASES, f"{path.name}: x-phase が不正"
        assert path.stem == f"{meta['x-id']}-{str(meta['x-branch']).split('-', 1)[1]}"
        assert meta["x-branch"] == f"exp/{path.stem}"
        assert list((root / "experiments").glob(f"{meta['x-id']}-*")), "施策ディレクトリがない"


def test_rules_version_is_integer() -> None:
    assert int((ROOT / "docs/rules/VERSION").read_text().strip()) >= 1


def test_claude_md_points_to_existing_rules() -> None:
    text = (ROOT / "CLAUDE.md").read_text()
    for name in ("ai", "lifecycle", "running", "benchmark", "code", "okf"):
        assert f"docs/rules/{name}.md" in text
        assert (ROOT / f"docs/rules/{name}.md").exists()


def test_existing_proposals_are_valid() -> None:
    check_proposals(ROOT)


def make_skeleton(tmp_path: Path) -> Path:
    for rel in ("docs/rules/VERSION", ".okf/log.md", "tools/okf/templates/proposal.md.tmpl"):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, target)
    (tmp_path / "experiments").mkdir()
    return tmp_path


def test_new_experiment_creates_valid_proposal(tmp_path: Path) -> None:
    root = make_skeleton(tmp_path)
    first, _ = new_experiment.create(root, "最初の施策: ベースライン", "baseline", "infra", "-")
    second, _ = new_experiment.create(root, "二つ目", "second", "model", "Q1")
    assert (first, second) == ("E0000", "E0001")
    check_proposals(root)
    assert (root / "experiments/E0001-second/configs").is_dir()
    assert "E0001" in (root / ".okf/proposals/index.md").read_text()
    assert "E0001" in (root / ".okf/log.md").read_text()


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def make_pushed_repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    git(tmp_path, "init", "--bare", "-b", "main", str(remote))
    git(tmp_path, "clone", str(remote), str(work))
    git(work, "config", "user.email", "t@example.com")
    git(work, "config", "user.name", "t")
    (work / "README.md").write_text("x\n")
    (work / ".gitignore").write_text("runs/\n")
    git(work, "add", "-A")
    git(work, "commit", "-m", "init")
    git(work, "push", "-u", "origin", "HEAD")
    return work


def test_check_pushed_guard(tmp_path: Path) -> None:
    work = make_pushed_repo(tmp_path)
    assert run_script.check_pushed(work) is None
    (work / "new.txt").write_text("dirty\n")
    assert run_script.check_pushed(work) is not None  # 未コミット
    git(work, "add", "-A")
    git(work, "commit", "-m", "local")
    assert run_script.check_pushed(work) is not None  # push していない
    git(work, "push")
    assert run_script.check_pushed(work) is None


def test_run_and_collect_roundtrip(tmp_path: Path) -> None:
    work = make_pushed_repo(tmp_path)
    exp = work / "experiments/E0000-demo/configs"
    exp.mkdir(parents=True)
    (exp / "base.toml").write_text("lr = 0.1\n")
    git(work, "add", "-A")
    git(work, "commit", "-m", "exp")
    git(work, "push")
    code = (
        "import json, os, pathlib;"
        "pathlib.Path(os.environ['RUN_DIR'], 'metrics.json').write_text(json.dumps({'acc': 0.5}))"
    )
    status = run_script.run(work, "E0000", "base", 0, ["python3", "-c", code], dev=False)
    assert status == 0
    summary = collect.collect(work, "E0000")
    assert "acc=0.5" in summary.read_text()
    saved = work / "experiments/E0000-demo/results/base/s0/meta.json"
    meta = json.loads(saved.read_text())
    assert meta["exit_code"] == 0 and meta["dirty"] is False


def test_run_refuses_when_not_pushed(tmp_path: Path) -> None:
    work = make_pushed_repo(tmp_path)
    (work / "experiments/E0000-demo/configs").mkdir(parents=True)
    (work / "experiments/E0000-demo/configs/base.toml").write_text("a = 1\n")
    git(work, "add", "-A")
    git(work, "commit", "-m", "unpushed")
    assert run_script.run(work, "E0000", "base", 0, ["true"], dev=False) == 2
    assert run_script.run(work, "E0000", "base", 0, ["true"], dev=True) == 0
