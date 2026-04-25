from __future__ import annotations

from unittest.mock import patch

import app.services.persona_manager as pm_module
from app.services.persona_manager import DEFAULT_PERSONAS, PersonaManager


def test_assign_random_returns_persona() -> None:
    manager = PersonaManager()
    persona = manager.assign_random()
    assert persona.name
    assert persona.voice_id
    assert persona.greeting_style


def test_assign_random_avoids_recent() -> None:
    manager = PersonaManager()
    names_seen: list[str] = []
    recent = ["Aria", "Marcus", "Priya"]

    # Run 30 times and check that we never immediately repeat
    for _ in range(30):
        persona = manager.assign_random(recent_persona_names=recent)
        assert persona.name not in recent
        names_seen.append(persona.name)


def test_assign_random_falls_back_when_all_recent() -> None:
    """If all personas are in recent list, falls back to full pool."""
    manager = PersonaManager()
    all_names = [p.name for p in manager._personas]
    persona = manager.assign_random(recent_persona_names=all_names)
    assert persona is not None
    assert persona.name in all_names


def test_get_by_name_case_insensitive() -> None:
    manager = PersonaManager()
    persona = manager.get_by_name("aria")
    assert persona is not None
    assert persona.name == "Aria"


def test_get_by_name_returns_none_for_unknown() -> None:
    manager = PersonaManager()
    assert manager.get_by_name("nonexistent") is None


def test_persona_to_dict_and_from_dict_roundtrip() -> None:
    manager = PersonaManager()
    persona = manager.assign_random()
    d = persona.to_dict()
    restored = type(persona).from_dict(d)
    assert restored.name == persona.name
    assert restored.voice_id == persona.voice_id


def test_load_personas_falls_back_to_defaults_when_yaml_missing(tmp_path: object) -> None:
    """Covers the final `return DEFAULT_PERSONAS` branch when personas.yaml is absent."""
    with patch.object(pm_module, "__file__", str(tmp_path) + "/fake_service.py"):  # type: ignore[arg-type]
        manager = PersonaManager()
    expected_names = {p["name"] for p in DEFAULT_PERSONAS}
    actual_names = {p.name for p in manager._personas}
    assert actual_names == expected_names


def test_load_personas_falls_back_on_yaml_parse_error() -> None:
    """Covers the `except Exception: pass` handler and subsequent fallback."""
    import yaml

    with patch.object(yaml, "safe_load", side_effect=ValueError("bad yaml")):
        manager = PersonaManager()
    # Exception was caught; PersonaManager should still be usable via DEFAULT_PERSONAS
    assert len(manager._personas) == len(DEFAULT_PERSONAS)
    assert manager._personas[0].name == DEFAULT_PERSONAS[0]["name"]
