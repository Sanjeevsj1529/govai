from __future__ import annotations

import os
import json
from typing import Any
from openai import OpenAI

from env.gov_env import GovEnv

_VALIDATOR_OUTPUT_EMITTED = False

def get_llm_action(task_id: str, state: dict[str, Any], env: GovEnv) -> Any:
    base_url = os.environ.get("API_BASE_URL")
    api_key = os.environ.get("API_KEY", "dummy-key")
    
    if not base_url:
        return env.sample_action()
        
    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        actions = state["metadata"]["actions"]
        if task_id == "budget_task":
            prompt = f"Given state: {state['state']}. Allocate a budget across {actions}. Return only a JSON dict with sectors as keys and proportions (summing to 1.0) as values."
        else:
            prompt = f"Given state: {state['state']}. Choose one of: {actions}. Return ONLY the exact name of your choice."
            
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )
        content = resp.choices[0].message.content.strip()
        
        if task_id == "budget_task":
            import re
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            return json.loads(content)
        else:
            for act in actions:
                if act in content:
                    return act
    except Exception as e:
        print(f"API Exception: {e}")
        
    return env.sample_action()


def run_openenv_demo() -> list[dict[str, Any]]:
    env = GovEnv(seed=42)
    episodes: list[dict[str, Any]] = []

    for task_id in ("complaint_task", "policy_task", "budget_task"):
        state = env.reset(task_id=task_id)
        action = get_llm_action(task_id, state, env)
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
