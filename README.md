---
title: GovtAI Ops
emoji: "\ud83c\udfe2"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# GovtAI Ops

GovtAI Ops is a real-world OpenEnv hackathon environment for government task allocation. It simulates a public-sector operations desk where tasks arrive over time, employees have different skill levels, deadlines matter, and an AI policy must assign, prioritize, and rebalance work without breaking throughput.

## Why This Matters

Government offices often face three practical problems:

- uneven task distribution across employees
- delayed citizen-service requests
- poor visibility into whether routing choices are actually improving outcomes

GovtAI Ops turns that into a structured environment that can be stepped, graded, compared against a baseline, and deployed in a reproducible way.

## Environment Overview

The environment models:

- government service tasks with priority, effort, and deadlines
- employees with varying skill levels and active workloads
- dynamic task arrivals, especially in harder settings
- AI actions for assignment, rebalancing, and urgent prioritization

The concept remains realistic throughout: this is not a game loop, but an operational task-allocation simulation.

## OpenEnv API

The backend exposes the standard environment interface:

- `POST /reset` returns an initialized snapshot and initial observation
- `POST /step` advances the environment by one action cycle and returns observation, reward, done, and info inside the snapshot
- `GET /state` returns the current typed observation model
- `POST /run-full` runs a full reproducible episode for the selected task type

The standard simulation response shape includes:

```json
{
  "observation": {
    "pending_tasks": 0,
    "delayed_tasks": 0,
    "high_priority_tasks": 0,
    "avg_workload": 0.0,
    "idle_employees": 0
  },
  "reward": {
    "value": 0.0,
    "reason": "string"
  },
  "action": {
    "action_id": 0,
    "action_name": "assign_best"
  },
  "done": false,
  "info": {},
  "metrics": {},
  "task_type": "medium"
}
```

## Observation Space

Observation fields:

- `pending_tasks`: unfinished tasks pending or in progress
- `delayed_tasks`: tasks that have crossed their deadline
- `high_priority_tasks`: unfinished high-priority tasks
- `avg_workload`: average workload across employees
- `idle_employees`: employees currently not carrying any work

## Action Space

Discrete actions:

- `0`: `assign_best`
- `1`: `assign_least_busy`
- `2`: `reassign`
- `3`: `prioritize_urgent`

## Task Definitions

### Easy

- small number of tasks
- stable workload
- main goal: maximize completion

### Medium

- moderate load
- some incoming tasks
- main goal: reduce delays and balance workload

### Hard

- dynamic incoming tasks
- sustained overload pressure
- main goal: handle overload and prioritize urgency

## Reward Logic

Reward shaping is continuous, not binary:

- `+10` task completion
- `+5` early completion
- `+1` progress
- `-5` idle employee
- `-10` delay
- `-20` repeated bad decisions or loops

This gives the agent meaningful step-by-step feedback instead of only terminal rewards.

## Grading

Each task is graded with the required deterministic formula:

```text
score = 0.5 * completion_rate + 0.3 * (1 - delay_ratio) + 0.2 * workload_balance
```

The score is clamped to `[0.0, 1.0]` and labeled as:

- `Poor`
- `Average`
- `Good`
- `Optimal`

## Baseline

`baseline.py` supports a reproducible baseline run across all three tasks with:

- `random.seed(42)`
- `OPENAI_API_KEY` read from the environment
- OpenAI API action selection when the key is available
- deterministic seeded fallback baseline when the key is missing, so the app still runs cleanly

The script prints:

- score per task
- final average score

Run it with:

```bash
python baseline.py
```

## Frontend

The frontend keeps the working simulation flow and existing features while using a cleaner student-built layout:

- top bar with title, task selector, and theme toggle
- left panel with Start/Pause, Step, Reset, metrics, and score
- right panel with graph, AI decision log, and AI-vs-baseline comparison
- employee tracking board with clickable employee detail modal
- bottom OpenEnv debug panel

The graph, debug panel, and control flow remain intact.

## Local Setup

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
npm install
npm run dev
```

The frontend proxies `/api/*` requests to the FastAPI server during development.

## Docker / Hugging Face Spaces

Build and run:

```bash
docker build -t govtai-ops .
docker run -p 8000:8000 govtai-ops
```

The project is container-friendly:

- Python 3.11 base image
- dependency installation from `requirements.txt`
- backend served with `uvicorn`
- no local-only runtime dependencies required for the core app

## Important Files

- `env.py`: environment dynamics and OpenEnv step/reset/state behavior
- `main.py`: API layer and typed snapshot responses
- `grader.py`: deterministic task scoring
- `baseline.py`: reproducible baseline runner
- `openenv.yaml`: environment metadata
- `src/App.jsx`: redesigned frontend UI

## Baseline Results

Using `python baseline.py` with seed `42`, the current reproducible fallback baseline produced:

- `easy`: `1.0000` (`Optimal`)
- `medium`: `0.9524` (`Optimal`)
- `hard`: `0.6414` (`Good`)
- `average_score`: `0.8646`

If `OPENAI_API_KEY` is set, `baseline.py` attempts the OpenAI policy first and falls back to the seeded baseline if the API path is unavailable.
