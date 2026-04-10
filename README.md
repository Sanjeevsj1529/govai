---
title: GovtAI Ops
emoji: 🏛️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# GovtAI Parliament Ops 🏛️

GovtAI Parliament Ops is a high-reliability governance simulation with an AI-powered task allocation engine and interactive dashboard. It features a full OpenEnv-compliant simulation environment, LLM-driven decision-making, and comprehensive performance grading.

## 🚀 Key Features

- **AI Task Allocation Engine**: LLM-powered agent (via OpenAI proxy) that optimizes government task routing across employees using 4 strategic actions.
- **OpenEnv Simulation**: Full environment with observation vectors, reward shaping, and grader evaluation across easy/medium/hard task profiles.
- **Interactive Dashboard**: Real-time React + Vite frontend with simulation controls, employee details, task tracking, charts, and comparison analysis.
- **ML Integration**: Sentiment analysis using Hugging Face Transformers with PyTorch backend.
- **Gradio Parliament Debate**: Three-agent AI parliament (Proposer, Opposer, Moderator) for policy debate simulation.
- **High Reliability**: Comprehensive error handling, heuristic fallbacks, and local simulation fallback when backend is unreachable.

## 🛠️ Tech Stack

- **Frontend**: React 18 + Vite + Recharts + Lucide Icons
- **Backend**: FastAPI + Uvicorn
- **AI Agent**: OpenAI SDK (proxy mode) with heuristic fallback
- **ML Engine**: Transformers + PyTorch (DistilBERT sentiment analysis)
- **UI Alternative**: Gradio (Parliament Debate mode)
- **Deployment**: Docker (Hugging Face Spaces compatible)

## 📋 Setup & Deployment

### 1. Environment Variables
Set the following in your environment or a `.env` file:
```env
API_BASE_URL=your_proxy_url
API_KEY=your_proxy_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
npm install
```

### 3. Run Backend (FastAPI)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Run Frontend (Dev Mode)
```bash
npm run dev
```

### 5. Run Gradio App (Alternative)
```bash
python app.py
```

## 🏛️ Simulation Architecture

### Observation Space (5D Vector)
| Index | Field | Description |
|-------|-------|-------------|
| 0 | `pending_tasks` | Unfinished tasks still pending or in progress |
| 1 | `delayed_tasks` | Tasks that missed their deadline |
| 2 | `high_priority_tasks` | Unfinished high-priority tasks |
| 3 | `avg_workload` | Average active workload across employees |
| 4 | `idle_employees` | Employees with no assigned work |

### Action Space (4 Discrete Actions)
| ID | Action | Description |
|----|--------|-------------|
| 0 | `assign_best` | Route to highest-skilled employee |
| 1 | `assign_least_busy` | Route to least-loaded employee |
| 2 | `reassign` | Rebalance overloaded employee tasks |
| 3 | `prioritize_urgent` | Escalate deadline-critical tasks |

### Reward Shaping
- `+10` per task completion
- `+5` per early completion
- `+1` per progress step
- `-5` per idle employee
- `-10` per new delay
- `-20` per repeated bad decision loop

## 🔬 Validation Compliance
- ✅ **Proxy-Only API**: Uses only the provided proxy via `API_BASE_URL`
- ✅ **Zero Runtime Errors**: Comprehensive error handling with fallbacks
- ✅ **Input Sanitization**: Handles empty/invalid inputs gracefully
- ✅ **ML Requirement**: Integrated PyTorch-based sentiment classification
- ✅ **OpenEnv Compliant**: Standard reset/step/state API with graders
