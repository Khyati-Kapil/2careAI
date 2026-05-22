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

Optional (Redis-backed memory with TTL):
```bash
export REDIS_URL=redis://127.0.0.1:6379/0
export SESSION_TTL_SECONDS=3600
uvicorn services.memory_py.app.main:app --port 8002 --reload
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
- Redis-backed memory is supported:
- `REDIS_URL` enables Redis storage
- session memory uses TTL via `SESSION_TTL_SECONDS` (default `3600`)
- patient memory is persisted without TTL for cross-session continuity
- If Redis is unavailable, service falls back to in-memory dictionaries.

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
- Redis latency tuning and connection pooling

## Tradeoffs and Known Limitations

- No real telephony/SIP in this baseline
- ASR/TTS are represented as integration points, not production providers yet
- Natural-language time parsing is intentionally heuristic for now (e.g., tomorrow morning/evening)
- No durable SQL store yet for long-term analytics (current persistent option is Redis key-value)

## Submission Artifacts Checklist

- [ ] Final architecture diagram PNG/PDF export from `docs/architecture.md`
- [ ] Loom walkthrough (<=3 minutes)
- [ ] Latency benchmark report (`benchmarks/`)
- [ ] Full multilingual edge-case tests
