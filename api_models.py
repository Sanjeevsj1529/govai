from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


TaskMode = Literal["easy", "medium", "hard"]


class Observation(BaseModel):
    pending_tasks: int = Field(ge=0)
    delayed_tasks: int = Field(ge=0)
    high_priority_tasks: int = Field(ge=0)
    avg_workload: float = Field(ge=0)
    idle_employees: int = Field(ge=0)


class ActionModel(BaseModel):
    action_id: int | None = Field(default=None, ge=0, le=3)
    action_name: str


class RewardModel(BaseModel):
    value: float
    reason: str


class GraderResult(BaseModel):
    score: float = Field(ge=0, le=1)
    label: str


class EmployeeView(BaseModel):
    id: int
    name: str
    skill: str
    skillLevel: int
    workload: int
    status: str
    currentTasks: list[str] = []
    completedTasks: int = 0
    delayedTasks: int = 0
    efficiency: float = Field(ge=0, le=1)


class TaskView(BaseModel):
    id: str
    title: str = ""
    department: str = ""
    description: str = ""
    assignedEmployeeId: int | None = None
    priority: str
    employee: str
    deadline: str
    status: str
    remainingEffort: int
    completionTime: int | None = None
    ownerEmployeeId: int | None = None


class EmployeeTaskRecord(BaseModel):
    taskId: str
    title: str = ""
    department: str = ""
    description: str = ""
    priority: str
    status: str
    deadline: str = ""
    completionTime: int | None = None


class EmployeeDetailView(BaseModel):
    id: int
    name: str
    skill: str
    skillLevel: int
    currentWorkload: int
    status: str
    activeTasks: list[EmployeeTaskRecord]
    completedHistory: list[EmployeeTaskRecord]
    delayedTasks: list[EmployeeTaskRecord]
    efficiencyStats: dict[str, float | int]


class StepResult(BaseModel):
    observation: Observation
    reward: RewardModel
    action: ActionModel | None = None
    done: bool
    info: dict[str, Any]
    metrics: dict[str, Any] | None = None
    task_type: TaskMode = "medium"


class SimulationSnapshot(BaseModel):
    mode: TaskMode
    task_type: TaskMode
    initialized: bool
    done: bool
    step: int
    observation: Observation
    reward: RewardModel
    action: ActionModel
    grader: GraderResult
    info: dict[str, Any]
    state: dict[str, Any]
    metrics: dict[str, Any]
    employees: list[EmployeeView]
    employeeDetails: list[EmployeeDetailView] = []
    tasks: list[TaskView]
    logs: list[str]
    chartData: list[dict[str, Any]]
    comparison: dict[str, Any] | None = None
    totalReward: float = 0
    efficiencyGain: float = 0
    penalties: int = 0
    lastAction: str = ""
    currentState: list[float]
    tasksCompleted: int = 0
    pendingTasks: int = 0
    delayedTasks: int = 0
    efficiencyScore: float = 0
    graderScore: float = Field(ge=0, le=1)
    graderLabel: str
    reward_data: dict[str, Any]


class ResetRequest(BaseModel):
    mode: TaskMode = "medium"
    task_type: TaskMode | None = None

    def resolved_task_type(self) -> TaskMode:
        return self.task_type or self.mode


class RunFullRequest(BaseModel):
    mode: TaskMode = "medium"
    task_type: TaskMode | None = None
    max_steps: int = Field(default=50, ge=1, le=500)

    def resolved_task_type(self) -> TaskMode:
        return self.task_type or self.mode


class StepRequest(BaseModel):
    action_id: int | None = Field(default=None, ge=0, le=3)
