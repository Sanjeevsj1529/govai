from __future__ import annotations

from dataclasses import dataclass


DEPARTMENTS = ["municipality", "transport", "water", "electricity"]


@dataclass(frozen=True)
class ComplaintScenario:
    complaint_text: str
    correct_department: str


SCENARIOS = [
    ComplaintScenario(
        complaint_text="Streetlights in Ward 9 have not worked for three nights.",
        correct_department="electricity",
    ),
    ComplaintScenario(
        complaint_text="There is no water supply in my neighborhood since yesterday morning.",
        correct_department="water",
    ),
    ComplaintScenario(
        complaint_text="The main road bus stop has broken signage and unsafe traffic flow.",
        correct_department="transport",
    ),
    ComplaintScenario(
        complaint_text="Garbage has not been collected from our lane for a week.",
        correct_department="municipality",
    ),
]


def build_state(index: int = 0) -> dict[str, object]:
    scenario = SCENARIOS[index % len(SCENARIOS)]
    return {
        "task_id": "complaint_task",
        "state": scenario.complaint_text,
        "metadata": {
            "correct_department": scenario.correct_department,
            "actions": list(DEPARTMENTS),
        },
    }
