from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta, timezone
from urllib import error, request

from fastapi import FastAPI, HTTPException

from shared.latency import LatencyTracker
from shared.models import AgentTurnRequest, AgentTurnResponse, Intent, Language

app = FastAPI(title="agent-service")

SCHEDULER_URL = "http://127.0.0.1:8001"
MEMORY_URL = "http://127.0.0.1:8002"


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=1.5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise HTTPException(status_code=exc.code, detail=detail) from exc


def get_json(url: str) -> dict:
    with request.urlopen(url, timeout=1.5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def detect_language(text: str, hint: Language | None, preferred: str | None) -> Language:
    if hint:
        return hint
    lower = text.lower()
    if re.search(r"[\u0B80-\u0BFF]", text):
        return Language.TA
    if re.search(r"[\u0900-\u097F]", text):
        return Language.HI
    if any(w in lower for w in ["vanakkam", "doctor", "naalai"]):
        return Language.TA
    if any(w in lower for w in ["kal", "book", "namaste"]):
        return Language.HI
    if preferred in {"en", "hi", "ta"}:
        return Language(preferred)
    return Language.EN


def detect_intent(text: str) -> Intent:
    lower = text.lower()
    if any(x in lower for x in ["cancel", "रद्द", "ரத்து"]):
        return Intent.CANCEL
    if any(x in lower for x in ["reschedule", "change", "बदल", "மாற்ற"]):
        return Intent.RESCHEDULE
    if any(x in lower for x in ["book", "appointment", "बुक", "முன்பதிவு"]):
        return Intent.BOOK
    return Intent.UNKNOWN


def response_for_language(lang: Language, en: str, hi: str, ta: str) -> str:
    if lang == Language.HI:
        return hi
    if lang == Language.TA:
        return ta
    return en


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/turn", response_model=AgentTurnResponse)
def turn(payload: AgentTurnRequest) -> AgentTurnResponse:
    tracker = LatencyTracker()
    trace: list[str] = []

    with tracker.span("memory_read"):
        patient = get_json(f"{MEMORY_URL}/patient/{payload.patient_id}")
        session = get_json(f"{MEMORY_URL}/session/{payload.call_id}")

    with tracker.span("nlu"):
        intent = detect_intent(payload.utterance)
        lang = detect_language(payload.utterance, payload.language_hint, patient.get("preferred_language"))

    reply = ""
    with tracker.span("orchestration"):
        if intent == Intent.BOOK:
            start = datetime.now(timezone.utc) + timedelta(hours=2)
            end = start + timedelta(minutes=30)
            availability = post_json(
                f"{SCHEDULER_URL}/check_availability",
                {
                    "doctor_id": "doc-1",
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                },
            )
            trace.append(f"check_availability:{availability.get('reason')}")
            if availability.get("available"):
                booking = post_json(
                    f"{SCHEDULER_URL}/book",
                    {
                        "patient_id": payload.patient_id,
                        "doctor_id": "doc-1",
                        "start_time": start.isoformat(),
                        "duration_minutes": 30,
                    },
                )
                trace.append("book:success")
                appt_id = booking["appointment"]["appointment_id"]
                reply = response_for_language(
                    lang,
                    f"Your appointment is confirmed with Dr. Rao. ID: {appt_id}",
                    f"आपकी अपॉइंटमेंट डॉ. राव के साथ कन्फर्म हो गई है। आईडी: {appt_id}",
                    f"உங்கள் முன்பதிவு Dr. Rao உடன் உறுதி செய்யப்பட்டது. ஐடி: {appt_id}",
                )
            else:
                trace.append("book:conflict")
                reply = response_for_language(
                    lang,
                    "That slot is unavailable. I can suggest alternatives.",
                    "वह स्लॉट उपलब्ध नहीं है। मैं अन्य विकल्प सुझा सकता हूँ।",
                    "அந்த நேரம் இல்லை. மாற்று நேரங்களை பரிந்துரைக்கலாம்.",
                )
        elif intent == Intent.RESCHEDULE:
            reply = response_for_language(
                lang,
                "Please share your appointment ID and preferred new time.",
                "कृपया अपनी अपॉइंटमेंट आईडी और नया समय बताएं।",
                "தயவுசெய்து உங்கள் appointment ID மற்றும் புதிய நேரத்தை சொல்லுங்கள்.",
            )
        elif intent == Intent.CANCEL:
            reply = response_for_language(
                lang,
                "Please share your appointment ID and I will cancel it.",
                "कृपया अपनी अपॉइंटमेंट आईडी बताएं, मैं रद्द कर दूँगा।",
                "உங்கள் appointment ID கொடுக்கவும், நான் ரத்து செய்கிறேன்.",
            )
        else:
            reply = response_for_language(
                lang,
                "I can help with booking, rescheduling, or cancellation.",
                "मैं बुकिंग, रीशेड्यूल और कैंसिलेशन में मदद कर सकता हूँ।",
                "முன்பதிவு, மாற்றம், ரத்து செய்வதில் உதவ முடியும்.",
            )

    with tracker.span("memory_write"):
        post_json(
            f"{MEMORY_URL}/session",
            {
                "call_id": payload.call_id,
                "intent": intent.value,
                "language": lang.value,
            },
        )
        post_json(
            f"{MEMORY_URL}/patient",
            {
                "patient_id": payload.patient_id,
                "preferred_language": lang.value,
                "note": f"intent={intent.value};ts={int(time.time())}",
            },
        )

    return AgentTurnResponse(
        call_id=payload.call_id,
        language=lang,
        intent=intent,
        response_text=reply,
        tool_trace=trace,
        latency_ms={**tracker.data, "total": tracker.total()},
    )
