from __future__ import annotations

import random
from collections import deque

from models import Employee, EnvironmentState, Task
from reward import RewardBreakdown, calculate_reward

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
ACTION_NAMES = {
    0: "assign_best",
    1: "assign_least_busy",
    2: "reassign",
    3: "prioritize_urgent",
}
MODE_CONFIG = {
    "easy": {
        "employees": 3,
        "tasks": 6,
        "max_steps": 15,
        "deadline_jitter": 0,
        "incoming_tasks": (0, 0),
        "objective": "Complete straightforward citizen-service requests with minimal idle time.",
    },
    "medium": {
        "employees": 5,
        "tasks": 10,
        "max_steps": 20,
        "deadline_jitter": 1,
        "incoming_tasks": (0, 1),
        "objective": "Reduce delays while balancing workload across multiple departments.",
    },
    "hard": {
        "employees": 8,
        "tasks": 16,
        "max_steps": 30,
        "deadline_jitter": 2,
        "incoming_tasks": (1, 2),
        "objective": "Handle dynamic incoming tasks, overload, and urgent prioritization.",
    },
}


class GovtEnv:
    """
    Government task allocation environment following the standard OpenEnv loop.

    Observation vector:
    [pending_tasks, delayed_tasks, high_priority_tasks, average_workload, idle_employees]
    """

    def __init__(self, mode: str = "medium", seed: int | None = None) -> None:
        if mode not in MODE_CONFIG:
            raise ValueError(f"Unsupported mode: {mode}. Choose from {tuple(MODE_CONFIG)}.")

        self.mode = mode
        self.task_type = mode
        self.config = MODE_CONFIG[mode]
        self.seed = 42 if seed is None else seed
        self.rng = random.Random(self.seed)

        self.time_step = 0
        self.tasks: list[Task] = []
        self.employees: list[Employee] = []
        self.max_steps = self.config["max_steps"]
        self.next_task_id = 1
        self.action_history: deque[int] = deque(maxlen=3)

    def reset(self) -> list[float]:
        self.rng = random.Random(self.seed)
        self.time_step = 0
        self.max_steps = self.config["max_steps"]
        self.next_task_id = 1
        self.action_history.clear()
        self.employees = self._create_employees()
        self.tasks = self._create_tasks(self.config["tasks"])
        self._refresh_workloads()
        return self.get_state()

    def step(self, action: int) -> tuple[list[float], float, bool, dict]:
        if action not in {0, 1, 2, 3}:
            raise ValueError("Action must be one of 0, 1, 2, or 3.")

        action_name = self._apply_action(action)
        completed_now, early_completed_now, progress_now = self._simulate_task_completion()

        self.time_step += 1
        new_incoming_tasks = self._inject_dynamic_tasks()
        delayed_now = self._mark_delayed_tasks()
        self._refresh_workloads()

        idle_employees = sum(employee.current_workload == 0 for employee in self.employees)
        repeated_bad_decision = self._repeated_bad_decision_penalty(action)
        reward_breakdown = RewardBreakdown(
            completion=completed_now,
            early_completion=early_completed_now,
            progress=progress_now,
            idle=idle_employees,
            delay=delayed_now,
            repeated_bad_decision=repeated_bad_decision,
        )
        reward = float(calculate_reward(reward_breakdown))

        done = self.time_step >= self.max_steps or self._all_tasks_finished()
        next_state = self.get_state()
        info = {
            "action_name": action_name,
            "time_step": self.time_step,
            "completed_this_step": completed_now,
            "early_completed_this_step": early_completed_now,
            "progress_this_step": progress_now,
            "new_delays": delayed_now,
            "incoming_tasks": new_incoming_tasks,
            "idle_employees": idle_employees,
            "reward_breakdown": reward_breakdown.as_dict(),
        }
        self.action_history.append(action)
        return next_state, reward, done, info

    def state(self) -> list[float]:
        return self.get_state()

    def get_state(self) -> list[float]:
        return self.get_environment_state().vector()

    def get_environment_state(self) -> EnvironmentState:
        pending_tasks = sum(task.status in {"pending", "in_progress"} for task in self.tasks)
        delayed_tasks = sum(task.status == "delayed" for task in self.tasks)
        high_priority_tasks = sum(
            task.priority == "high" and task.status != "completed" for task in self.tasks
        )
        average_workload = (
            sum(employee.current_workload for employee in self.employees) / len(self.employees)
            if self.employees
            else 0.0
        )
        idle_employees = sum(employee.current_workload == 0 for employee in self.employees)
        completed_tasks = sum(task.status == "completed" for task in self.tasks)

        return EnvironmentState(
            task_type=self.task_type,
            time_step=self.time_step,
            pending_tasks=pending_tasks,
            delayed_tasks=delayed_tasks,
            high_priority_tasks=high_priority_tasks,
            average_workload=round(average_workload, 2),
            idle_employees=idle_employees,
            completed_tasks=completed_tasks,
            total_tasks=len(self.tasks),
        )

    def get_metrics(self) -> dict[str, float | int | str]:
        total_tasks = max(1, len(self.tasks))
        completed_tasks = sum(task.status == "completed" for task in self.tasks)
        delayed_tasks = sum(task.status == "delayed" for task in self.tasks)
        workloads = [employee.current_workload for employee in self.employees]
        avg_workload = sum(workloads) / len(workloads) if workloads else 0.0

        if not workloads:
            workload_balance = 1.0
        else:
            avg_deviation = sum(abs(workload - avg_workload) for workload in workloads) / len(workloads)
            workload_balance = 1.0 / (1.0 + avg_deviation)

        return {
            "task_type": self.task_type,
            "total_tasks": len(self.tasks),
            "completed_tasks": completed_tasks,
            "delayed_tasks": delayed_tasks,
            "avg_workload": round(avg_workload, 2),
            "completion_rate": round(completed_tasks / total_tasks, 4),
            "delay_ratio": round(delayed_tasks / total_tasks, 4),
            "workload_balance": round(max(0.0, min(1.0, workload_balance)), 4),
            "objective": self.config["objective"],
        }

    def _create_employees(self) -> list[Employee]:
        return [
            Employee(id=employee_id, skill_level=self.rng.randint(1, 5))
            for employee_id in range(1, self.config["employees"] + 1)
        ]

    def _create_tasks(self, count: int) -> list[Task]:
        tasks: list[Task] = []
        for _ in range(count):
            priority = self.rng.choices(
                population=["low", "medium", "high"],
                weights=self._priority_weights(),
                k=1,
            )[0]
            base_deadline = {"low": 7, "medium": 5, "high": 3}[priority]
            jitter = self.rng.randint(0, self.config["deadline_jitter"])
            deadline = self.time_step + base_deadline + jitter
            effort = PRIORITY_SCORES[priority] + self.rng.randint(0, self.config["deadline_jitter"] + 1)
            tasks.append(
                Task(
                    id=self.next_task_id,
                    priority=priority,
                    deadline=deadline,
                    created_at=self.time_step,
                    remaining_effort=max(1, effort),
                )
            )
            self.next_task_id += 1
        return tasks

    def _inject_dynamic_tasks(self) -> int:
        minimum, maximum = self.config["incoming_tasks"]
        if maximum == 0:
            return 0
        incoming_count = self.rng.randint(minimum, maximum)
        if incoming_count <= 0:
            return 0
        self.tasks.extend(self._create_tasks(incoming_count))
        self._refresh_workloads()
        return incoming_count

    def _priority_weights(self) -> tuple[int, int, int]:
        if self.mode == "easy":
            return (4, 3, 2)
        if self.mode == "medium":
            return (3, 3, 3)
        return (2, 3, 5)

    def _apply_action(self, action: int) -> str:
        if action == 0:
            self._assign_task_to_best_skill()
        elif action == 1:
            self._assign_task_to_least_busy()
        elif action == 2:
            self._reassign_overloaded_tasks()
        else:
            self._prioritize_urgent_tasks()
        return ACTION_NAMES[action]

    def _assign_task_to_best_skill(self) -> None:
        self._distribute_unassigned_tasks(order="priority", prefer_best_skill=True)

    def _assign_task_to_least_busy(self) -> None:
        self._distribute_unassigned_tasks(order="deadline", prefer_best_skill=False)

    def _reassign_overloaded_tasks(self) -> None:
        overloaded = [employee for employee in self.employees if employee.current_workload > 6]
        available_targets = sorted(self.employees, key=lambda item: (item.current_workload, -item.skill_level))

        for source in overloaded:
            candidate = self._pick_reassignable_task(source.id)
            if candidate is None:
                continue
            target = next((employee for employee in available_targets if employee.id != source.id), None)
            if target is None:
                continue

            candidate.assigned_employee = target.id
            if candidate.status == "pending":
                candidate.status = "in_progress"

        self._refresh_workloads()

    def _prioritize_urgent_tasks(self) -> None:
        urgent_tasks = self._unassigned_tasks()
        urgent_tasks.sort(
            key=lambda task: (
                task.deadline - self.time_step,
                -PRIORITY_SCORES[task.priority],
                task.id,
            )
        )
        if not urgent_tasks:
            return

        queue = urgent_tasks[: max(2, len(self.employees))]
        for task in queue:
            employee = min(
                self.employees,
                key=lambda item: (item.current_workload, self._target_employee_load(item), -item.skill_level),
            )
            self._assign_task(task, employee)

        self._fill_employee_backlog(order="deadline")

    def _assign_task(self, task: Task, employee: Employee) -> None:
        if task.status == "completed":
            return
        task.assigned_employee = employee.id
        task.last_assigned_employee = employee.id
        if task.status in {"pending", "delayed"}:
            task.status = "in_progress"
        self._refresh_workloads()

    def _pick_unassigned_task(self, order: str) -> Task | None:
        tasks = self._unassigned_tasks()
        if not tasks:
            return None

        if order == "priority":
            tasks.sort(key=lambda task: (-PRIORITY_SCORES[task.priority], task.deadline, task.id))
        else:
            tasks.sort(key=lambda task: (task.deadline, -PRIORITY_SCORES[task.priority], task.id))
        return tasks[0]

    def _distribute_unassigned_tasks(self, order: str, prefer_best_skill: bool) -> None:
        if not self._unassigned_tasks():
            return

        if prefer_best_skill:
            employees = sorted(self.employees, key=lambda item: (-item.skill_level, item.current_workload, item.id))
        else:
            employees = sorted(self.employees, key=lambda item: (item.current_workload, -item.skill_level, item.id))

        for employee in employees:
            task = self._pick_unassigned_task(order=order)
            if task is None:
                break
            self._assign_task(task, employee)

        self._fill_employee_backlog(order=order)

    def _fill_employee_backlog(self, order: str) -> None:
        while True:
            task = self._pick_unassigned_task(order=order)
            if task is None:
                break

            employee = min(
                self.employees,
                key=lambda item: (item.current_workload / max(1, self._target_employee_load(item)), item.current_workload, -item.skill_level),
            )
            if employee.current_workload >= self._target_employee_load(employee):
                break
            self._assign_task(task, employee)

    def _target_employee_load(self, employee: Employee) -> int:
        return max(2, employee.skill_level + 1)

    def _pick_reassignable_task(self, employee_id: int) -> Task | None:
        candidates = [
            task
            for task in self.tasks
            if task.assigned_employee == employee_id and task.status in {"in_progress", "delayed"}
        ]
        if not candidates:
            return None
        candidates.sort(
            key=lambda task: (PRIORITY_SCORES[task.priority], -task.remaining_effort, task.deadline)
        )
        return candidates[0]

    def _unassigned_tasks(self) -> list[Task]:
        return [
            task
            for task in self.tasks
            if task.status in {"pending", "delayed"} and task.assigned_employee is None
        ]

    def _simulate_task_completion(self) -> tuple[int, int, int]:
        completed_count = 0
        early_completed_count = 0
        progress_count = 0

        for employee in self.employees:
            assigned_tasks = [
                task
                for task in self.tasks
                if task.assigned_employee == employee.id and task.status in {"in_progress", "delayed"}
            ]
            assigned_tasks.sort(key=lambda task: (task.deadline, -PRIORITY_SCORES[task.priority], task.id))

            available_effort = employee.skill_level
            for task in assigned_tasks:
                if available_effort <= 0:
                    break

                work_done = min(available_effort, task.remaining_effort)
                if work_done > 0:
                    progress_count += 1
                task.remaining_effort -= work_done
                available_effort -= work_done

                if task.remaining_effort <= 0:
                    task.status = "completed"
                    task.completed_at = self.time_step
                    task.assigned_employee = None
                    completed_count += 1
                    if self.time_step <= task.deadline:
                        early_completed_count += 1

        return completed_count, early_completed_count, progress_count

    def _mark_delayed_tasks(self) -> int:
        new_delays = 0
        for task in self.tasks:
            if task.status == "completed":
                continue
            if self.time_step > task.deadline and task.status != "delayed":
                task.status = "delayed"
                new_delays += 1
        return new_delays

    def _refresh_workloads(self) -> None:
        for employee in self.employees:
            employee.current_workload = sum(
                task.remaining_effort
                for task in self.tasks
                if task.assigned_employee == employee.id and task.status != "completed"
            )

    def _all_tasks_finished(self) -> bool:
        return all(task.status == "completed" for task in self.tasks)

    def _repeated_bad_decision_penalty(self, action: int) -> int:
        if len(self.action_history) < 2:
            return 0
        recent = list(self.action_history)
        same_action_loop = recent[-1] == recent[-2] == action
        delayed_tasks = sum(task.status == "delayed" for task in self.tasks)
        overloaded = sum(employee.current_workload > 6 for employee in self.employees)
        if same_action_loop and (delayed_tasks > 0 or overloaded > 0):
            return 1
        return 0


if __name__ == "__main__":
    env = GovtEnv(mode="medium", seed=42)
    state = env.reset()
    print("Initial state:", state)

    for action in [0, 1, 3, 2]:
        state, reward, done, info = env.step(action)
        print(f"action={action} state={state} reward={reward} done={done} info={info}")
        if done:
            break
