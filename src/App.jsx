import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Bot,
  Gauge,
  Moon,
  Pause,
  Play,
  RefreshCcw,
  StepForward,
  Sun,
  Users,
  X,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import GlassPanel from "./components/GlassPanel";
import MetricCard from "./components/MetricCard";
import StatusBadge from "./components/StatusBadge";

function buildApiBases() {
  if (typeof window === "undefined") {
    return ["/api", ""];
  }

  const configuredBase = window.localStorage.getItem("govtai-api-base")?.trim();
  const { protocol, hostname, origin } = window.location;
  const candidates = [
    configuredBase,
    "/api",
    "",
    `${origin}/api`,
    origin,
  ];

  if (hostname === "localhost" || hostname === "127.0.0.1") {
    candidates.push("http://127.0.0.1:8000", "http://localhost:8000");
  } else {
    candidates.push(`${protocol}//${hostname}:8000`);
  }

  return [...new Set(candidates.filter(Boolean))];
}
const initialLogs = [
  "AI routing queue initialized.",
  "OpenEnv state vector ready.",
  "Awaiting first operational decision.",
];

const taskProfiles = {
  easy: { label: "Easy", objective: "Maximize completion under light civic-service load." },
  medium: { label: "Medium", objective: "Reduce delays while balancing department workloads." },
  hard: { label: "Hard", objective: "Handle dynamic overload and prioritize urgent work." },
};

const localEmployeeNames = [
  "Anika Rao", "Karan Mehta", "Sara Iqbal", "Rohan Sen", "Priya Sharma", "Arjun Patel",
  "Meera Nair", "Vikram Verma", "Neha Kapoor", "Ishaan Joshi", "Kavya Roy", "Rahul Malhotra",
];

const localTaskBlueprints = [
  {
    title: "Birth Certificate Verification",
    department: "Citizen Records",
    description: "Verify resident documents, validate identity details, and finalize the municipal birth certificate request.",
  },
  {
    title: "Property Tax Assessment Review",
    department: "Revenue",
    description: "Audit pending tax entries, reconcile arrears, and prepare the updated property assessment sheet.",
  },
  {
    title: "Water Connection Approval",
    department: "Utilities",
    description: "Review field inspection notes, confirm compliance, and clear the household water connection application.",
  },
  {
    title: "Pension Disbursement Reconciliation",
    department: "Social Welfare",
    description: "Match beneficiary records with payment logs and release any pension cases held for verification.",
  },
  {
    title: "Trade License Renewal Check",
    department: "Commerce",
    description: "Inspect submitted renewal documents, confirm fee receipt, and move the business license to issuance.",
  },
  {
    title: "Land Mutation File Processing",
    department: "Land Records",
    description: "Cross-check ownership paperwork, survey references, and prepare the mutation file for approval.",
  },
  {
    title: "Public Grievance Resolution",
    department: "Citizen Services",
    description: "Review complaint evidence, coordinate with the department desk, and close the grievance with an action note.",
  },
  {
    title: "Building Permit Scrutiny",
    department: "Urban Planning",
    description: "Validate drawings, zoning compliance, and safety notes before sending the permit file forward.",
  },
  {
    title: "Scholarship Eligibility Audit",
    department: "Education",
    description: "Confirm student records, income proofs, and category certificates before scholarship release.",
  },
  {
    title: "Road Maintenance Work Order",
    department: "Public Works",
    description: "Review field reports, assign repair priority, and issue the maintenance work order to the local team.",
  },
];

const localConfig = {
  easy: { employees: 3, tasks: 6, maxSteps: 15, incoming: [0, 0] },
  medium: { employees: 5, tasks: 10, maxSteps: 20, incoming: [0, 1] },
  hard: { employees: 8, tasks: 16, maxSteps: 30, incoming: [1, 2] },
};

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function labelForScore(score) {
  if (score < 0.4) return "Poor";
  if (score <= 0.6) return "Average";
  if (score <= 0.8) return "Good";
  return "Optimal";
}

function localTaskMetadata(index, priority) {
  const base = localTaskBlueprints[index % localTaskBlueprints.length];
  const priorityNote = priority === "High"
    ? "Urgent public-service case requiring fast turnaround."
    : priority === "Medium"
      ? "Important file that should move without queue build-up."
      : "Routine file with standard service-level handling.";
  return {
    title: base.title,
    department: base.department,
    description: `${base.description} ${priorityNote}`,
  };
}

function createLocalEnvironment(mode) {
  const config = localConfig[mode] ?? localConfig.medium;
  const employees = Array.from({ length: config.employees }, (_, index) => {
    const skillLevel = randInt(1, 5);
    return {
      id: index + 1,
      name: localEmployeeNames[index % localEmployeeNames.length],
      skill: ["Beginner", "Intermediate", "Advanced", "Expert", "Specialist"][skillLevel - 1],
      skillLevel,
      workload: 0,
      status: "idle",
      currentTasks: [],
      completedTasks: 0,
      delayedTasks: 0,
      efficiency: 0,
    };
  });

  const priorities = ["Low", "Medium", "High"];
  const tasks = Array.from({ length: config.tasks }, (_, index) => {
    const priority = priorities[randInt(0, 2)];
    const metadata = localTaskMetadata(index, priority);
    return {
      id: `T-${101 + index}`,
      title: metadata.title,
      department: metadata.department,
      description: metadata.description,
      assignedEmployeeId: null,
      priority,
      employee: "Unassigned",
      deadline: `T+${priority === "High" ? 3 : priority === "Medium" ? 5 : 7}`,
      deadlineStep: priority === "High" ? 3 : priority === "Medium" ? 5 : 7,
      status: "Pending",
      remainingEffort: priority === "High" ? randInt(3, 5) : priority === "Medium" ? randInt(2, 4) : randInt(1, 3),
      completionTime: null,
      ownerEmployeeId: null,
    };
  });

  return { mode, config, employees, tasks, timeStep: 0, nextTaskId: 101 + config.tasks };
}

