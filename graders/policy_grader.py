from __future__ import annotations


def grade_policy(action: str, scores: dict[str, float]) -> float:
    return max(0.01, min(0.99, float(scores.get(action, 0.01))))
