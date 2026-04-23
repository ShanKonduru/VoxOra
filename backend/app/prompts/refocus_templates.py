from __future__ import annotations

import random

# ── Refocusing phrase templates ───────────────────────────────────────────────
# {question_brief} is replaced at runtime with a short version of the question.

REFOCUS_PHRASES: list[str] = [
    (
        "I appreciate you sharing that. To make the best use of your time, "
        "let's return to our survey — {question_brief}"
    ),
    (
        "That's an interesting thought. However, for the purposes of this "
        "interview, I'd like to focus on: {question_brief}"
    ),
    (
        "I understand. To keep us on track, my question for you was: "
        "{question_brief}"
    ),
    (
        "Thank you for that. Let's refocus on the survey question — "
        "{question_brief}"
    ),
    (
        "I hear you. To respect your time and the structure of this interview, "
        "let me bring us back to: {question_brief}"
    ),
    (
        "Noted. My interview question for you remains: {question_brief} — "
        "whenever you're ready."
    ),
    (
        "Let's stay with our survey. The question I'd like you to address is: "
        "{question_brief}"
    ),
    (
        "I appreciate the thought, but for this survey I need to ask you "
        "specifically about: {question_brief}"
    ),
]

# After this many consecutive refocusing attempts, the question is skipped.
MAX_REFOCUS_BEFORE_SKIP = 3


def get_refocus_phrase(question_brief: str) -> str:
    """Return a randomly selected refocusing phrase with the question injected."""
    template = random.choice(REFOCUS_PHRASES)
    return template.format(question_brief=question_brief)


def get_skip_message() -> str:
    """Message delivered when a question is skipped after too many refocuses."""
    return (
        "I understand this question may be difficult to address right now. "
        "Let's move on to the next question."
    )


def get_repeat_request() -> str:
    """Message delivered when audio quality is too low to transcribe."""
    return (
        "I'm sorry, I didn't quite catch that. Could you please repeat "
        "your answer a little more clearly?"
    )