function localObserve(env) {
  const pending = env.tasks.filter((task) => task.status === "Pending" || task.status === "In Progress").length;
  const delayed = env.tasks.filter((task) => task.status === "Delayed").length;
  const high = env.tasks.filter((task) => task.priority === "High" && task.status !== "Completed").length;
  const avgWorkload = env.employees.length
    ? env.employees.reduce((sum, employee) => sum + employee.workload, 0) / env.employees.length / 20
    : 0;
  const idle = env.employees.filter((employee) => employee.workload === 0).length;
  return {
    pending_tasks: pending,
    delayed_tasks: delayed,
    high_priority_tasks: high,
    avg_workload: Number(avgWorkload.toFixed(2)),
    idle_employees: idle,
  };
}

function localRefreshEmployees(env) {
  env.employees.forEach((employee) => {
    const assigned = env.tasks.filter((task) => task.assignedEmployeeId === employee.id && task.status !== "Completed");
    const load = assigned.reduce((sum, task) => sum + task.remainingEffort, 0);
    employee.workload = clamp(load * 20, 0, 100);
    employee.currentTasks = assigned.map((task) => task.id);
    employee.completedTasks = env.tasks.filter((task) => task.ownerEmployeeId === employee.id && task.status === "Completed").length;
    employee.delayedTasks = env.tasks.filter((task) => task.ownerEmployeeId === employee.id && task.status === "Delayed").length;
    const owned = env.tasks.filter((task) => task.ownerEmployeeId === employee.id);
    employee.efficiency = Number((employee.completedTasks / Math.max(1, owned.length)).toFixed(2));
    employee.status = employee.workload === 0 ? "idle" : employee.workload > 75 ? "overloaded" : "busy";
  });
}

function localPickAction(observation) {
  if (observation.delayed_tasks > 0) return { action_id: 2, action_name: "reassign" };
  if (observation.high_priority_tasks > 0) return { action_id: 3, action_name: "prioritize_urgent" };
  if (observation.idle_employees > 0) return { action_id: 1, action_name: "assign_least_busy" };
  return { action_id: 0, action_name: "assign_best" };
}

function localTargetLoad(employee) {
  return Math.max(40, (employee.skillLevel + 1) * 20);
}

function localPickPendingTask(env, order = "priority") {
  const pending = env.tasks.filter((task) => (task.status === "Pending" || task.status === "Delayed") && task.assignedEmployeeId == null);
  if (!pending.length) return null;

  const sortByPriority = [...pending].sort((a, b) => (b.priority === "High") - (a.priority === "High") || a.deadlineStep - b.deadlineStep);
  const sortByDeadline = [...pending].sort((a, b) => a.deadlineStep - b.deadlineStep);
  return order === "deadline" ? sortByDeadline[0] : sortByPriority[0];
}

function localAssignTask(task, employee) {
  if (!task || !employee) return;
  task.assignedEmployeeId = employee.id;
  task.ownerEmployeeId = employee.id;
  task.employee = employee.name;
  task.status = "In Progress";
}

function localFillBacklog(env, order = "priority") {
  while (true) {
    localRefreshEmployees(env);
    const candidate = localPickPendingTask(env, order);
    if (!candidate) return;

    const target = [...env.employees].sort(
      (a, b) => a.workload / localTargetLoad(a) - b.workload / localTargetLoad(b) || a.workload - b.workload || b.skillLevel - a.skillLevel,
    )[0];

    if (!target || target.workload >= localTargetLoad(target)) return;
    localAssignTask(candidate, target);
  }
}

function localAssign(env, actionId) {
  localRefreshEmployees(env);
  const order = actionId === 1 ? "deadline" : "priority";
  const employees = [...env.employees].sort(
    actionId === 0
      ? (a, b) => b.skillLevel - a.skillLevel || a.workload - b.workload
      : (a, b) => a.workload - b.workload || b.skillLevel - a.skillLevel,
  );

  employees.forEach((employee) => {
    const candidate = localPickPendingTask(env, order);
    if (candidate) localAssignTask(candidate, employee);
  });

  localFillBacklog(env, order);
  localRefreshEmployees(env);
}

function localReassign(env) {
  const overloaded = env.employees.filter((employee) => employee.workload > 75);
  const targets = [...env.employees].sort((a, b) => a.workload - b.workload || b.skillLevel - a.skillLevel);
  overloaded.forEach((employee) => {
    const task = env.tasks.find((item) => item.assignedEmployeeId === employee.id && item.status !== "Completed");
    const target = targets.find((item) => item.id !== employee.id);
    if (task && target) {
      task.assignedEmployeeId = target.id;
      task.ownerEmployeeId = target.id;
      task.employee = target.name;
      task.status = "In Progress";
    }
  });
}

function localPrioritize(env) {
  const urgent = env.tasks
    .filter((task) => (task.status === "Pending" || task.status === "Delayed") && task.assignedEmployeeId == null)
    .sort((a, b) => a.deadlineStep - b.deadlineStep || (b.priority === "High") - (a.priority === "High"))
    .slice(0, Math.max(2, env.employees.length));
  urgent.forEach((task) => {
    localRefreshEmployees(env);
    const target = [...env.employees].sort((a, b) => a.workload - b.workload || b.skillLevel - a.skillLevel)[0];
    localAssignTask(task, target);
  });
  localFillBacklog(env, "deadline");
  localRefreshEmployees(env);
}

