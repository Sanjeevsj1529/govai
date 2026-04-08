from __future__ import annotations

from typing import Any


TASK_TYPES = ("easy", "medium", "hard")


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _extract_metrics(metrics: dict[str, Any]) -> tuple[float, float, float]:
    total_tasks = max(1, int(metrics.get("total_tasks", 0)))
    completed_tasks = max(0, int(metrics.get("completed_tasks", 0)))
    delayed_tasks = max(0, int(metrics.get("delayed_tasks", 0)))

    completion_rate = float(metrics.get("completion_rate", completed_tasks / total_tasks))
    delay_ratio = float(metrics.get("delay_ratio", delayed_tasks / total_tasks))
    workload_balance = float(metrics.get("workload_balance", 0.0))

    return (
        _clamp(completion_rate),
        _clamp(delay_ratio),
        _clamp(workload_balance),
    )


def grade_task(metrics: dict[str, Any], task_type: str = "medium") -> tuple[float, str]:
    if task_type not in TASK_TYPES:
        raise ValueError(f"Unsupported task_type: {task_type}")

    completion_rate, delay_ratio, workload_balance = _extract_metrics(metrics)
    score = (
        0.5 * completion_rate
        + 0.3 * (1 - delay_ratio)
        + 0.2 * workload_balance
    )
    score = round(_clamp(score), 4)
    return score, performance_label(score)


def evaluate_performance(metrics: dict[str, Any], task_type: str = "medium") -> tuple[float, str]:
    return grade_task(metrics, task_type=task_type)


def performance_label(score: float) -> str:
    """Convert a numeric score into a simple performance label."""
    if score < 0.4:
        return "Poor"
    if score <= 0.6:
        return "Average"
    if score <= 0.8:
        return "Good"
    return "Optimal"
