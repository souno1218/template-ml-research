from pathlib import Path

import pytest

from project_name import registry


def test_builtin_job_is_registered() -> None:
    assert "example" in registry.names("job")


def test_unknown_kind_and_name_raise() -> None:
    with pytest.raises(KeyError):
        registry.register("nope", "x")
    with pytest.raises(KeyError, match="登録済み"):
        registry.get("job", "does-not-exist")


def test_duplicate_name_raises() -> None:
    registry.register("metric", "dup_test")(len)
    with pytest.raises(KeyError, match="既に登録"):
        registry.register("metric", "dup_test")(abs)


def test_load_plugins_registers_and_skips_tests(tmp_path: Path) -> None:
    code = tmp_path / "E0099-x" / "code"
    code.mkdir(parents=True)
    (code / "plug.py").write_text(
        "from project_name.registry import register\n"
        "@register('model', 'plugin_model')\nclass M: ...\n"
    )
    (code / "test_plug.py").write_text("raise RuntimeError('読み込まれてはいけない')\n")
    registry.load_plugins([code])
    assert "plugin_model" in registry.names("model")
