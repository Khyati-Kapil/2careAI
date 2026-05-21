from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

from shared.models import Language

app = FastAPI(title="memory-service")

SESSION_MEMORY: dict[str, dict] = {}
PATIENT_MEMORY: dict[str, dict] = {}


class SessionUpdate(BaseModel):
    call_id: str
    intent: str | None = None
    pending_fields: dict[str, str] = {}
    language: Language | None = None


class PatientUpdate(BaseModel):
    patient_id: str
    preferred_language: Language | None = None
    note: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/session/{call_id}")
def get_session(call_id: str) -> dict:
    return SESSION_MEMORY.get(call_id, {})


@app.post("/session")
def upsert_session(payload: SessionUpdate) -> dict:
    current = SESSION_MEMORY.get(payload.call_id, {})
    next_value = {
        **current,
        "intent": payload.intent if payload.intent is not None else current.get("intent"),
        "pending_fields": {**current.get("pending_fields", {}), **payload.pending_fields},
        "language": payload.language.value if payload.language else current.get("language"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    SESSION_MEMORY[payload.call_id] = next_value
    return next_value


@app.get("/patient/{patient_id}")
def get_patient(patient_id: str) -> dict:
    return PATIENT_MEMORY.get(patient_id, {})


@app.post("/patient")
def upsert_patient(payload: PatientUpdate) -> dict:
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
    PATIENT_MEMORY[payload.patient_id] = next_value
    return next_value
