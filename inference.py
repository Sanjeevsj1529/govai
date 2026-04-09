from __future__ import annotations

from typing import Any

from env.gov_env import GovEnv

_VALIDATOR_OUTPUT_EMITTED = False


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
    global _VALIDATOR_OUTPUT_EMITTED
    _VALIDATOR_OUTPUT_EMITTED = True
    overall_score = sum(float(episode["reward"]) for episode in episodes) / max(1, len(episodes))
    print("[START] task=govai", flush=True)
    print(f"[STEP] step=1 reward={overall_score:.4f}", flush=True)
    print(f"[END] task=govai score={overall_score:.4f} steps=1", flush=True)

    for episode in episodes:
        task_id = str(episode["task_id"])
        reward = float(episode["reward"])

        # Emit the simplest possible parser-friendly block format.
        print(f"[START] task={task_id}", flush=True)
        print(f"[STEP] step=1 reward={reward:.4f}", flush=True)
        print(f"[END] task={task_id} score={reward:.4f} steps=1", flush=True)


def main() -> None:
    if not _VALIDATOR_OUTPUT_EMITTED:
        emit_validator_blocks(run_openenv_demo())


if __name__ != "__main__":
    emit_validator_blocks(run_openenv_demo())


if __name__ == "__main__":
    main()
