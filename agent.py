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
                f"System state (pending={state[0] if len(state)>0 else 0}, "
                f"delayed={state[1] if len(state)>1 else 0}, "
                f"high_priority={state[2] if len(state)>2 else 0}, "
                f"avg_workload={state[3] if len(state)>3 else 0:.2f}, "
                f"idle_employees={state[4] if len(state)>4 else 0}). "
                "Available actions: 0:assign_best, 1:assign_least_busy, 2:reassign, 3:prioritize_urgent. "
                "Respond STRICTLY in this format (no extra text):\n"
                "Action ID: [0-3]\n"
                "Recommended Action: <action name>\n"
                "Reasoning: <one clear sentence explaining why>\n"
                "Impact: <one measurable benefit>\n"
                "Confidence Score: <0-100>%"
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI optimizing government task allocation. "
                                   "Always reply ONLY in the exact structured format requested, nothing else.",
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
            # Return structured fallback so the UI never shows raw errors
            return (
                f"Action ID: 1\n"
                f"Recommended Action: assign_least_busy\n"
                f"Reasoning: LLM unavailable — using fallback logic based on current queue state.\n"
                f"Impact: Ensures tasks continue flowing without interruption.\n"
                f"Confidence Score: 60%"
            )

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
            return (
                "Action ID: 2\n"
                "Recommended Action: reassign\n"
                f"Reasoning: {int(delayed)} delayed task(s) detected — reassigning to restore SLA compliance.\n"
                "Impact: Reduces backlog delay and restores on-time delivery rate.\n"
                "Confidence Score: 85%"
            )
        if high_pri > 0:
            return (
                "Action ID: 3\n"
                "Recommended Action: prioritize_urgent\n"
                f"Reasoning: {int(high_pri)} high-priority task(s) in queue — escalating urgency.\n"
                "Impact: Fast-tracks critical civic-service cases to meet strict deadlines.\n"
                "Confidence Score: 90%"
            )
        if idle > 0:
            return (
                "Action ID: 1\n"
                "Recommended Action: assign_least_busy\n"
                f"Reasoning: {int(idle)} idle employee(s) available — distributing backlog by least-busy.\n"
                "Impact: Improves workload balance and reduces idle capacity waste.\n"
                "Confidence Score: 88%"
            )
        return (
            "Action ID: 0\n"
            "Recommended Action: assign_best\n"
            "Reasoning: Steady state — routing tasks to the best-skilled available employee.\n"
            "Impact: Maximises task completion quality and throughput efficiency.\n"
            "Confidence Score: 82%"
        )

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
