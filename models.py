from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Task:
    id: int
    priority: str
    deadline: int
    created_at: int = 0
    status: str = "pending"
    assigned_employee: int | None = None
    last_assigned_employee: int | None = None
    remaining_effort: int = 1
    completed_at: int | None = None

    def to_dict(self) -> dict[str, int | str | None]:
        return asdict(self)


@dataclass(slots=True)
class Employee:
    id: int
    skill_level: int
    current_workload: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(slots=True)
class EnvironmentState:
    task_type: str
    time_step: int
    pending_tasks: int
    delayed_tasks: int
    high_priority_tasks: int
    average_workload: float
    idle_employees: int
    completed_tasks: int
    total_tasks: int

    def vector(self) -> list[float]:
        return [
            float(self.pending_tasks),
            float(self.delayed_tasks),
            float(self.high_priority_tasks),
            round(float(self.average_workload), 2),
            float(self.idle_employees),
        ]

    def to_dict(self) -> dict[str, float | int | str | list[float]]:
        payload = asdict(self)
        payload["vector"] = self.vector()
        return payload
