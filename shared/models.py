from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class Language(str, Enum):
    EN = "en"
    HI = "hi"
    TA = "ta"


class Intent(str, Enum):
    BOOK = "book"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CANCELED = "canceled"


class PatientProfile(BaseModel):
    patient_id: str
    name: str
    preferred_language: Language = Language.EN


class Appointment(BaseModel):
    appointment_id: str
    patient_id: str
    doctor_id: str
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.BOOKED


class SlotQuery(BaseModel):
    doctor_id: str
    start_time: datetime
    end_time: datetime


class AgentTurnRequest(BaseModel):
    call_id: str
    patient_id: str
    utterance: str = Field(min_length=1)
    language_hint: Language | None = None


class AgentTurnResponse(BaseModel):
    call_id: str
    language: Language
    intent: Intent
    response_text: str
    tool_trace: list[str]
    latency_ms: dict[str, float]
