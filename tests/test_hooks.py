"""Claude Code の hooks が止めるべき操作を止め、ほかは通すこと。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "scripts" / "hooks"


def run_hook(name: str, data: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        check=False,
    )


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "bench" / "suites" / "v1").mkdir(parents=True)
    (tmp_path / "bench" / "suites" / "v1" / "suite.toml").write_text('version = "v1"\n')
    (tmp_path / "docs" / "rules").mkdir(parents=True)
    (tmp_path / "docs" / "rules" / "VERSION").write_text("1\n")
    (tmp_path / ".okf" / "proposals").mkdir(parents=True)
    (tmp_path / ".okf" / "proposals" / "E0001-lr.md").write_text(
        "---\ntype: Proposal\nid: E0001\nkind: model\nbranch: exp/E0001-lr\n---\n"
    )
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def edit(repo: Path, rel: str) -> subprocess.CompletedProcess:
    return run_hook(
        "guard_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(repo / rel)}}
    )


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push -u origin main",
        "git push --force origin exp/E0001-lr",
        "git reset --hard HEAD~1",
        "git clean -fd",
        "git branch -D exp/E0001-lr",
        "git commit --no-verify -m x",
    ],
)
def test_guard_bash_blocks(command: str) -> None:
    r = run_hook("guard_bash.py", {"tool_input": {"command": command}})
    assert r.returncode == 2, command
    assert "止めました" in r.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin exp/E0001-lr",
        "git status",
        "uv run pytest",
        "git push origin claude/main-fix",
    ],
)
def test_guard_bash_allows(command: str) -> None:
    assert run_hook("guard_bash.py", {"tool_input": {"command": command}}).returncode == 0


def test_frozen_suite_is_blocked_everywhere(repo: Path) -> None:
    assert edit(repo, "bench/suites/v1/suite.toml").returncode == 2
    assert edit(repo, "bench/suites/v1/new.npz").returncode == 2
    assert (
        edit(repo, "bench/suites/v2/suite.toml").returncode == 0
    )  # 施策のブランチでなければ新しい版は止めない


def test_model_experiment_cannot_touch_bench_or_rules(repo: Path) -> None:
    git(repo, "switch", "-q", "-c", "exp/E0001-lr")
    assert edit(repo, "bench/suites/v2/suite.toml").returncode == 2
    assert edit(repo, "docs/rules/ai.md").returncode == 2
    assert edit(repo, "CLAUDE.md").returncode == 2
    assert edit(repo, "src/project_name/model.py").returncode == 0


def test_infra_experiment_can_touch_rules(repo: Path) -> None:
    p = repo / ".okf" / "proposals" / "E0001-lr.md"
    p.write_text(p.read_text().replace("kind: model", "kind: infra"))
    git(repo, "switch", "-q", "-c", "exp/E0001-lr")
    assert edit(repo, "docs/rules/ai.md").returncode == 0
    assert edit(repo, "bench/suites/v2/suite.toml").returncode == 2


def test_session_start_prints_location(repo: Path) -> None:
    git(repo, "switch", "-q", "-c", "exp/E0001-lr")
    r = run_hook("session_start.py", {"cwd": str(repo)})
    assert r.returncode == 0
    assert "ルール v1" in r.stdout and "E0001" in r.stdout