function localDoWork(env) {
  let completed = 0;
  let early = 0;
  let progress = 0;
  env.employees.forEach((employee) => {
    let capacity = employee.skillLevel;
    const active = env.tasks
      .filter((task) => task.assignedEmployeeId === employee.id && (task.status === "In Progress" || task.status === "Delayed"))
      .sort((a, b) => a.deadlineStep - b.deadlineStep);
    active.forEach((task) => {
      if (capacity <= 0) return;
      const worked = Math.min(capacity, task.remainingEffort);
      if (worked > 0) progress += 1;
      task.remainingEffort -= worked;
      capacity -= worked;
      if (task.remainingEffort <= 0) {
        task.remainingEffort = 0;
        task.status = "Completed";
        task.assignedEmployeeId = null;
        task.employee = "Completed";
        task.completionTime = env.timeStep;
        completed += 1;
        if (env.timeStep <= task.deadlineStep) early += 1;
      }
    });
  });
  return { completed, early, progress };
}

function localInjectTasks(env) {
  const [minIncoming, maxIncoming] = env.config.incoming;
  const count = randInt(minIncoming, maxIncoming);
  for (let index = 0; index < count; index += 1) {
    const idNumber = env.nextTaskId++;
    const priority = ["Low", "Medium", "High"][randInt(0, 2)];
    const metadata = localTaskMetadata(idNumber - 101, priority);
    env.tasks.push({
      id: `T-${idNumber}`,
      title: metadata.title,
      department: metadata.department,
      description: metadata.description,
      assignedEmployeeId: null,
      priority,
      employee: "Unassigned",
      deadline: `T+${env.timeStep + (priority === "High" ? 3 : priority === "Medium" ? 5 : 7)}`,
      deadlineStep: env.timeStep + (priority === "High" ? 3 : priority === "Medium" ? 5 : 7),
      status: "Pending",
      remainingEffort: priority === "High" ? randInt(3, 5) : priority === "Medium" ? randInt(2, 4) : randInt(1, 3),
      completionTime: null,
      ownerEmployeeId: null,
    });
  }
}

function localMetrics(env) {
  const total = Math.max(1, env.tasks.length);
  const completed = env.tasks.filter((task) => task.status === "Completed").length;
  const delayed = env.tasks.filter((task) => task.status === "Delayed").length;
  const avg = env.employees.length ? env.employees.reduce((sum, item) => sum + item.workload, 0) / env.employees.length / 20 : 0;
  const workloadBalance = env.employees.length
    ? 1 / (1 + env.employees.reduce((sum, item) => sum + Math.abs(item.workload / 20 - avg), 0) / env.employees.length)
    : 1;
  const score = clamp(0.5 * (completed / total) + 0.3 * (1 - delayed / total) + 0.2 * workloadBalance, 0, 1);
  return {
    task_type: env.mode,
    total_tasks: env.tasks.length,
    completed_tasks: completed,
    delayed_tasks: delayed,
    avg_workload: Number(avg.toFixed(2)),
    completion_rate: Number((completed / total).toFixed(4)),
    delay_ratio: Number((delayed / total).toFixed(4)),
    workload_balance: Number(workloadBalance.toFixed(4)),
    objective: taskProfiles[env.mode].objective,
    reward: 0,
    efficiency: Number((score * 100).toFixed(2)),
    grader: { score: Number(score.toFixed(4)), label: labelForScore(score) },
  };
}

function localEmployeeDetails(env) {
  return env.employees.map((employee) => ({
    id: employee.id,
    name: employee.name,
    skill: employee.skill,
    skillLevel: employee.skillLevel,
    currentWorkload: employee.workload,
    status: employee.status,
    activeTasks: env.tasks.filter((task) => task.assignedEmployeeId === employee.id && task.status !== "Completed").map((task) => ({
      taskId: task.id,
      title: task.title,
      department: task.department,
      description: task.description,
      priority: task.priority,
      status: task.status,
      deadline: task.deadline,
      completionTime: task.completionTime,
    })),
    completedHistory: env.tasks.filter((task) => task.ownerEmployeeId === employee.id && task.status === "Completed").map((task) => ({
      taskId: task.id,
      title: task.title,
      department: task.department,
      description: task.description,
      priority: task.priority,
      status: task.status,
      deadline: task.deadline,
      completionTime: task.completionTime,
    })),
    delayedTasks: env.tasks.filter((task) => task.ownerEmployeeId === employee.id && task.status === "Delayed").map((task) => ({
      taskId: task.id,
      title: task.title,
      department: task.department,
      description: task.description,
      priority: task.priority,
      status: task.status,
      deadline: task.deadline,
      completionTime: task.completionTime,
    })),
    efficiencyStats: {
      active_tasks: employee.currentTasks.length,
      completed_tasks: employee.completedTasks,
      delayed_tasks: employee.delayedTasks,
      on_time_rate: employee.efficiency,
      efficiency_score: employee.efficiency,
    },
  }));
}

function localSnapshot(env, reward = 0, rewardReason = "Environment reset.", action = { action_id: null, action_name: "environment_reset" }, comparison = null) {
  localRefreshEmployees(env);
  const observation = localObserve(env);
  const metrics = localMetrics(env);
  metrics.reward = reward;
  return {
    mode: env.mode,
    task_type: env.mode,
    initialized: true,
    done: env.timeStep >= env.config.maxSteps || env.tasks.every((task) => task.status === "Completed"),
    step: env.timeStep,
    observation,
    reward: { value: reward, reason: rewardReason },
    action,
    info: { objective: metrics.objective, last_action_reason: "Local fallback simulation is active." },
    metrics,
    grader: metrics.grader,
    logs: [
      `Step ${env.timeStep}: ${action.action_name}`,
      ...initialLogs,
    ].slice(0, 10),
    chartData: [{ tick: "00", tasks: 0 }, ...Array.from({ length: env.timeStep }, (_, index) => ({
      tick: String(index + 1).padStart(2, "0"),
      tasks: env.tasks.filter((task) => task.status === "Completed" && (task.completionTime ?? 0) <= index + 1).length,
    }))].slice(-12),
    employees: env.employees,
    employeeDetails: localEmployeeDetails(env),
    tasks: env.tasks,
    comparison,
    currentState: [
      observation.pending_tasks,
      observation.delayed_tasks,
      observation.high_priority_tasks,
      observation.avg_workload,
      observation.idle_employees,
    ],
  };
}

