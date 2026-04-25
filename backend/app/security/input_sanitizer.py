from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.config import settings

logger = logging.getLogger(__name__)

# ── Compiled injection detection patterns ─────────────────────────────────────
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"forget\s+your\s+(instructions?|role|prompt|rules?|training|guidelines?)",
        r"you\s+are\s+now\s+(?!being\s+asked)",
        r"pretend\s+(that\s+)?you\s+(are|were|can|have)",
        r"\bact\s+as\s+(if\s+you\s+(were|are)\s+)?(?!a\s+(participant|user|survey))",
        r"\bDAN\b",
        r"developer\s+mode",
        r"\bjailbreak\b",
        r"sudo\s+(mode|command|access)",
        r"override\s+(your\s+)?(instructions?|rules?|role|guidelines?|restrictions?)",
        r"reveal\s+(your\s+)?(prompt|instructions?|system\s+prompt|context|orders?)",
        r"bypass\s+(your\s+)?(safety|filter|rules?|guidelines?|restrictions?|limits?)",
        r"(what|tell\s+me)\s+(are|were|is)\s+your\s+(instructions?|orders?|system\s+prompt|prompt)",
        r"new\s+(instructions?|persona|role|character)\s*[:\-]",
        r"(assistant|ai|model|gpt)\s+mode",
        r"disable\s+(your\s+)?(filters?|safety|restrictions?|guardrails?)",
        r"simulate\s+(a\s+)?(different|another|new)\s+(ai|assistant|model|bot)",
        r"token\s+limit\s+bypass",
        r"(escape|exit|leave)\s+(character|role|persona|survey|interview)",
        r"hypothetically\s+speaking\s*,?\s*(if\s+you\s+(were|could|had\s+no))",
    ]
]


@dataclass
class SanitizationResult:
    is_safe: bool
    action: Literal["PASS", "BLOCK", "WARN"]
    matched_pattern: str | None = None
    matched_keyword: str | None = None
    reason: str | None = None


def _load_blocklist(path: str) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    return {
        line.strip().lower()
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


# Confusable-character map: visually similar Cyrillic/Greek/etc. → ASCII Latin.
# Applied AFTER NFKD so composed characters are already decomposed.
_CONFUSABLES: dict[int, str] = {
    # Cyrillic lookalikes
    0x0430: "a",  # а → a
    0x0435: "e",  # е → e
    0x0456: "i",  # і → i  (Ukrainian i)
    0x0457: "i",  # ї → i
    0x043E: "o",  # о → o
    0x0440: "r",  # р → r
    0x0441: "c",  # с → c
    0x0445: "x",  # х → x
    0x0443: "y",  # у → y
    0x0410: "A",  # А → A
    0x0415: "E",  # Е → E
    0x0406: "I",  # І → I
    0x041E: "O",  # О → O
    0x0420: "R",  # Р → R
    0x0421: "C",  # С → C
    0x0425: "X",  # Х → X
    # Greek lookalikes
    0x03BF: "o",  # ο → o  (Greek small omicron)
    0x03C1: "p",  # ρ → p  (Greek rho)
    0x03B5: "e",  # ε → e  (Greek epsilon)
    0x0391: "A",  # Α → A  (Greek capital alpha)
    0x0395: "E",  # Ε → E  (Greek capital epsilon)
    0x039F: "O",  # Ο → O  (Greek capital omicron)
}
_CONFUSABLES_TABLE = str.maketrans(_CONFUSABLES)


def _normalize(text: str) -> str:
    """
    Normalize unicode to catch lookalike-character substitution attacks.
    Applies NFKD decomposition followed by a confusable-character map that
    transliterates Cyrillic/Greek visual lookalikes to their ASCII equivalents.
    """
    return unicodedata.normalize("NFKD", text).translate(_CONFUSABLES_TABLE)


class InputSanitizer:
    def __init__(self) -> None:
        self._blocklist: set[str] = _load_blocklist(settings.jailbreak_blocklist_path)

    def check(self, text: str) -> SanitizationResult:
        # 1. Length guard
        if len(text) > settings.input_max_length:
            return SanitizationResult(
                is_safe=False,
                action="BLOCK",
                reason=f"Input exceeds maximum allowed length of {settings.input_max_length} characters",
            )

        # 2. Unicode normalization + control-character stripping
        normalized = _normalize(text)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", normalized)

        # 3. Regex injection-pattern scan
        for pattern in _INJECTION_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                logger.warning(
                    "InputSanitizer BLOCK | pattern=%s | snippet=%.80s",
                    pattern.pattern,
                    text,
                )
                return SanitizationResult(
                    is_safe=False,
                    action="BLOCK",
                    matched_pattern=pattern.pattern,
                    reason="Potential prompt injection pattern detected",
                )

        # 4. Jailbreak keyword dictionary scan
        lower = cleaned.lower()
        for keyword in self._blocklist:
            if keyword in lower:
                logger.warning(
                    "InputSanitizer BLOCK | keyword=%s | snippet=%.80s", keyword, text
                )
                return SanitizationResult(
                    is_safe=False,
                    action="BLOCK",
                    matched_keyword=keyword,
                    reason="Jailbreak keyword detected",
                )

        return SanitizationResult(is_safe=True, action="PASS")


input_sanitizer = InputSanitizer()
