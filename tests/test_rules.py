"""ルールを機械で守らせる検査。Proposal・索引・評価一式・入口の文書・hooks。"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from project_name.lab.proposals import (
    REQUIRED_SECTIONS,
    list_proposals,
    read_doc,
    render_indexes,
    rules_version,
    validate,
)
from project_name.lab.suite import list_suites, load_suite

ROOT = Path(__file__).resolve().parents[1]


def test_rules_version_is_an_integer() -> None:
    assert rules_version(ROOT) >= 1


def test_agents_md_matches_claude_md() -> None:
    claude, agents = (ROOT / "CLAUDE.md").read_text(), (ROOT / "AGENTS.md").read_text()
    assert claude == agents, "AGENTS.md は CLAUDE.md と同じ内容にする (cp CLAUDE.md AGENTS.md)"


def test_claude_md_points_to_existing_files() -> None:
    text = (ROOT / "CLAUDE.md").read_text()
    paths = re.findall(r"`((?:docs|\.okf)/[^`*<>]+?)`", text)
    assert "docs/rules/ai.md" in paths
    for rel in paths:
        assert (ROOT / rel).exists(), f"CLAUDE.md が指す {rel} がない"


@pytest.mark.parametrize("proposal", list_proposals(ROOT), ids=lambda p: p.stem)
def test_proposal_is_valid(proposal) -> None:
    errs = validate(proposal, ROOT)
    assert not errs, f"{proposal.path.name}:\n  " + "\n  ".join(errs)


def test_proposal_ids_are_unique() -> None:
    ids = [p.id for p in list_proposals(ROOT)]
    assert len(ids) == len(set(ids))


def test_indexes_are_up_to_date() -> None:
    for path, text in render_indexes(ROOT).items():
        assert path.exists() and path.read_text() == text, (
            f"{path.relative_to(ROOT)} が古い。uv run scripts/index.py で作り直す"
        )


def test_template_has_required_sections() -> None:
    body = read_doc(ROOT / "experiments" / "_template" / "proposal.md").body
    for sec in REQUIRED_SECTIONS:
        assert f"# {sec}" in body


@pytest.mark.parametrize("version", list_suites(ROOT))
def test_suite_files_are_unchanged(version: str) -> None:
    load_suite(version, ROOT).verify()


def test_hooks_point_to_existing_scripts() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    commands = [
        h["command"] for groups in settings["hooks"].values() for g in groups for h in g["hooks"]
    ]
    assert commands
    for cmd in commands:
        m = re.search(r"\$CLAUDE_PROJECT_DIR/([^\"]+)", cmd)
        assert m and (ROOT / m.group(1)).exists(), cmd
