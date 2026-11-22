from pathlib import Path

import pytest

from project_name.lab.suite import load_suite, sha256


def _suite(root: Path) -> Path:
    d = root / "bench" / "suites" / "v1"
    d.mkdir(parents=True)
    (d / "test.csv").write_text("x,y\n1,2\n")
    (d / "suite.toml").write_text(
        f'version = "v1"\n[sets.test]\nfile = "test.csv"\n'
        f'sha256 = "{sha256(d / "test.csv")}"\nn = 1\n'
    )
    return d


def test_verify_and_fingerprint(tmp_path: Path) -> None:
    d = _suite(tmp_path)
    suite = load_suite("v1", tmp_path)
    suite.verify()
    assert suite.path("test") == d / "test.csv"
    assert suite.fingerprint() == sha256(d / "suite.toml")


def test_changed_data_is_detected(tmp_path: Path) -> None:
    d = _suite(tmp_path)
    (d / "test.csv").write_text("x,y\n1,3\n")
    with pytest.raises(ValueError, match="変更されている"):
        load_suite("v1", tmp_path).verify()


def test_version_must_match_directory(tmp_path: Path) -> None:
    d = _suite(tmp_path)
    (d / "suite.toml").write_text('version = "v2"\n')
    with pytest.raises(ValueError, match="version"):
        load_suite("v1", tmp_path)
