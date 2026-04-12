# 🏛️ GovAI Ops — Explainable AI for Government Workflow Optimization

> **AI-powered decision engine that optimizes civic-service task allocation with real-time, explainable reasoning.**

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Live%20Demo-Hugging%20Face-orange)](https://huggingface.co/spaces/Sanjeevsj1529/govai)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Validated-brightgreen)](https://openenv.ai)

---

## 🚨 The Problem

Government offices worldwide suffer from:

- **Chronic task delays** — citizen requests pile up due to poor prioritization
- **Unbalanced workloads** — some employees are overloaded while others sit idle
- **No explainability** — supervisors can't audit _why_ a task was routed a certain way
- **Manual inefficiency** — rule-based systems struggle with dynamic, high-priority surges

These inefficiencies translate directly into slower public services, frustrated citizens, and wasted government resources.

---

## 💡 The Solution

**GovAI Ops** replaces static rule-based routing with an **LLM-powered AI decision engine** that:

1. **Observes** the live environment state (pending tasks, delays, workload, idle employees)
2. **Reasons** about the optimal action using GPT-4o-mini via a secure API proxy
3. **Explains** every decision with a structured output: Action + Reasoning + Impact + Confidence
4. **Adapts** in real-time as new tasks arrive and conditions change

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **AI Decision Engine** | LLM selects from 4 expert actions every simulation step |
| 📋 **Explainable Outputs** | Every decision shows Recommended Action, Reasoning, Impact & Confidence Score |
| 📊 **AI vs Baseline Comparison** | Live side-by-side efficiency and delay metrics |
| ⚡ **Real-Time Simulation** | Step-by-step or full auto-run with live charts |
| 🛡️ **Robust Fallback** | If LLM is unavailable, structured heuristic output is shown instantly |
| 👥 **Employee Tracking** | Click any employee to see workload, task history, and efficiency stats |
| 🌙 **Dark Mode** | Full light/dark theme with smooth transitions |

---

## 🤖 AI Decision Output Format

Every step, the AI engine produces structured, auditable output:

```
Recommended Action: prioritize_urgent
Reasoning: 3 high-priority tasks detected in queue — escalating urgency.
Impact: Fast-tracks critical civic-service cases to meet strict deadlines.
Confidence Score: 90%
```

- **Green badge** = High confidence (≥ 80%)
- **Yellow badge** = Medium confidence (50–79%)
- **Red badge** = Low confidence (< 50%)

---

## 📈 Measured Impact

Running the AI agent against a rule-based baseline across simulation modes:

| Metric | Baseline | AI Agent | Improvement |
|---|---|---|---|
| Efficiency Score | ~55% | ~72%+ | **+17 points** |
| Delayed Tasks | 3–5 avg | 1–2 avg | **~60% reduction** |
| Idle Employee Waste | High | Minimized | **Optimized automatically** |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              React Frontend (Vite)           │
│  Real-time charts · Structured AI output    │
│  Employee tracking · AI vs Baseline panel   │
└────────────────────┬────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────┐
│              FastAPI Backend                 │
│  GovtEnv (OpenEnv) · SimulationService      │
│  GovtAgent → LLM Proxy (GPT-4o-mini)       │
└─────────────────────────────────────────────┘
```

**Tech Stack:** FastAPI · React 18 · Recharts · OpenAI-compatible Proxy · Hugging Face Transformers · Gradio

---

## 🚀 Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export API_BASE_URL="<your-proxy-base-url>"
export API_KEY="<your-api-key>"

# Start backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# In a separate terminal — start frontend
npm install && npm run dev
```

Or simply open the **[Live Demo on Hugging Face →](https://huggingface.co/spaces/Sanjeevsj1529/govai)**

---

## 🔬 Grading & Validation

This project is validated by the **OpenEnv** automated grading system:

- ✅ Phase 1 Passed — Environment & reward signal
- ✅ Phase 2 Passed — LLM proxy API traffic confirmed
- ✅ Fail-safe fallback — app never hangs, always produces output

---

## 📁 Project Structure

```
govai/
├── main.py          # FastAPI server + simulation service
├── agent.py         # GovtAgent — LLM decision engine
├── env.py           # GovtEnv — OpenEnv-compatible environment
├── baseline.py      # Baseline comparison logic
├── reward.py        # Reward computation
├── src/
│   ├── App.jsx      # React frontend — simulation dashboard
│   └── index.css    # Design system
└── app.py           # Gradio parliament debate UI
```

---

## 👤 Author

Built for the OpenEnv Hackathon · April 2026
