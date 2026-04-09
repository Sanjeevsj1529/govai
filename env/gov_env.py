from __future__ import annotations

import random
from typing import Any

from graders.budget_grader import grade_budget
from graders.complaint_grader import grade_complaint
from graders.policy_grader import grade_policy
from tasks.budget_task import SECTORS, build_state as build_budget_state
from tasks.complaint_task import DEPARTMENTS, build_state as build_complaint_state
from tasks.policy_task import POLICY_OPTIONS, build_state as build_policy_state


TASK_ORDER = ("complaint_task", "policy_task", "budget_task")


class GovEnv:
    """Minimal OpenEnv-compatible environment for government decision workflows."""

    def __init__(self, task_id: str = "complaint_task", seed: int = 42) -> None:
        if task_id not in TASK_ORDER:
            raise ValueError(f"Unsupported task_id: {task_id}")
        self.seed = seed
        self.rng = random.Random(seed)
        self.task_id = task_id
        self._scenario_index = 0
        self.current_observation: dict[str, Any] = {}

    def reset(self, task_id: str | None = None) -> dict[str, Any]:
        if task_id is not None:
            if task_id not in TASK_ORDER:
                raise ValueError(f"Unsupported task_id: {task_id}")
            self.task_id = task_id

        builder = {
            "complaint_task": build_complaint_state,
            "policy_task": build_policy_state,
            "budget_task": build_budget_state,
        }[self.task_id]
        self.current_observation = builder(self._scenario_index)
        self._scenario_index += 1
        return self.current_observation

    def sample_action(self) -> Any:
        if self.task_id == "complaint_task":
            return self.rng.choice(DEPARTMENTS)
        if self.task_id == "policy_task":
            return self.rng.choice(POLICY_OPTIONS)

        weights = [self.rng.randint(1, 100) for _ in SECTORS]
        total = sum(weights)
        return {
            sector: round(weight / total, 2)
            for sector, weight in zip(SECTORS, weights)
        }

    def step(self, action: Any) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        if not self.current_observation:
            self.reset(self.task_id)

        metadata = self.current_observation["metadata"]
        if self.task_id == "complaint_task":
            reward = grade_complaint(str(action), str(metadata["correct_department"]))
        elif self.task_id == "policy_task":
            reward = grade_policy(str(action), dict(metadata["scores"]))
        else:
            reward = grade_budget(action if isinstance(action, dict) else {}, dict(metadata["ideal_allocation"]))

        reward = max(0.0, min(1.0, float(reward)))
        info = {
            "task_id": self.task_id,
            "reward": reward,
            "valid_actions": metadata["actions"],
        }
        return self.current_observation, reward, True, info
