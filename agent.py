from __future__ import annotations
import os
import re
import logging

logger = logging.getLogger(__name__)

# Lazy client — created on first use so the module can import safely
# even when env vars are not yet set.
_client = None


def _get_client():
    """Return a cached OpenAI client using ONLY the proxy env vars."""
    global _client
    if _client is not None:
        return _client

    base_url = os.getenv("API_BASE_URL")
    api_key = os.getenv("API_KEY")

    if not base_url or not api_key:
        logger.warning(
            "API_BASE_URL or API_KEY not set — LLM calls will use heuristic fallback."
        )
        return None

    from openai import OpenAI  # import here so missing package is caught gracefully

    _client = OpenAI(base_url=base_url, api_key=api_key)
    logger.info("OpenAI proxy client initialised (base_url=%s)", base_url)
    return _client


class GovtAgent:
    """
    Expert AI agent for government task allocation.
    Uses dedicated proxy with robust error handling and debugging.
    """

    def __init__(self):
        self.last_reason = "System Initialized. Awaiting first operational decision."

    # ------------------------------------------------------------------ #
    #  Core LLM call
    # ------------------------------------------------------------------ #
    def get_llm_decision(self, state: list[float]) -> str:
        """
        Calls the LLM via proxy to get a decision based on the system state.
        Includes mandatory debugging and 10s timeout.
        """
        client = _get_client()
        if client is None:
            return self._heuristic_decision(state)

        try:
            prompt = (
                f"System state (pending, delayed, high_priority, workload, idle): {state}. "
                "Actions: 0:assign_best, 1:assign_least_busy, 2:reassign, 3:prioritize_urgent. "
                "Respond ONLY as: 'Action ID: [0-3] | Reason: [one-line description]'"
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI optimizing government task allocation. "
                                   "Always reply in the exact format requested.",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=10,
            )

            # MANDATORY DEBUGGING
            print("LLM RESPONSE:", response, flush=True)

            content = response.choices[0].message.content
            return content.strip()

        except Exception as e:
            error_msg = f"LLM Error: {e}"
            print(f"DEBUG: {error_msg}", flush=True)
            logger.error(error_msg)
            return f"Action ID: 1 | Reason: {error_msg}"

    # ------------------------------------------------------------------ #
    #  Heuristic fallback (when proxy is not configured)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _heuristic_decision(state: list[float]) -> str:
        pending, delayed, high_pri, workload, idle = (
            state[0] if len(state) > 0 else 0,
            state[1] if len(state) > 1 else 0,
            state[2] if len(state) > 2 else 0,
            state[3] if len(state) > 3 else 0,
            state[4] if len(state) > 4 else 0,
        )
        if delayed > 0:
            return "Action ID: 2 | Reason: Delayed tasks detected — reassigning to restore SLA compliance."
        if high_pri > 0:
            return "Action ID: 3 | Reason: High-priority tasks in queue — escalating urgency."
        if idle > 0:
            return "Action ID: 1 | Reason: Idle employees available — distributing backlog by least-busy."
        return "Action ID: 0 | Reason: Steady state — routing to best-skilled employee."

    # ------------------------------------------------------------------ #
    #  Action selection
    # ------------------------------------------------------------------ #
    def select_action(self, state: list[float]) -> int:
        """Decides on an action using the LLM engine (or heuristic fallback)."""
        raw_output = self.get_llm_decision(state)
        self.last_reason = raw_output

        try:
            match = re.search(r"Action ID:\s*([0-3])", raw_output, re.IGNORECASE)
            if match:
                return int(match.group(1))

            match = re.search(r"(\d)", raw_output)
            if match:
                val = int(match.group(1))
                return max(0, min(3, val))

            return 0
        except Exception:
            return 0

    def explain_action(self, action: int) -> str:
        """Returns the raw LLM / heuristic output for display in the UI."""
        return self.last_reason
