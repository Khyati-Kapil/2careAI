from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.models import Appointment, AppointmentStatus, SlotQuery

app = FastAPI(title="scheduler-service")

DOCTORS = {"doc-1": "Dr. Rao", "doc-2": "Dr. Mehta"}
APPOINTMENTS: dict[str, Appointment] = {}


class BookRequest(BaseModel):
    patient_id: str
    doctor_id: str
    start_time: datetime
    duration_minutes: int = 30


class RescheduleRequest(BaseModel):
    appointment_id: str
    doctor_id: str
    start_time: datetime
    duration_minutes: int = 30


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_conflicting(doctor_id: str, start_time: datetime, end_time: datetime, ignore_id: str | None = None) -> bool:
    for appt in APPOINTMENTS.values():
        if appt.status != AppointmentStatus.BOOKED:
            continue
        if appt.doctor_id != doctor_id:
            continue
        if ignore_id and appt.appointment_id == ignore_id:
            continue
        overlaps = start_time < appt.end_time and end_time > appt.start_time
        if overlaps:
            return True
    return False


def _suggest_alternatives(doctor_id: str, from_time: datetime, count: int = 3) -> list[dict]:
    suggestions = []
    cursor = from_time
    while len(suggestions) < count:
        cursor = cursor + timedelta(minutes=30)
        end = cursor + timedelta(minutes=30)
        if cursor <= _utc_now():
            continue
        if not _is_conflicting(doctor_id, cursor, end):
            suggestions.append({"doctor_id": doctor_id, "start_time": cursor, "end_time": end})
    return suggestions


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/check_availability")
def check_availability(query: SlotQuery) -> dict:
    if query.doctor_id not in DOCTORS:
        return {"available": False, "reason": "doctor_unavailable", "alternatives": []}

    if query.start_time <= _utc_now():
        alternatives = _suggest_alternatives(query.doctor_id, _utc_now())
        return {"available": False, "reason": "past_time", "alternatives": alternatives}

    if _is_conflicting(query.doctor_id, query.start_time, query.end_time):
        alternatives = _suggest_alternatives(query.doctor_id, query.start_time)
        return {"available": False, "reason": "slot_conflict", "alternatives": alternatives}

    return {"available": True, "reason": "ok", "alternatives": []}


@app.post("/book")
def book(req: BookRequest) -> dict:
    if req.doctor_id not in DOCTORS:
        raise HTTPException(status_code=400, detail="doctor_unavailable")

    start_time = req.start_time
    end_time = start_time + timedelta(minutes=req.duration_minutes)

    if start_time <= _utc_now():
        raise HTTPException(status_code=400, detail="past_time")

    if _is_conflicting(req.doctor_id, start_time, end_time):
        raise HTTPException(status_code=409, detail="slot_conflict")

    appt_id = f"apt-{uuid4().hex[:8]}"
    appt = Appointment(
        appointment_id=appt_id,
        patient_id=req.patient_id,
        doctor_id=req.doctor_id,
        start_time=start_time,
        end_time=end_time,
    )
    APPOINTMENTS[appt_id] = appt
    return {"appointment": appt.model_dump()}


@app.post("/reschedule")
def reschedule(req: RescheduleRequest) -> dict:
    appt = APPOINTMENTS.get(req.appointment_id)
    if not appt or appt.status != AppointmentStatus.BOOKED:
        raise HTTPException(status_code=404, detail="appointment_not_found")

    start_time = req.start_time
    end_time = start_time + timedelta(minutes=req.duration_minutes)

    if start_time <= _utc_now():
        raise HTTPException(status_code=400, detail="past_time")

    if _is_conflicting(req.doctor_id, start_time, end_time, ignore_id=req.appointment_id):
        raise HTTPException(status_code=409, detail="slot_conflict")

    appt.doctor_id = req.doctor_id
    appt.start_time = start_time
    appt.end_time = end_time
    return {"appointment": appt.model_dump()}


@app.post("/cancel/{appointment_id}")
def cancel(appointment_id: str) -> dict:
    appt = APPOINTMENTS.get(appointment_id)
    if not appt or appt.status != AppointmentStatus.BOOKED:
        raise HTTPException(status_code=404, detail="appointment_not_found")
    appt.status = AppointmentStatus.CANCELED
    return {"appointment": appt.model_dump()}
