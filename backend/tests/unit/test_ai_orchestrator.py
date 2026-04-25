from __future__ import annotations

from app.services.ai_orchestrator import AIOrchestratorService


def test_confidence_from_avg_logprob_boundary_values() -> None:
    assert AIOrchestratorService._confidence_from_avg_logprob(-5.0) == 0.0
    assert AIOrchestratorService._confidence_from_avg_logprob(-1.55) == 0.69
    assert AIOrchestratorService._confidence_from_avg_logprob(-1.5) == 0.70
    assert AIOrchestratorService._confidence_from_avg_logprob(0.0) == 1.0


def test_confidence_from_segments_with_dict_values() -> None:
    segments = [{"avg_logprob": -2.0}, {"avg_logprob": -1.0}]
    # mean=-1.5 -> confidence=0.70
    assert AIOrchestratorService._confidence_from_segments(segments) == 0.70


def test_confidence_from_segments_defaults_to_one_when_unavailable() -> None:
    assert AIOrchestratorService._confidence_from_segments([]) == 1.0
    assert AIOrchestratorService._confidence_from_segments(None) == 1.0
