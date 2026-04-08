from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent import GovtAgent
from api_models import (
    ActionModel,
    EmployeeDetailView,
    EmployeeTaskRecord,
    Observation,
    ResetRequest,
    RewardModel,
    RunFullRequest,
    SimulationSnapshot,
    StepRequest,
    StepResult,
)
from baseline import compare_baseline_vs_ai
from env import ACTION_NAMES, MODE_CONFIG, GovtEnv
from grader import evaluate_performance


SKILL_LABELS = {
    1: "Beginner",
    2: "Intermediate",
    3: "Advanced",
    4: "Expert",
    5: "Specialist",
}

EMPLOYEE_NAMES = [
    "Anika Rao",
    "Karan Mehta",
    "Sara Iqbal",
    "Rohan Sen",
    "Priya Sharma",
    "Arjun Patel",
    "Meera Nair",
    "Vikram Verma",
    "Neha Kapoor",
    "Ishaan Joshi",
    "Kavya Roy",
    "Rahul Malhotra",
    "Aditi Das",
    "Nikhil Khanna",
    "Pooja Menon",
    "Dev Arora",
]

STATUS_LABELS = {
    "pending": "Pending",
    "in_progress": "In Progress",
    "completed": "Completed",
    "delayed": "Delayed",
}

PRIORITY_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}

TASK_BLUEPRINTS = [
    (
        "Birth Certificate Verification",
        "Citizen Records",
        "Verify resident documents, validate identity details, and finalize the municipal birth certificate request.",
    ),
    (
        "Property Tax Assessment Review",
        "Revenue",
        "Audit pending tax entries, reconcile arrears, and prepare the updated property assessment sheet.",
    ),
    (
        "Water Connection Approval",
        "Utilities",
        "Review field inspection notes, confirm compliance, and clear the household water connection application.",
    ),
    (
        "Pension Disbursement Reconciliation",
        "Social Welfare",
        "Match beneficiary records with payment logs and release any pension cases held for verification.",
    ),
    (
        "Trade License Renewal Check",
        "Commerce",
        "Inspect submitted renewal documents, confirm fee receipt, and move the business license to issuance.",
    ),
    (
        "Land Mutation File Processing",
        "Land Records",
        "Cross-check ownership paperwork, survey references, and prepare the mutation file for approval.",
    ),
    (
        "Public Grievance Resolution",
        "Citizen Services",
        "Review complaint evidence, coordinate with the department desk, and close the grievance with an action note.",
    ),
    (
        "Building Permit Scrutiny",
        "Urban Planning",
        "Validate drawings, zoning compliance, and safety notes before sending the permit file forward.",
    ),
    (
        "Scholarship Eligibility Audit",
        "Education",
        "Confirm student records, income proofs, and category certificates before scholarship release.",
    ),
    (
        "Road Maintenance Work Order",
        "Public Works",
        "Review field reports, assign repair priority, and issue the maintenance work order to the local team.",
    ),
]


