from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="identity-service")

PATIENT_DIRECTORY: dict[str, dict] = {
    "+919900000001": {"patient_id": "pat-101", "name": "Asha", "confidence": 0.97},
    "+919900000002": {"patient_id": "pat-102", "name": "Ravi", "confidence": 0.95},
}


class IdentityResolveRequest(BaseModel):
    call_id: str
    caller_number: str | None = None
    provided_patient_id: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/resolve")
def resolve(req: IdentityResolveRequest) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    if req.provided_patient_id:
        return {
            "resolved": True,
            "patient_id": req.provided_patient_id,
            "method": "provided_patient_id",
            "confidence": 1.0,
            "resolved_at": now,
        }

    if req.caller_number and req.caller_number in PATIENT_DIRECTORY:
        row = PATIENT_DIRECTORY[req.caller_number]
        return {
            "resolved": True,
            "patient_id": row["patient_id"],
            "method": "caller_number_match",
            "confidence": row["confidence"],
            "resolved_at": now,
        }

    return {
        "resolved": False,
        "patient_id": None,
        "method": "no_match",
        "confidence": 0.0,
        "resolved_at": now,
    }
