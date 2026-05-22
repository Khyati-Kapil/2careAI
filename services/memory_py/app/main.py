from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field
from redis import Redis
from redis.exceptions import RedisError

from shared.models import Language

app = FastAPI(title="memory-service")

SESSION_MEMORY: dict[str, dict] = {}
PATIENT_MEMORY: dict[str, dict] = {}
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
REDIS_URL = os.getenv("REDIS_URL", "")


def _build_redis_client() -> Redis | None:
    if not REDIS_URL:
        return None
    try:
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except RedisError:
        return None


REDIS_CLIENT = _build_redis_client()


class SessionUpdate(BaseModel):
    call_id: str
    intent: str | None = None
    pending_fields: dict[str, str] = Field(default_factory=dict)
    language: Language | None = None


class PatientUpdate(BaseModel):
    patient_id: str
    preferred_language: Language | None = None
    note: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "redis_enabled": "true" if REDIS_CLIENT else "false",
        "session_ttl_seconds": str(SESSION_TTL_SECONDS),
    }


@app.get("/session/{call_id}")
def get_session(call_id: str) -> dict:
    if REDIS_CLIENT:
        key = f"session:{call_id}"
        raw = REDIS_CLIENT.get(key)
        if raw:
            return json.loads(raw)
    return SESSION_MEMORY.get(call_id, {})


@app.post("/session")
def upsert_session(payload: SessionUpdate) -> dict:
    if REDIS_CLIENT:
        raw = REDIS_CLIENT.get(f"session:{payload.call_id}")
        current = json.loads(raw) if raw else {}
    else:
        current = SESSION_MEMORY.get(payload.call_id, {})
    next_value = {
        **current,
        "intent": payload.intent if payload.intent is not None else current.get("intent"),
        "pending_fields": {**current.get("pending_fields", {}), **payload.pending_fields},
        "language": payload.language.value if payload.language else current.get("language"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if REDIS_CLIENT:
        REDIS_CLIENT.setex(f"session:{payload.call_id}", SESSION_TTL_SECONDS, json.dumps(next_value))
    else:
        SESSION_MEMORY[payload.call_id] = next_value
    return next_value


@app.get("/patient/{patient_id}")
def get_patient(patient_id: str) -> dict:
    if REDIS_CLIENT:
        raw = REDIS_CLIENT.get(f"patient:{patient_id}")
        if raw:
            return json.loads(raw)
    return PATIENT_MEMORY.get(patient_id, {})


@app.post("/patient")
def upsert_patient(payload: PatientUpdate) -> dict:
    if REDIS_CLIENT:
        raw = REDIS_CLIENT.get(f"patient:{payload.patient_id}")
        current = json.loads(raw) if raw else {}
    else:
        current = PATIENT_MEMORY.get(payload.patient_id, {})
    notes = list(current.get("notes", []))
    if payload.note:
        notes.append(payload.note)

    next_value = {
        **current,
        "preferred_language": payload.preferred_language.value if payload.preferred_language else current.get("preferred_language", "en"),
        "notes": notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if REDIS_CLIENT:
        REDIS_CLIENT.set(f"patient:{payload.patient_id}", json.dumps(next_value))
    else:
        PATIENT_MEMORY[payload.patient_id] = next_value
    return next_value