function localReset(mode, shouldRun = false) {
  const env = createLocalEnvironment(mode);
  const snapshot = localSnapshot(env, 0, "Local fallback initialized.");
  return { env, snapshot: { ...snapshot, running: shouldRun, apiError: "Backend unreachable. Running local fallback." } };
}

function localStep(env) {
  const observation = localObserve(env);
  const action = localPickAction(observation);
  if (action.action_id === 2) localReassign(env);
  else if (action.action_id === 3) localPrioritize(env);
  else localAssign(env, action.action_id);
  const progress = localDoWork(env);
  env.timeStep += 1;
  localInjectTasks(env);
  let delays = 0;
  env.tasks.forEach((task) => {
    if (task.status !== "Completed" && env.timeStep > task.deadlineStep && task.status !== "Delayed") {
      task.status = "Delayed";
      delays += 1;
    }
  });
  localRefreshEmployees(env);
  const idle = env.employees.filter((employee) => employee.workload === 0).length;
  const reward = progress.completed * 10 + progress.early * 5 + progress.progress - idle * 5 - delays * 10;
  return localSnapshot(env, reward, "Local fallback step executed.", action);
}

function createInitialState(mode = "medium") {
  return {
    mode,
    taskType: mode,
    initialized: false,
    running: false,
    done: false,
    step: 0,
    observation: null,
    currentState: [0, 0, 0, 0, 0],
    reward: 0,
    rewardReason: "Waiting for the first step.",
    rewardBreakdown: null,
    action: null,
    actionDescription: "The AI will explain its routing choice after the first step.",
    metrics: null,
    graderScore: 0,
    graderLabel: "Poor",
    logs: initialLogs,
    chartData: [{ tick: "00", tasks: 0 }],
    comparisonSummary: null,
    comparisonData: [],
    employees: [],
    employeeDetails: [],
    tasks: [],
    apiError: null,
  };
}

function getChartTheme(theme) {
  const light = theme === "light";
  return {
    axis: light ? "#526073" : "#9aa6b2",
    grid: light ? "#d8dee7" : "#2c3642",
    tooltipBackground: light ? "#ffffff" : "#151b22",
    tooltipBorder: light ? "1px solid #d8dee7" : "1px solid #2c3642",
    tooltipLabel: light ? "#0f1720" : "#f3f6f8",
    tooltipText: light ? "#334155" : "#d7dde3",
    accent: light ? "#1d4ed8" : "#7dd3fc",
    good: "#15803d",
    warn: "#b45309",
    bad: "#b91c1c",
  };
}

function formatVector(values) {
  return `[${values.map((value) => Number(value).toFixed(2)).join(", ")}]`;
}