class SimulationService:
    """Stateful service that exposes the govt operations environment in OpenEnv form."""

    def __init__(self) -> None:
        self.agent = GovtAgent()
        self.mode = "medium"
        self.task_type = "medium"
        self.seed = 42
        self.env = GovtEnv(mode=self.mode, seed=self.seed)
        self.logs: list[str] = []
        self.chart_data: list[dict[str, Any]] = []
        self.last_reward_value = 0.0
        self.last_reward_reason = "Waiting for the first step."
        self.last_reward_breakdown: dict[str, Any] = {
            "completion": 0,
            "early_completion": 0,
            "progress": 0,
            "idle": 0,
            "delay": 0,
            "repeated_bad_decision": 0,
            "reason": "Waiting for the first step.",
            "total": 0,
        }
        self.total_reward = 0.0
        self.last_action = "Awaiting simulation start"
        self.last_action_id: int | None = None
        self.last_action_name = "awaiting_start"
        self.last_action_reason = "The AI will explain its routing decision after the first step."
        self.done = False
        self.comparison_cache: dict[str, dict[str, Any]] = {}

    def reset(self, mode: str) -> dict[str, Any]:
        self.mode = mode
        self.task_type = mode
        self.env = GovtEnv(mode=mode, seed=self.seed)
        state = self.env.reset()
        self.logs = [
            f"Simulation started for the {mode.title()} task",
            "Government office environment initialized",
            "AI agent ready for task routing",
        ]
        self.chart_data = [{"tick": "00", "tasks": 0}]
        self.last_reward_value = 0.0
        self.last_reward_reason = "Environment reset."
        self.last_reward_breakdown = {
            "completion": 0,
            "early_completion": 0,
            "progress": 0,
            "idle": 0,
            "delay": 0,
            "repeated_bad_decision": 0,
            "reason": "Environment reset.",
            "total": 0,
        }
        self.total_reward = 0.0
        self.last_action = "Environment reset"
        self.last_action_id = None
        self.last_action_name = "environment_reset"
        self.last_action_reason = "Waiting for the first AI decision."
        self.done = False
        return self.snapshot(state=state)

    def state(self) -> Observation:
        return self._observation_from_vector(self.env.state())

    def step(self, action_id: int | None = None) -> StepResult:
        current_state = self.env.state()
        chosen_action = self.agent.select_action(current_state) if action_id is None else action_id
        next_state, reward, done, info = self.env.step(chosen_action)

        self.last_reward_value = reward
        self.last_reward_breakdown = info["reward_breakdown"]
        self.last_reward_reason = str(info["reward_breakdown"]["reason"])
        self.total_reward += reward
        self.done = done
        self.last_action_id = chosen_action
        self.last_action_name = ACTION_NAMES[chosen_action]
        self.last_action = self.last_action_name.replace("_", " ").title()
        self.last_action_reason = self.agent.explain_action(chosen_action)

        debug_log = (
            f"Step {info['time_step']}: {self.last_action} | reward={reward:.1f} | "
            f"{self.last_action_reason}"
        )
        self.logs = [debug_log, *self.logs][:12]
        self.chart_data.append({"tick": f"{info['time_step']:02d}", "tasks": self._completed_tasks()})
        self.chart_data = self.chart_data[-12:]

        metrics = self.metrics()
        return StepResult(
            observation=self._observation_from_vector(next_state),
            reward=RewardModel(value=reward, reason=self.last_reward_reason),
            action=ActionModel(action_id=chosen_action, action_name=self.last_action_name),
            done=done,
            info={
                **info,
                "action": ActionModel(action_id=chosen_action, action_name=self.last_action_name).model_dump(),
                "grader": metrics["grader"],
            },
            metrics=metrics,
            task_type=self.task_type,
        )

    def metrics(self) -> dict[str, Any]:
        metrics = self.env.get_metrics()
        score, label = evaluate_performance(metrics, task_type=self.task_type)
        return {
            **metrics,
            "reward": round(self.total_reward, 2),
            "efficiency": round(score * 100, 2),
            "grader": {"score": score, "label": label},
            "task_type": self.task_type,
        }

    def comparison(self) -> dict[str, Any]:
        comparison = self._get_comparison(self.mode)
        baseline = comparison["baseline"]
        ai = comparison["ai"]
        return {
            **comparison,
            "chart": [
                {
                    "name": "Baseline",
                    "efficiency": baseline["efficiency"],
                    "delays": baseline["delayed_tasks"],
                },
                {
                    "name": "AI",
                    "efficiency": ai["efficiency"],
                    "delays": ai["delayed_tasks"],
                },
            ],
        }

    def run_full(self, mode: str, max_steps: int) -> dict[str, Any]:
        self.reset(mode)
        while not self.done and self.env.time_step < max_steps:
            self.step()
        return self.snapshot(comparison=self.comparison())

    def snapshot(self, state: list[float] | None = None, comparison: dict[str, Any] | None = None) -> dict[str, Any]:
        vector = state or self.env.state()
        observation = self._observation_from_vector(vector)
        metrics = self.metrics()
        grader = metrics["grader"]
        overloaded_employees = sum(employee["status"] == "overloaded" for employee in self._serialize_employees())
        environment_state = self.env.get_environment_state()

        payload = SimulationSnapshot(
            mode=self.mode,
            task_type=self.task_type,
            initialized=True,
            done=self.done,
            step=self.env.time_step,
            observation=observation,
            reward=RewardModel(value=self.last_reward_value, reason=self.last_reward_reason),
            action=ActionModel(action_id=self.last_action_id, action_name=self.last_action_name),
            grader=grader,
            info={
                "objective": metrics["objective"],
                "reward_breakdown": self.last_reward_breakdown,
                "last_action_reason": self.last_action_reason,
            },
            state=environment_state.to_dict(),
            metrics=metrics,
            employees=self._serialize_employees(),
            employeeDetails=self._serialize_employee_details(),
            tasks=self._serialize_tasks(),
            logs=list(self.logs),
            chartData=list(self.chart_data),
            comparison=comparison,
            totalReward=round(self.total_reward, 2),
            efficiencyGain=max(0.0, round(metrics["efficiency"] - 56, 2)),
            penalties=metrics["delayed_tasks"] + overloaded_employees,
            lastAction=self.last_action,
            currentState=vector,
            tasksCompleted=metrics["completed_tasks"],
            pendingTasks=observation.pending_tasks,
            delayedTasks=metrics["delayed_tasks"],
            efficiencyScore=metrics["efficiency"],
            graderScore=grader["score"],
            graderLabel=grader["label"],
            reward_data={
                "current": self.last_reward_value,
                "total": round(self.total_reward, 2),
                "breakdown": self.last_reward_breakdown,
            },
        )
        return payload.model_dump()

    def _observation_from_vector(self, vector: list[float]) -> Observation:
        return Observation(
            pending_tasks=int(vector[0]),
            delayed_tasks=int(vector[1]),
            high_priority_tasks=int(vector[2]),
            avg_workload=round(float(vector[3]), 2),
            idle_employees=int(vector[4]),
        )

    def _completed_tasks(self) -> int:
        return sum(task.status == "completed" for task in self.env.tasks)

    def _serialize_employees(self) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for index, employee in enumerate(self.env.employees):
            workload = min(100, employee.current_workload * 20)
            if workload == 0:
                status = "idle"
            elif workload > 75:
                status = "overloaded"
            else:
                status = "busy"

            owned_tasks = [
                task
                for task in self.env.tasks
                if task.last_assigned_employee == employee.id or task.assigned_employee == employee.id
            ]
            current_tasks = [
                f"T-{100 + task.id}"
                for task in owned_tasks
                if task.assigned_employee == employee.id and task.status != "completed"
            ]
            completed_count = sum(
                task.status == "completed" and task.last_assigned_employee == employee.id
                for task in owned_tasks
            )
            delayed_count = sum(
                task.status == "delayed" and task.last_assigned_employee == employee.id
                for task in owned_tasks
            )
            efficiency = completed_count / max(1, len(owned_tasks))

            payload.append(
                {
                    "id": employee.id,
                    "name": EMPLOYEE_NAMES[index % len(EMPLOYEE_NAMES)],
                    "skill": SKILL_LABELS.get(employee.skill_level, f"Level {employee.skill_level}"),
                    "skillLevel": employee.skill_level,
                    "workload": workload,
                    "status": status,
                    "currentTasks": current_tasks,
                    "completedTasks": completed_count,
                    "delayedTasks": delayed_count,
                    "efficiency": round(efficiency, 2),
                }
            )
        return payload

    def _serialize_tasks(self) -> list[dict[str, Any]]:
        employees = {employee["id"]: employee["name"] for employee in self._serialize_employees()}
        payload: list[dict[str, Any]] = []
        for task in self.env.tasks:
            task_meta = self._task_metadata(task.id, task.priority)
            payload.append(
                {
                    "id": f"T-{100 + task.id}",
                    "title": task_meta["title"],
                    "department": task_meta["department"],
                    "description": task_meta["description"],
                    "assignedEmployeeId": task.assigned_employee,
                    "priority": PRIORITY_LABELS.get(task.priority, task.priority.title()),
                    "employee": employees.get(task.assigned_employee, "Unassigned"),
                    "deadline": f"T+{task.deadline}",
                    "status": STATUS_LABELS.get(task.status, task.status.title()),
                    "remainingEffort": task.remaining_effort,
                    "completionTime": task.completed_at,
                    "ownerEmployeeId": task.last_assigned_employee,
                }
            )
        return payload

    def _serialize_employee_details(self) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        employee_views = {item["id"]: item for item in self._serialize_employees()}

        for employee in self.env.employees:
            view = employee_views[employee.id]
            related_tasks = [
                task
                for task in self.env.tasks
                if task.last_assigned_employee == employee.id or task.assigned_employee == employee.id
            ]

            def to_record(task: Any) -> EmployeeTaskRecord:
                task_meta = self._task_metadata(task.id, task.priority)
                return EmployeeTaskRecord(
                    taskId=f"T-{100 + task.id}",
                    title=task_meta["title"],
                    department=task_meta["department"],
                    description=task_meta["description"],
                    priority=PRIORITY_LABELS.get(task.priority, task.priority.title()),
                    status=STATUS_LABELS.get(task.status, task.status.title()),
                    deadline=f"T+{task.deadline}",
                    completionTime=task.completed_at,
                )

            active_tasks = [
                to_record(task)
                for task in related_tasks
                if task.assigned_employee == employee.id and task.status != "completed"
            ]
            completed_history = [
                to_record(task)
                for task in related_tasks
                if task.status == "completed" and task.last_assigned_employee == employee.id
            ]
            delayed_tasks = [
                to_record(task)
                for task in related_tasks
                if task.status == "delayed" and task.last_assigned_employee == employee.id
            ]
            completed_on_time = sum(
                task.completed_at is not None and task.completed_at <= task.deadline
                for task in related_tasks
                if task.status == "completed" and task.last_assigned_employee == employee.id
            )
            completed_total = max(1, len(completed_history))

            detail = EmployeeDetailView(
                id=employee.id,
                name=view["name"],
                skill=view["skill"],
                skillLevel=employee.skill_level,
                currentWorkload=view["workload"],
                status=view["status"],
                activeTasks=active_tasks,
                completedHistory=completed_history,
                delayedTasks=delayed_tasks,
                efficiencyStats={
                    "active_tasks": len(active_tasks),
                    "completed_tasks": len(completed_history),
                    "delayed_tasks": len(delayed_tasks),
                    "on_time_rate": round(completed_on_time / completed_total, 2),
                    "efficiency_score": view["efficiency"],
                },
            )
            details.append(detail.model_dump())

        return details

    def _task_metadata(self, task_id: int, priority: str) -> dict[str, str]:
        title, department, description = TASK_BLUEPRINTS[(task_id - 1) % len(TASK_BLUEPRINTS)]
        priority_note = {
            "low": "Routine file with standard service-level handling.",
            "medium": "Important file that should move without queue build-up.",
            "high": "Urgent public-service case requiring fast turnaround.",
        }.get(priority, "Government office workflow item.")
        return {
            "title": title,
            "department": department,
            "description": f"{description} {priority_note}",
        }

    def _get_comparison(self, mode: str) -> dict[str, Any]:
        if mode not in self.comparison_cache:
            self.comparison_cache[mode] = compare_baseline_vs_ai(
                mode=mode,
                max_steps=MODE_CONFIG[mode]["max_steps"],
                seed=self.seed,
            )
        return self.comparison_cache[mode]


