from __future__ import annotations

from dataclasses import dataclass


POLICY_OPTIONS = ["targeted_subsidy", "infrastructure_push", "digital_outreach", "staff_expansion"]


@dataclass(frozen=True)
class PolicyScenario:
    scenario: str
    scores: dict[str, float]


SCENARIOS = [
    PolicyScenario(
        scenario="Rural clinics are seeing medicine stock-outs and long travel times for patients.",
        scores={
            "targeted_subsidy": 0.45,
            "infrastructure_push": 0.95,
            "digital_outreach": 0.35,
            "staff_expansion": 0.7,
        },
    ),
    PolicyScenario(
        scenario="Urban households eligible for benefits are missing deadlines because of low awareness.",
        scores={
            "targeted_subsidy": 0.55,
            "infrastructure_push": 0.4,
            "digital_outreach": 0.9,
            "staff_expansion": 0.5,
        },
    ),
    PolicyScenario(
        scenario="A district has enough physical facilities but a severe shortage of case workers.",
        scores={
            "targeted_subsidy": 0.35,
            "infrastructure_push": 0.3,
            "digital_outreach": 0.5,
            "staff_expansion": 0.92,
        },
    ),
]


def build_state(index: int = 0) -> dict[str, object]:
    scenario = SCENARIOS[index % len(SCENARIOS)]
    return {
        "task_id": "policy_task",
        "state": scenario.scenario,
        "metadata": {
            "scores": dict(scenario.scores),
            "actions": list(POLICY_OPTIONS),
        },
    }
