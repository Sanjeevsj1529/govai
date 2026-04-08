from __future__ import annotations

import json
import sys
from typing import Any

from agent import GovtAgent


agent = GovtAgent()


def _state_from_observation(observation: dict[str, Any]) -> list[float]:
    return [
        float(observation.get("pending_tasks", 0)),
        float(observation.get("delayed_tasks", 0)),
        float(observation.get("high_priority_tasks", 0)),
        float(observation.get("avg_workload", 0.0)),
        float(observation.get("idle_employees", 0)),
    ]


def infer(observation: dict[str, Any]) -> int:
    return agent.select_action(_state_from_observation(observation))


def predict(observation: dict[str, Any]) -> int:
    return infer(observation)


def main() -> None:
    payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    observation = payload.get("observation", payload)
    action = infer(observation if isinstance(observation, dict) else {})
    json.dump({"action": action}, sys.stdout)


if __name__ == "__main__":
    main()
