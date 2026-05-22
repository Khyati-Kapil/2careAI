# 2careAI - Real-Time Multilingual Voice Agent (Clinical Appointment Booking)

This repository implements a low-latency voice AI architecture for booking, rescheduling, and cancellation across English, Hindi, and Tamil.

## Current Progress (Step-by-Step Execution)

Implemented:
- Python services: `agent`, `scheduler`, `memory`
- TypeScript service: `voice-gateway`
- Outbound campaign worker scaffold
- Conflict checks: doctor existence, past-time rejection, overlap prevention
- Session + cross-session memory updates
- Multi-turn `reschedule` and `cancel` execution with appointment-id extraction
- Per-turn latency logging (`memory_read`, `nlu`, `orchestration`, `memory_write`, `total`)

## Architecture

- Diagram source: `/Users/khyati/2careAI/docs/architecture.md`
- Runtime components:
  - `apps/voice-gateway-ts`: receives turn payload, forwards to agent, returns trace + latency
  - `services/agent_py`: intent/language handling + tool orchestration
  - `services/scheduler_py`: appointment lifecycle and conflict logic
  - `services/memory_py`: session and patient memory
  - `workers/campaign_py`: outbound campaign trigger loop

## Run Locally

### 1) Python env

```bash
cd /Users/khyati/2careAI
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Start services

```bash
uvicorn services.scheduler_py.app.main:app --port 8001 --reload
uvicorn services.memory_py.app.main:app --port 8002 --reload
uvicorn services.agent_py.app.main:app --port 8000 --reload
```

### 3) Start gateway

```bash
npm install
npm run dev:gateway
```

### 4) Sample turn

```bash
curl -X POST http://127.0.0.1:3000/voice/turn \
  -H 'Content-Type: application/json' \
  -d '{"patientId":"pat-001","utterance":"मुझे appointment book करनी है"}'
```

### 5) Outbound campaign simulation

```bash
python workers/campaign_py/app/main.py
```

### 6) Latency benchmark

```bash
python benchmarks/latency_benchmark.py
```

## Memory Design

- Session memory (`call_id` keyed): current intent, pending fields, active language
- Cross-session memory (`patient_id` keyed): preferred language, interaction notes
- Current implementation is in-memory for fast iteration; interface is structured for Redis + persistent DB migration.

## Latency Design Notes

Target: `< 450 ms` speech-end to first audio response.

Current instrumentation logs:
- `memory_read`
- `nlu`
- `orchestration`
- `memory_write`
- `total`
- gateway adds `e2e_estimated`

Next optimization passes:
- streaming ASR partials
- speculative tool prefetch for high-confidence intent
- streaming TTS first-clause emit
- Redis for memory access predictability

## Tradeoffs and Known Limitations

- No real telephony/SIP in this baseline
- ASR/TTS are represented as integration points, not production providers yet
- Natural-language time parsing is intentionally heuristic for now (e.g., tomorrow morning/evening)
- In-memory stores are non-durable (planned Redis + Postgres)

## Submission Artifacts Checklist

- [ ] Final architecture diagram PNG/PDF export from `docs/architecture.md`
- [ ] Loom walkthrough (<=3 minutes)
- [ ] Latency benchmark report (`benchmarks/`)
- [ ] Full multilingual edge-case tests
