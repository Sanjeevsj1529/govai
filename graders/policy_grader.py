from __future__ import annotations


def grade_policy(action: str, scores: dict[str, float]) -> float:
    return max(0.0, min(1.0, float(scores.get(action, 0.0))))