function formatPercent(value) {
  return `${Math.round((value ?? 0) * 100)}%`;
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeSnapshot(snapshot) {
  const observation = snapshot.observation ?? null;
  const rewardValue = typeof snapshot.reward === "object" ? snapshot.reward?.value ?? 0 : snapshot.reward ?? 0;
  const rewardReason =
    typeof snapshot.reward === "object"
      ? snapshot.reward?.reason ?? "No reward reason available."
      : "No reward reason available.";
  const chartData = safeArray(snapshot.chartData);

  return {
    mode: snapshot.mode ?? snapshot.task_type ?? "medium",
    taskType: snapshot.task_type ?? snapshot.mode ?? "medium",
    initialized: snapshot.initialized ?? true,
    done: Boolean(snapshot.done),
    step: snapshot.step ?? 0,
    observation,
    currentState:
      snapshot.currentState ??
      (observation
        ? [
            observation.pending_tasks,
            observation.delayed_tasks,
            observation.high_priority_tasks,
            observation.avg_workload,
            observation.idle_employees,
          ]
        : [0, 0, 0, 0, 0]),
    reward: rewardValue,
    rewardReason,
    rewardBreakdown: snapshot.reward_data?.breakdown ?? snapshot.info?.reward_breakdown ?? null,
    action: snapshot.action ?? null,
    actionDescription: snapshot.info?.last_action_reason ?? "No action explanation available yet.",
    metrics: snapshot.metrics ?? null,
    graderScore: snapshot.grader?.score ?? snapshot.graderScore ?? 0,
    graderLabel: snapshot.grader?.label ?? snapshot.graderLabel ?? "Poor",
    logs: safeArray(snapshot.logs).length ? snapshot.logs : initialLogs,
    chartData: chartData.length ? chartData : [{ tick: "00", tasks: 0 }],
    comparisonSummary: snapshot.comparison ?? null,
    comparisonData: safeArray(snapshot.comparison?.chart),
    employees: safeArray(snapshot.employees),
    employeeDetails: safeArray(snapshot.employeeDetails),
    tasks: safeArray(snapshot.tasks),
  };
}

function ThemeSwitch({ theme, onToggle }) {
  const dark = theme === "dark";

  return (
    <button
      type="button"
      role="switch"
      aria-checked={dark}
      aria-label="Toggle theme"
      onClick={onToggle}
      className={`theme-switch ${dark ? "is-dark" : "is-light"}`}
    >
      <span className="theme-switch__label">Light</span>
      <span className="theme-switch__track">
        <span className="theme-switch__thumb">
          {dark ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
        </span>
      </span>
      <span className="theme-switch__label">Dark</span>
    </button>
  );
}

function InfoRow({ label, value, tone = "default" }) {
  return (
    <div className="info-row">
      <span className="info-row__label">{label}</span>
      <span className={`info-row__value info-row__value--${tone}`}>{value}</span>
    </div>
  );
}

function DecisionItem({ index, currentStep, entry }) {
  return (
    <div className="decision-log__item">
      <span className="decision-log__step">Step {Math.max(currentStep - index, 0)}</span>
      <p>{entry}</p>
    </div>
  );
}

function TaskRecord({ task }) {
  return (
    <div className="record-card">
      <div className="record-row">
        <div>
          <p className="record-card__title">{task.title || task.taskId}</p>
          <p className="record-card__meta">{task.taskId} | {task.department}</p>
        </div>
        <StatusBadge status={task.status} />
      </div>
      <p className="record-card__description">{task.description}</p>
      <div className="record-card__footer">
        <span>{task.priority}</span>
        <span>{task.deadline || "No deadline"}</span>
        <span>{task.completionTime != null ? `Completed at ${task.completionTime}` : "In progress"}</span>
      </div>
    </div>
  );
}

function EmployeeCard({ employee, onSelect }) {
  return (
    <button type="button" className="employee-card" onClick={() => onSelect(employee.id)}>
      <div className="employee-card__main">
        <div>
          <p className="employee-card__name">{employee.name}</p>
          <p className="employee-card__meta">{employee.skill}</p>
        </div>
        <StatusBadge status={employee.status} />
      </div>
      <div className="employee-card__stats">
        <span>{employee.workload}% load</span>
        <span>{employee.currentTasks?.length ?? 0} active</span>
        <span>{employee.completedTasks ?? 0} completed</span>
      </div>
      <div className="employee-card__tasks">
        {(employee.currentTasks?.length ? employee.currentTasks : ["No active tasks"]).map((taskId) => (
          <span key={taskId} className="task-chip">
            {taskId}
          </span>
        ))}
      </div>
    </button>
  );
}

function EmployeeDetailModal({ detail, onClose }) {
  if (!detail) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-shell" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <p className="panel-kicker">Employee Detail</p>
            <h3>{detail.name}</h3>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close employee detail">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="modal-grid">
          <GlassPanel title="Profile" subtitle="Current routing context.">
            <div className="info-stack">
              <InfoRow label="Skill level" value={`${detail.skill} (${detail.skillLevel})`} />
              <InfoRow label="Current workload" value={`${detail.currentWorkload}%`} />
              <InfoRow label="Status" value={detail.status} tone="accent" />
              <InfoRow
                label="Efficiency score"
                value={Number(detail.efficiencyStats?.efficiency_score ?? 0).toFixed(2)}
                tone="accent"
              />
            </div>
          </GlassPanel>

          <GlassPanel title="Efficiency Stats" subtitle="Employee-level throughput tracking.">
            <div className="info-stack">
              <InfoRow label="Active tasks" value={detail.efficiencyStats?.active_tasks ?? 0} />
              <InfoRow label="Completed tasks" value={detail.efficiencyStats?.completed_tasks ?? 0} />
              <InfoRow label="Delayed tasks" value={detail.efficiencyStats?.delayed_tasks ?? 0} />
              <InfoRow
                label="On-time rate"
                value={formatPercent(detail.efficiencyStats?.on_time_rate ?? 0)}
                tone="accent"
              />
            </div>
          </GlassPanel>

          <GlassPanel title="Active Tasks" subtitle="Current assignments.">
            <div className="record-list">
              {detail.activeTasks.length ? (
                detail.activeTasks.map((task) => <TaskRecord key={task.taskId} task={task} />)
              ) : (
                <p className="empty-state">No active tasks assigned.</p>
              )}
            </div>
          </GlassPanel>

          <GlassPanel title="Delayed Tasks" subtitle="Current risk areas.">
            <div className="record-list">
              {detail.delayedTasks.length ? (
                detail.delayedTasks.map((task) => <TaskRecord key={task.taskId} task={task} />)
              ) : (
                <p className="empty-state">No delayed tasks for this employee.</p>
              )}
            </div>
          </GlassPanel>
        </div>

        <GlassPanel title="Task History" subtitle="Completed and assigned task history.">
          <div className="table-shell">
            <table className="task-table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Completion time</th>
                </tr>
              </thead>
              <tbody>
                {detail.completedHistory.length ? (
                  detail.completedHistory.map((task) => (
                    <tr key={task.taskId}>
                      <td>
                        <div className="task-table__primary">{task.title || task.taskId}</div>
                        <div className="task-table__secondary">{task.taskId} | {task.department}</div>
                      </td>
                      <td>{task.priority}</td>
                      <td><StatusBadge status={task.status} /></td>
                      <td>{task.completionTime ?? "-"}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="empty-state empty-state--table">No completed history yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}

export default function App() {
  const [sim, setSim] = useState(() => createInitialState());
  const [theme, setTheme] = useState("light");
  const [cursor, setCursor] = useState({ x: 0, y: 0 });
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const intervalRef = useRef(null);
  const pendingStepRef = useRef(false);
  const localEnvRef = useRef(null);
  const simRef = useRef(sim);
  const activeApiBaseRef = useRef(null);
  const apiBases = useMemo(() => buildApiBases(), []);

  const chartTheme = useMemo(() => getChartTheme(theme), [theme]);
  const taskProfile = taskProfiles[sim.mode] ?? taskProfiles.medium;

  const workloadData = useMemo(
    () =>
      sim.employees.map((employee) => ({
        name: employee.name.split(" ")[0],
        workload: employee.workload,
      })),
    [sim.employees],
  );

  const selectedEmployeeDetail = useMemo(
    () => sim.employeeDetails.find((employee) => employee.id === selectedEmployeeId) ?? null,
    [selectedEmployeeId, sim.employeeDetails],
  );

  const comparisonView = useMemo(() => {
    const summary = sim.comparisonSummary;
    if (summary?.baseline && summary?.ai) {
      return {
        baselineCompleted: summary.baseline.completed_tasks,
        baselineDelays: summary.baseline.delayed_tasks,
        baselineEfficiency: Number(summary.baseline.efficiency ?? 0).toFixed(2),
        aiCompleted: summary.ai.completed_tasks,
        aiDelays: summary.ai.delayed_tasks,
        aiEfficiency: Number(summary.ai.efficiency ?? 0).toFixed(2),
        averageLabel: summary.label,
      };
    }

    return {
      baselineCompleted: 0,
      baselineDelays: 0,
      baselineEfficiency: "0.00",
      aiCompleted: sim.metrics?.completed_tasks ?? 0,
      aiDelays: sim.metrics?.delayed_tasks ?? 0,
      aiEfficiency: Number(sim.metrics?.efficiency ?? 0).toFixed(2),
      averageLabel: sim.graderLabel,
    };
  }, [sim.comparisonSummary, sim.graderLabel, sim.metrics]);

  async function apiRequest(path, options = {}) {
    let lastError = null;
    const candidates = [
      activeApiBaseRef.current,
      window.localStorage.getItem("govtai-working-api-base")?.trim(),
      ...apiBases,
    ];

    for (const base of [...new Set(candidates.filter((candidate) => candidate !== null && candidate !== undefined))]) {
      try {
        const url = base ? `${base}${path}` : path;
        const response = await fetch(url, {
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            "bypass-tunnel-reminder": "true",
            "ngrok-skip-browser-warning": "true",
          },
          ...options,
        });
        if (!response.ok) {
          let message = `API request failed: ${response.status} at ${url}`;
          try {
            const body = await response.json();
            if (body?.detail) message = `${message} - ${body.detail}`;
          } catch {
            // Keep generic error.
          }
          lastError = new Error(message);
          continue;
        }
        activeApiBaseRef.current = base;
        window.localStorage.setItem("govtai-working-api-base", base ?? "");
        return await response.json();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(`Unknown API request error at ${base || "same-origin"}.`);
      }
    }

    throw lastError ?? new Error("API request failed.");
  }

  async function loadComparison(mode = sim.mode) {
    try {
      const response = await apiRequest("/comparison");
      setSim((current) => ({
        ...current,
        comparisonSummary: response.task_type === mode ? response : current.comparisonSummary,
        comparisonData: response.task_type === mode ? response.chart ?? [] : current.comparisonData,
        apiError: null,
      }));
    } catch {
      setSim((current) => ({
        ...current,
        comparisonData:
          current.comparisonData.length
            ? current.comparisonData
            : [
                { name: "Baseline", efficiency: 55, delays: 3 },
                { name: "AI", efficiency: current.metrics?.efficiency ?? 0, delays: current.metrics?.delayed_tasks ?? 0 },
              ],
        apiError: current.initialized ? current.apiError : null,
      }));
    }
  }

  function applySnapshot(snapshot, extra = {}) {
    const normalized = normalizeSnapshot(snapshot);
    setSim((current) => ({
      ...current,
      ...normalized,
      running: extra.running ?? current.running,
      comparisonSummary: extra.comparisonSummary ?? normalized.comparisonSummary ?? current.comparisonSummary,
      comparisonData: extra.comparisonData ?? normalized.comparisonData ?? current.comparisonData,
      apiError: extra.apiError ?? null,
    }));
  }

  async function resetFromBackend(mode, shouldRun = false) {
    try {
      const snapshot = await apiRequest("/reset", {
        method: "POST",
        body: JSON.stringify({ mode, task_type: mode }),
      });
      localEnvRef.current = null;
      applySnapshot(snapshot, { running: shouldRun, apiError: null });
      setSelectedEmployeeId(null);
      void loadComparison(mode);
      return normalizeSnapshot(snapshot);
    } catch (error) {
      const fallback = localReset(mode, shouldRun);
      localEnvRef.current = fallback.env;
      setSim({
        ...createInitialState(mode),
        ...normalizeSnapshot(fallback.snapshot),
        running: shouldRun,
        apiError: null,
      });
      return normalizeSnapshot(fallback.snapshot);
    }
  }

  async function stepFromBackend(skipInitCheck = false) {
    if (pendingStepRef.current) return;
    if (!skipInitCheck && !simRef.current.initialized) {
      setSim((current) => ({ ...current, apiError: "Start the environment before stepping." }));
      return;
    }

    pendingStepRef.current = true;
    try {
      const snapshot = await apiRequest("/step", { method: "POST" });
      localEnvRef.current = null;
      applySnapshot(snapshot, { running: snapshot.done ? false : simRef.current.running });
    } catch (error) {
      if (!localEnvRef.current) {
        const fallback = localReset(simRef.current.mode, simRef.current.running);
        localEnvRef.current = fallback.env;
        setSim((current) => ({
          ...current,
          ...normalizeSnapshot(fallback.snapshot),
          running: current.running,
          apiError: null,
        }));
      } else {
        const snapshot = localStep(localEnvRef.current);
        setSim((current) => ({
          ...current,
          ...normalizeSnapshot(snapshot),
          running: snapshot.done ? false : current.running,
          apiError: null,
        }));
      }
    } finally {
      pendingStepRef.current = false;
    }
  }

  async function runFullSimulation() {
    try {
      const snapshot = await apiRequest("/run-full", {
        method: "POST",
        body: JSON.stringify({ mode: sim.mode, task_type: sim.mode, max_steps: 50 }),
      });
      localEnvRef.current = null;
      applySnapshot(snapshot, {
        running: false,
        comparisonSummary: snapshot.comparison ?? sim.comparisonSummary,
        comparisonData: snapshot.comparison?.chart ?? sim.comparisonData,
      });
    } catch (error) {
      if (!localEnvRef.current) {
        const fallback = localReset(sim.mode, false);
        localEnvRef.current = fallback.env;
      }
      let snapshot = localSnapshot(localEnvRef.current, 0, "Local fallback initialized.");
      while (!snapshot.done) {
        snapshot = localStep(localEnvRef.current);
      }
      setSim((current) => ({
        ...current,
        ...normalizeSnapshot(snapshot),
        running: false,
        apiError: null,
      }));
    }
  }

  async function toggleSimulation() {
    if (sim.running) {
      simRef.current = { ...simRef.current, running: false };
      setSim((current) => ({ ...current, running: false, apiError: null }));
      return;
    }

    if (!sim.initialized || sim.done) {
      await resetFromBackend(sim.mode, false);
      simRef.current = { ...simRef.current, running: true };
      setSim((current) => ({ ...current, running: true, apiError: null }));
      void stepFromBackend(true);
      return;
    }

    simRef.current = { ...simRef.current, running: true };
    setSim((current) => ({ ...current, running: true, apiError: null }));
    void stepFromBackend(true);
  }

  async function resetSimulation() {
    await resetFromBackend(sim.mode, false);
  }

  async function changeTaskType(event) {
    await resetFromBackend(event.target.value, false);
  }

  function toggleTheme() {
    setTheme((current) => {
      const next = current === "light" ? "dark" : "light";
      window.localStorage.setItem("govtai-theme", next);
      return next;
    });
  }

  useEffect(() => {
    const storedTheme = window.localStorage.getItem("govtai-theme");
    if (storedTheme === "light" || storedTheme === "dark") setTheme(storedTheme);
  }, []);

  useEffect(() => {
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  useEffect(() => {
    simRef.current = sim;
  }, [sim]);

  useEffect(() => {
    function handlePointerMove(event) {
      setCursor({ x: event.clientX, y: event.clientY });
    }
    window.addEventListener("pointermove", handlePointerMove);
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, []);

  useEffect(() => {
    void resetFromBackend("medium", false);
  }, []);

  useEffect(() => {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (!sim.running || sim.done || !sim.initialized) return undefined;

    intervalRef.current = window.setInterval(() => {
      void stepFromBackend();
    }, 1000);

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [sim.running, sim.done, sim.initialized]);

  const comparisonChart = sim.comparisonData.length
    ? sim.comparisonData
    : [
        { name: "Baseline", efficiency: 0, delays: 0 },
        { name: "AI", efficiency: sim.metrics?.completion_rate ? Math.round(sim.graderScore * 100) : 0, delays: sim.metrics?.delayed_tasks ?? 0 },
      ];

  return (
    <div className={`app-shell theme-${theme}`}>
      <div className="app-background" />
      <div className="cursor-ring hidden md:block" style={{ transform: `translate(${cursor.x - 18}px, ${cursor.y - 18}px)` }} />
      <div className="cursor-core hidden md:block" style={{ transform: `translate(${cursor.x - 4}px, ${cursor.y - 4}px)` }} />

      <div className="app-frame">
        <header className="topbar">
          <div>
            <p className="panel-kicker">OpenEnv Real-World Environment</p>
            <h1 className="page-title">GovtAI Ops</h1>
          </div>
          <div className="topbar__controls">
            <label className="field-block" htmlFor="task-type">
              <span className="field-label">Task Selector</span>
              <select id="task-type" value={sim.mode} onChange={changeTaskType} className="select-input">
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </label>
            <div className="field-block">
              <span className="field-label">Theme</span>
              <ThemeSwitch theme={theme} onToggle={toggleTheme} />
            </div>
          </div>
        </header>

        <main className="main-layout">
          <aside className="left-panel">
            <GlassPanel title="Controls" subtitle="Existing simulation flow preserved.">
              <div className="control-stack">
                <button type="button" onClick={toggleSimulation} className="primary-action">
                  {sim.running ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  <span>{sim.running ? "Pause" : "Start"}</span>
                </button>
                <button type="button" onClick={stepFromBackend} className="secondary-action">
                  <StepForward className="h-4 w-4" />
                  <span>Step</span>
                </button>
                <button type="button" onClick={resetSimulation} className="secondary-action">
                  <RefreshCcw className="h-4 w-4" />
                  <span>Reset</span>
                </button>
                <button type="button" onClick={runFullSimulation} className="ghost-action">Run Full</button>
              </div>
              {sim.apiError ? <p className="inline-error">{sim.apiError}</p> : null}
            </GlassPanel>

            <GlassPanel title="Metrics Card" subtitle={taskProfile.objective}>
              <div className="metric-list">
                <MetricCard label="Completed" value={sim.metrics?.completed_tasks ?? 0} icon={Activity} />
                <MetricCard label="Delayed" value={sim.metrics?.delayed_tasks ?? 0} icon={Pause} />
                <MetricCard label="Balance" value={Number(sim.metrics?.workload_balance ?? 0).toFixed(2)} icon={Gauge} />
              </div>
            </GlassPanel>

            <GlassPanel title="Score Card" subtitle="Task-specific grader output.">
              <div className="score-card">
                <div className="score-card__value">{Number(sim.graderScore ?? 0).toFixed(2)}</div>
                <div className="score-card__label">{sim.graderLabel}</div>
                <div className="info-stack">
                  <InfoRow label="Reward" value={Number(sim.reward).toFixed(2)} tone="accent" />
                  <InfoRow label="Task" value={taskProfile.label} />
                  <InfoRow label="Status" value={sim.running ? "Running" : sim.done ? "Done" : "Paused"} />
                </div>
              </div>
            </GlassPanel>
          </aside>

          <section className="right-panel">
            <GlassPanel title="Graph" subtitle="Completion trend over time.">
              <div className="chart-area chart-area--wide">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sim.chartData}>
                    <CartesianGrid stroke={chartTheme.grid} vertical={false} />
                    <XAxis dataKey="tick" stroke={chartTheme.axis} tickLine={false} axisLine={false} />
                    <YAxis stroke={chartTheme.axis} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: chartTheme.tooltipBackground, border: chartTheme.tooltipBorder, borderRadius: "12px" }} labelStyle={{ color: chartTheme.tooltipLabel }} itemStyle={{ color: chartTheme.tooltipText }} />
                    <Line type="monotone" dataKey="tasks" stroke={chartTheme.accent} strokeWidth={3} dot={{ r: 3, fill: chartTheme.accent }} activeDot={{ r: 5, fill: chartTheme.accent }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </GlassPanel>

            <div className="right-panel__subgrid">
              <GlassPanel title="AI Decision Log" subtitle="Live decision visibility.">
                <div className="decision-summary"><Bot className="h-4 w-4" /><span>{sim.actionDescription}</span></div>
                <div className="decision-log">
                  {sim.logs.map((entry, index) => <DecisionItem key={`${entry}-${index}`} index={index} currentStep={sim.step} entry={entry} />)}
                </div>
              </GlassPanel>

              <GlassPanel title="AI vs Baseline" subtitle="Side-by-side comparison.">
                <div className="comparison-grid">
                  <div className="comparison-card">
                    <p className="comparison-card__title">Baseline</p>
                    <InfoRow label="Completed" value={comparisonView.baselineCompleted} />
                    <InfoRow label="Delays" value={comparisonView.baselineDelays} />
                    <InfoRow label="Efficiency" value={comparisonView.baselineEfficiency} />
                  </div>
                  <div className="comparison-card">
                    <p className="comparison-card__title">AI</p>
                    <InfoRow label="Completed" value={comparisonView.aiCompleted} />
                    <InfoRow label="Delays" value={comparisonView.aiDelays} />
                    <InfoRow label="Efficiency" value={comparisonView.aiEfficiency} tone="accent" />
                  </div>
                  <div className="comparison-card comparison-card--accent">
                    <p className="comparison-card__title">Assessment</p>
                    <InfoRow label="Label" value={comparisonView.averageLabel} tone="accent" />
                    <InfoRow label="Reward" value={Number(sim.reward).toFixed(2)} tone="accent" />
                  </div>
                </div>
                <div className="chart-area chart-area--compact">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={comparisonChart}>
                      <CartesianGrid stroke={chartTheme.grid} vertical={false} />
                      <XAxis dataKey="name" stroke={chartTheme.axis} tickLine={false} axisLine={false} />
                      <YAxis stroke={chartTheme.axis} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ background: chartTheme.tooltipBackground, border: chartTheme.tooltipBorder, borderRadius: "12px" }} labelStyle={{ color: chartTheme.tooltipLabel }} itemStyle={{ color: chartTheme.tooltipText }} />
                      <Bar dataKey="efficiency" radius={[6, 6, 0, 0]}>
                        {comparisonChart.map((entry) => <Cell key={entry.name} fill={entry.name === "AI" ? chartTheme.accent : "#94a3b8"} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassPanel>
            </div>
          </section>
        </main>

        <section className="tracking-layout">
          <GlassPanel title="Employee Tracking" subtitle="Click an employee for detailed workload and task history.">
            <div className="tracking-grid">
              <div>
                <div className="section-header"><Users className="h-4 w-4" /><span>Employees</span></div>
                <div className="employee-list">
                  {sim.employees.map((employee) => <EmployeeCard key={employee.id} employee={employee} onSelect={setSelectedEmployeeId} />)}
                </div>
              </div>
              <div>
                <div className="section-header"><Gauge className="h-4 w-4" /><span>Workload Graph</span></div>
                <div className="chart-area chart-area--compact">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={workloadData}>
                      <CartesianGrid stroke={chartTheme.grid} vertical={false} />
                      <XAxis dataKey="name" stroke={chartTheme.axis} tickLine={false} axisLine={false} />
                      <YAxis stroke={chartTheme.axis} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ background: chartTheme.tooltipBackground, border: chartTheme.tooltipBorder, borderRadius: "12px" }} labelStyle={{ color: chartTheme.tooltipLabel }} itemStyle={{ color: chartTheme.tooltipText }} />
                      <Bar dataKey="workload" radius={[6, 6, 0, 0]}>
                        {workloadData.map((entry) => <Cell key={entry.name} fill={entry.workload > 75 ? chartTheme.bad : entry.workload > 40 ? chartTheme.warn : chartTheme.accent} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div>
                <div className="section-header"><Activity className="h-4 w-4" /><span>Task Assignments</span></div>
                <div className="table-shell">
                  <table className="task-table">
                    <thead><tr><th>Task</th><th>Priority</th><th>Employee</th><th>Status</th><th>Completion</th></tr></thead>
                    <tbody>
                      {sim.tasks.map((task) => (
                        <tr key={task.id}>
                          <td>
                            <div className="task-table__primary">{task.title || task.id}</div>
                            <div className="task-table__secondary">{task.id} | {task.department}</div>
                          </td>
                          <td>{task.priority}</td>
                          <td>{task.employee}</td>
                          <td><StatusBadge status={task.status} /></td>
                          <td>{task.completionTime ?? "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </GlassPanel>
        </section>

        <section className="debug-layout">
          <GlassPanel title="OpenEnv Debug Panel" subtitle="State, action, reward, and metrics trace.">
            <div className="debug-grid">
              <InfoRow label="State vector" value={formatVector(sim.currentState)} />
              <InfoRow label="Action" value={sim.action?.action_name ?? "awaiting_start"} tone="accent" />
              <InfoRow label="Reward" value={`${Number(sim.reward).toFixed(2)} | ${sim.rewardReason}`} tone="accent" />
              <InfoRow label="Task type" value={sim.taskType} />
              <InfoRow label="Completion rate" value={Number(sim.metrics?.completion_rate ?? 0).toFixed(2)} />
              <InfoRow label="Delay ratio" value={Number(sim.metrics?.delay_ratio ?? 0).toFixed(2)} />
              <InfoRow label="Workload balance" value={Number(sim.metrics?.workload_balance ?? 0).toFixed(2)} />
              <InfoRow label="Objective" value={sim.metrics?.objective ?? taskProfile.objective} />
            </div>
          </GlassPanel>
        </section>
      </div>

      <EmployeeDetailModal detail={selectedEmployeeDetail} onClose={() => setSelectedEmployeeId(null)} />
    </div>
  );
}
