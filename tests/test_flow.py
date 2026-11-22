"""実行の入口から集計までが通ること: run.py の push 済みの検査、--dev の実行、collect.py の集計。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return out.stdout.strip()


def script(root: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name), *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def make_repo(tmp_path: Path) -> Path:
    """設定と施策のディレクトリだけを持つ小さなリポジトリ。"""
    root = tmp_path / "repo"
    (root / "configs" / "base").mkdir(parents=True)
    shutil.copy(
        ROOT / "configs" / "base" / "example.toml", root / "configs" / "base" / "example.toml"
    )
    cfg = root / "experiments" / "E0001-lr" / "configs"
    cfg.mkdir(parents=True)
    shutil.copy(
        ROOT / "experiments" / "_template" / "configs" / "baseline.toml", cfg / "baseline.toml"
    )
    (root / "docs" / "rules").mkdir(parents=True)
    (root / "docs" / "rules" / "VERSION").write_text("1\n")
    (root / ".okf" / "proposals").mkdir(parents=True)
    (root / ".okf" / "proposals" / "E0001-lr.md").write_text(
        "---\ntype: Proposal\nid: E0001\n---\n"
    )
    (root / ".gitignore").write_text("runs/\n")
    git(root.parent, "init", "-q", "-b", "main", str(root))
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "init")
    return root


def test_run_refuses_unpushed_commit(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    r = script(
        root,
        "run.py",
        "--config",
        "experiments/E0001-lr/configs/baseline.toml",
        "--experiment",
        "E0001",
        "--variant",
        "baseline",
    )
    assert r.returncode == 2
    assert "origin" in r.stderr


def test_run_and_collect(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-q", "-u", "origin", "main")

    args = [
        "--config",
        "experiments/E0001-lr/configs/baseline.toml",
        "--experiment",
        "E0001",
        "--variant",
        "baseline",
    ]
    r = script(root, "run.py", *args, "--seed", "0")
    assert r.returncode == 0, r.stderr
    (run_dir,) = [p for p in (root / "runs").iterdir() if p.name != "dev"]
    meta = json.loads((run_dir / "meta.json").read_text())
    assert meta["status"] == "ok" and meta["commit"] == git(root, "rev-parse", "HEAD")
    assert meta["dirty"] is False and meta["rules_version"] == 1
    assert (run_dir / "per_sample.jsonl").exists()

    r = script(root, "collect.py", "E0001")
    assert r.returncode == 0, r.stderr
    summary = (root / "experiments" / "E0001-lr" / "results" / "summary.md").read_text()
    assert "baseline" in summary and "test_mse" in summary and "%" in summary


def test_dev_run_is_not_collected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "untracked.txt").write_text("dirty")
    args = [
        "--config",
        "experiments/E0001-lr/configs/baseline.toml",
        "--experiment",
        "E0001",
        "--variant",
        "baseline",
    ]
    r = script(root, "run.py", *args, "--dev")
    assert r.returncode == 0, r.stderr
    assert (root / "runs" / "dev").is_dir()
    assert script(root, "collect.py", "E0001").returncode == 1
