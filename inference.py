from __future__ import annotations

import json
import sys
from typing import Any

from agent import GovtAgent
from env.gov_env import GovEnv


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


def run_openenv_demo() -> list[dict[str, Any]]:
    env = GovEnv(seed=42)
    episodes: list[dict[str, Any]] = []

    for task_id in ("complaint_task", "policy_task", "budget_task"):
        state = env.reset(task_id=task_id)
        action = env.sample_action()
        next_state, reward, done, info = env.step(action)
        episodes.append(
            {
                "task_id": task_id,
                "state": state,
                "action": action,
                "next_state": next_state,
                "reward": reward,
                "done": done,
                "info": info,
            }
        )

    return episodes


def emit_validator_blocks(episodes: list[dict[str, Any]]) -> None:
    for episode in episodes:
        task_id = str(episode["task_id"])
        reward = float(episode["reward"])
        action = episode["action"]

        print(f"[START]task={task_id}", flush=True)
        print(
            f"[STEP]step=1 reward={reward:.4f} done={str(bool(episode['done'])).lower()} action={json.dumps(action, separators=(',', ':'))}",
            flush=True,
        )
        print(f"[END]task={task_id} score={reward:.4f} steps=1", flush=True)


def main() -> None:
    emit_validator_blocks(run_openenv_demo())


if __name__ == "__main__":
    main()
