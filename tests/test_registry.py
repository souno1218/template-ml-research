from pathlib import Path

import pytest

from project_name import registry


def test_register_and_get() -> None:
    @registry.register("test_kind", "a")
    class A:
        pass

    assert registry.get("test_kind", "a") is A
    assert "a" in registry.names("test_kind")


def test_duplicate_registration_is_rejected() -> None:
    registry.register("test_kind", "dup")(object)
    with pytest.raises(ValueError):
        registry.register("test_kind", "dup")(object)


def test_unknown_name_lists_candidates() -> None:
    with pytest.raises(KeyError, match="registered"):
        registry.get("test_kind", "missing")


def test_load_plugins_registers_from_directory(tmp_path: Path) -> None:
    (tmp_path / "plug.py").write_text(
        "from project_name.registry import register\n\n"
        "@register('plugin_kind', 'p')\n"
        "def p() -> int:\n    return 1\n"
    )
    registry.load_plugins([tmp_path])
    assert registry.get("plugin_kind", "p")() == 1