app = FastAPI(title="GovtAI Ops API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = SimulationService()
DIST_DIR = Path(__file__).resolve().parent / "dist"


@app.post("/reset", response_model=SimulationSnapshot)
@app.post("/api/reset", response_model=SimulationSnapshot)
def reset_simulation(request: ResetRequest) -> dict[str, Any]:
    try:
        return service.reset(request.resolved_task_type())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reset failed: {exc}") from exc


@app.post("/step", response_model=SimulationSnapshot)
@app.post("/api/step", response_model=SimulationSnapshot)
def run_step(request: StepRequest | None = None) -> dict[str, Any]:
    try:
        service.step(action_id=request.action_id if request else None)
        return service.snapshot()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Step failed: {exc}") from exc


@app.get("/state", response_model=Observation)
@app.get("/api/state", response_model=Observation)
def get_state() -> Observation:
    try:
        return service.state()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"State failed: {exc}") from exc


@app.get("/metrics")
@app.get("/api/metrics")
def get_metrics() -> dict[str, Any]:
    try:
        return service.metrics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Metrics failed: {exc}") from exc


@app.get("/comparison")
@app.get("/api/comparison")
def get_comparison() -> dict[str, Any]:
    try:
        return service.comparison()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {exc}") from exc


@app.post("/run-full", response_model=SimulationSnapshot)
@app.post("/api/run-full", response_model=SimulationSnapshot)
def run_full_simulation(request: RunFullRequest) -> dict[str, Any]:
    try:
        return service.run_full(mode=request.resolved_task_type(), max_steps=request.max_steps)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Run full simulation failed: {exc}") from exc


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str) -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = DIST_DIR / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
