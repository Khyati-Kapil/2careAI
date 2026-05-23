# 2careAI - Real-Time Multilingual Voice Agent (Clinical Appointment Booking)

This repository implements a low-latency voice AI architecture for booking, rescheduling, and cancellation across English, Hindi, and Tamil.

## Current Progress (Step-by-Step Execution)

Implemented:
- Python services: `agent`, `scheduler`, `memory`
- Python `identity` service for caller-to-patient resolution
- TypeScript service: `voice-gateway`
- Outbound campaign worker queue with retry + outcome logging
- Conflict checks: doctor existence, past-time rejection, overlap prevention
- Session + cross-session memory updates
- Multi-turn `reschedule` and `cancel` execution with appointment-id extraction
- Language switch support (English/Hindi/Tamil) mid-conversation
- Reasoning trace persistence and retrieval endpoints
- Correlation IDs propagated gateway -> agent -> tool services
- Tool-call audit envelopes with status and latency per invocation
- Streaming response endpoint (SSE chunking for low-latency voice handoff simulation)
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
uvicorn services.identity_py.app.main:app --port 8003 --reload
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

Campaign outcomes are written to:
`/Users/khyati/2careAI/workers/campaign_py/outbound_outcomes.jsonl`

### 5.1) Streaming turn simulation (SSE)

```bash
curl -N -X POST http://127.0.0.1:3000/voice/turn/stream \
  -H 'Content-Type: application/json' \
  -d '{"patientId":"pat-001","utterance":"book appointment tomorrow morning"}'
```

### 6) Latency benchmark

```bash
python benchmarks/latency_benchmark.py
```

## Memory Design

- Session memory (`call_id` keyed): current intent, pending fields, active language, `conversation_state`, `pending_confirmation`
- Cross-session memory (`patient_id` keyed): preferred language, interaction notes, historical interaction trail
- Redis-backed memory is supported:
- `REDIS_URL` enables Redis storage
- session memory uses TTL via `SESSION_TTL_SECONDS` (default `3600`)
- patient memory is persisted without TTL for cross-session continuity
- If Redis is unavailable, service falls back to in-memory dictionaries.

Retrieval and prompt integration:
- Agent reads patient + session memory at the start of each turn.
- Retrieved memory directly changes orchestration policy:
- unknown utterance continues prior session intent for multi-turn completion
- stored `appointment_id` and `alternatives_json` drive follow-up execution
- `preferred_language` decides response language continuity across sessions
- Memory summary used for each turn is written into reasoning traces for demonstrability.

## Outbound Campaign Mode

- Campaign worker supports queued jobs, retry, and structured outcome logging.
- Campaigns can trigger reminder/follow-up turns in patient preferred language.
- Response handling includes:
- booking/reschedule/cancel flow detection
- polite rejection classification (`politely_declined`)
- JSONL audit output for campaign analytics and QA
- File: `/Users/khyati/2careAI/workers/campaign_py/outbound_outcomes.jsonl`

## Scheduling and Conflict Logic

- Scheduler validates:
- unavailable doctor (`doctor_unavailable`)
- past-time slot (`past_time`)
- overlap conflict (`slot_conflict`)
- Agent behavior on invalid slots:
- offers up to 3 alternatives
- stores alternatives in session memory
- supports next-turn confirmation via option number (`1/2/3`)
- prevents double booking by re-validating before final booking/reschedule.

## Reasoning Trace Visibility

- Agent stores structured per-turn traces in-memory (bounded ring buffer).
- Trace payload now includes:
- `correlation_id`
- `tool_audit` (tool, status, latency, error)
- `memory_summary` snapshot used at turn-time
- Endpoints:
  - `GET /traces?limit=50`
  - `GET /traces/{call_id}`
- Gateway passthrough:
  - `GET /voice/traces/:callId`
- Demo page includes auto-refreshing "Live Trace Viewer".

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
- replace SSE chunking with provider-backed streaming TTS
- Redis latency tuning and connection pooling

## Tradeoffs and Known Limitations

- No real telephony/SIP in this baseline
- ASR/TTS provider integration is still mocked at gateway/agent boundary
- Natural-language time parsing is intentionally heuristic for now (e.g., tomorrow morning/evening)
- No durable SQL store yet for long-term analytics (current persistent option is Redis key-value)

## Submission Artifacts Checklist

- [x] Final architecture diagram source in `docs/architecture.md`
- [x] Loom script in `docs/loom_script.md`
- [x] Latency benchmark runner in `benchmarks/latency_benchmark.py`
- [x] Baseline multilingual and helper tests in `tests/test_agent_helpers.py`
- [ ] Export architecture PNG/PDF
- [ ] Record final Loom walkthrough (<=3 minutes)
- [ ] Attach measured latency report from runtime execution
