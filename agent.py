from __future__ import annotations


class GovtAgent:
    """
    Rule-based agent for the GovtAI Ops environment.

    State format:
    [pending_tasks, delayed_tasks, high_priority_tasks, average_workload, idle_employees]
    """

    def select_action(self, state: list[float]) -> int:
        """
        Choose one of the environment actions:

        0 -> assign to best-skilled employee
        1 -> assign to least busy employee
        2 -> reassign overloaded tasks
        3 -> prioritize urgent tasks
        """
        _pending_tasks, delayed_tasks, high_priority_tasks, average_workload, _idle_employees = state

        # If urgent work exists, deal with it first.
        if high_priority_tasks > 0:
            return 3

        # If delays are building up, try to rebalance the office.
        if delayed_tasks >= 2:
            return 2

        # If the team is carrying too much work on average, route to the least busy staff.
        if average_workload > 3.0:
            return 1

        # Otherwise, use the strongest available employee.
        return 0

    def explain_action(self, action: int) -> str:
        explanations = {
            0: "AI assigned the highest-priority task to the strongest available employee.",
            1: "AI assigned work to the least busy employee to keep workload balanced.",
            2: "AI redistributed tasks from overloaded employees to reduce delivery risk.",
            3: "AI prioritized urgent tasks first to avoid deadline breaches.",
        }
        return explanations.get(action, "AI selected a routing action for the current office state.")
