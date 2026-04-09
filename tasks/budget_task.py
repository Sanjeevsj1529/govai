from __future__ import annotations

from dataclasses import dataclass


SECTORS = ["health", "education", "infrastructure", "sanitation"]


@dataclass(frozen=True)
class BudgetScenario:
    budget: int
    ideal_allocation: dict[str, float]


SCENARIOS = [
    BudgetScenario(
        budget=100,
        ideal_allocation={"health": 0.3, "education": 0.25, "infrastructure": 0.3, "sanitation": 0.15},
    ),
    BudgetScenario(
        budget=120,
        ideal_allocation={"health": 0.35, "education": 0.2, "infrastructure": 0.25, "sanitation": 0.2},
    ),
    BudgetScenario(
        budget=90,
        ideal_allocation={"health": 0.25, "education": 0.3, "infrastructure": 0.2, "sanitation": 0.25},
    ),
]


def build_state(index: int = 0) -> dict[str, object]:
    scenario = SCENARIOS[index % len(SCENARIOS)]
    return {
        "task_id": "budget_task",
        "state": {
            "budget": scenario.budget,
            "sectors": list(SECTORS),
        },
        "metadata": {
            "ideal_allocation": dict(scenario.ideal_allocation),
            "actions": list(SECTORS),
        },
    }
