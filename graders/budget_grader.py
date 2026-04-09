from __future__ import annotations


def grade_budget(action: dict[str, float], ideal_allocation: dict[str, float]) -> float:
    if not isinstance(action, dict) or not action:
        return 0.0

    total = float(sum(max(0.0, float(value)) for value in action.values()))
    if total <= 0:
        return 0.0

    normalized = {
        sector: max(0.0, float(action.get(sector, 0.0))) / total
        for sector in ideal_allocation
    }
    distance = sum(abs(normalized[sector] - float(target)) for sector, target in ideal_allocation.items())
    return max(0.0, min(1.0, 1.0 - (distance / 2.0)))
