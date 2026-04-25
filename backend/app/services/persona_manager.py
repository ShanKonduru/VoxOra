from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List

DEFAULT_PERSONAS: List[dict] = [
    {"name": "Aria",   "gender": "female",  "accent": "British RP",        "voice_id": "nova",    "greeting_style": "formal"},
    {"name": "Marcus", "gender": "male",    "accent": "Neutral American",   "voice_id": "onyx",    "greeting_style": "professional"},
    {"name": "Priya",  "gender": "female",  "accent": "Indian English",     "voice_id": "shimmer", "greeting_style": "academic"},
    {"name": "James",  "gender": "male",    "accent": "Australian",         "voice_id": "echo",    "greeting_style": "formal"},
    {"name": "Sofia",  "gender": "female",  "accent": "Neutral American",   "voice_id": "alloy",   "greeting_style": "professional"},
    {"name": "Chen",   "gender": "neutral", "accent": "Neutral American",   "voice_id": "fable",   "greeting_style": "academic"},
]


@dataclass
class Persona:
    name: str
    gender: str
    accent: str
    voice_id: str
    greeting_style: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "gender": self.gender,
            "accent": self.accent,
            "voice_id": self.voice_id,
            "greeting_style": self.greeting_style,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        return cls(
            name=data["name"],
            gender=data["gender"],
            accent=data["accent"],
            voice_id=data["voice_id"],
            greeting_style=data["greeting_style"],
        )


class PersonaManager:
    def __init__(self) -> None:
        self._personas: List[Persona] = self._load_personas()

    def _load_personas(self) -> List[Persona]:
        yaml_file = Path(__file__).parent.parent / "prompts" / "personas.yaml"
        if yaml_file.exists():
            try:
                import yaml  # type: ignore

                with yaml_file.open() as f:
                    data = yaml.safe_load(f)
                    return [Persona.from_dict(p) for p in data.get("personas", [])]
            except Exception:
                pass
        return [Persona.from_dict(p) for p in DEFAULT_PERSONAS]

    def assign_random(
        self, recent_persona_names: List[str] | None = None
    ) -> Persona:
        """
        Randomly assign a persona, avoiding recent ones to ensure variety.
        Falls back to full pool if all personas have been used recently.
        """
        available = self._personas
        if recent_persona_names and len(self._personas) > len(recent_persona_names):
            available = [
                p for p in self._personas if p.name not in recent_persona_names[-3:]
            ]
        if not available:  # pragma: no cover  — filter guard, unreachable with ≥4 personas
            available = self._personas
        return random.choice(available)

    def get_by_name(self, name: str) -> Persona | None:
        for p in self._personas:
            if p.name.lower() == name.lower():
                return p
        return None


persona_manager = PersonaManager()
