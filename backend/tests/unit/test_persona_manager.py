from __future__ import annotations

from app.services.persona_manager import PersonaManager


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
