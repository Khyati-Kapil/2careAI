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

APPOINTMENT_ID_RE = re.compile(r"\bapt-[a-zA-Z0-9]{4,}\b", re.IGNORECASE)


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


def extract_appointment_id(text: str) -> str | None:
    match = APPOINTMENT_ID_RE.search(text)
    if not match:
        return None
    return match.group(0).lower()


def parse_requested_start(text: str) -> datetime:
    lower = text.lower()
    base = datetime.now(timezone.utc)
    if "day after tomorrow" in lower:
        day_offset = 2
    elif any(w in lower for w in ["tomorrow", "kal", "நாளை"]):
        day_offset = 1
    else:
        day_offset = 0

    if any(w in lower for w in ["morning", "subah", "காலை"]):
        hour = 4
    elif any(w in lower for w in ["evening", "shaam", "மாலை"]):
        hour = 12
    elif any(w in lower for w in ["afternoon", "dopahar", "மதியம்"]):
        hour = 9
    else:
        hour = 2
    start = (base + timedelta(days=day_offset)).replace(minute=0, second=0, microsecond=0) + timedelta(hours=hour)
    if start <= base:
        start = base + timedelta(hours=2)
    return start


def response_for_language(lang: Language, en: str, hi: str, ta: str) -> str:
    if lang == Language.HI:
        return hi
    if lang == Language.TA:
        return ta
    return en


def _extract_http_detail(exc: HTTPException) -> str:
    raw = exc.detail
    if isinstance(raw, str):
        cleaned = raw.strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                body = json.loads(cleaned)
                if isinstance(body, dict) and "detail" in body:
                    return str(body["detail"])
            except json.JSONDecodeError:
                return cleaned
        return cleaned
    return str(raw)


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
        if intent == Intent.UNKNOWN and session.get("intent") in {"reschedule", "cancel"}:
            intent = Intent(session.get("intent"))
        lang = detect_language(payload.utterance, payload.language_hint, patient.get("preferred_language"))
        appointment_id = extract_appointment_id(payload.utterance) or session.get("pending_fields", {}).get("appointment_id")

    reply = ""
    pending_fields: dict[str, str] = {}
    with tracker.span("orchestration"):
        if intent == Intent.BOOK:
            start = parse_requested_start(payload.utterance)
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
            if not appointment_id:
                pending_fields["appointment_id"] = ""
                trace.append("reschedule:ask_appointment_id")
                reply = response_for_language(
                    lang,
                    "Please share your appointment ID and preferred new time.",
                    "कृपया अपनी अपॉइंटमेंट आईडी और नया समय बताएं।",
                    "தயவுசெய்து உங்கள் appointment ID மற்றும் புதிய நேரத்தை சொல்லுங்கள்.",
                )
            else:
                start = parse_requested_start(payload.utterance)
                try:
                    result = post_json(
                        f"{SCHEDULER_URL}/reschedule",
                        {
                            "appointment_id": appointment_id,
                            "doctor_id": "doc-1",
                            "start_time": start.isoformat(),
                            "duration_minutes": 30,
                        },
                    )
                    trace.append("reschedule:success")
                    appt = result["appointment"]
                    reply = response_for_language(
                        lang,
                        f"Rescheduled successfully. New time is {appt['start_time']} with Dr. Rao.",
                        f"रीशेड्यूल सफल रहा। नया समय {appt['start_time']} है, डॉ. राव के साथ।",
                        f"மாற்றம் வெற்றிகரமாக முடிந்தது. புதிய நேரம் {appt['start_time']}, Dr. Rao உடன்.",
                    )
                except HTTPException as exc:
                    detail = _extract_http_detail(exc)
                    trace.append(f"reschedule:error:{detail}")
                    if "slot_conflict" in detail:
                        reply = response_for_language(
                            lang,
                            "That new slot is not available. Please share another preferred time.",
                            "वह नया स्लॉट उपलब्ध नहीं है। कृपया दूसरा समय बताएं।",
                            "அந்த புதிய நேரம் இல்லை. வேறு நேரம் சொல்லுங்கள்.",
                        )
                    elif "appointment_not_found" in detail:
                        pending_fields["appointment_id"] = ""
                        reply = response_for_language(
                            lang,
                            "I could not find that appointment ID. Please re-check and share it again.",
                            "वह अपॉइंटमेंट आईडी नहीं मिली। कृपया फिर से जांचकर बताएं।",
                            "அந்த appointment ID கிடைக்கவில்லை. தயவுசெய்து மீண்டும் சரிபார்த்து சொல்லுங்கள்.",
                        )
                    else:
                        reply = response_for_language(
                            lang,
                            "I hit an issue while rescheduling. Please try once more.",
                            "रीशेड्यूल करते समय समस्या आई। कृपया एक बार फिर कोशिश करें।",
                            "மாற்றும் போது சிக்கல் ஏற்பட்டது. இன்னொரு முறை முயற்சிக்கவும்.",
                        )
        elif intent == Intent.CANCEL:
            if not appointment_id:
                pending_fields["appointment_id"] = ""
                trace.append("cancel:ask_appointment_id")
                reply = response_for_language(
                    lang,
                    "Please share your appointment ID and I will cancel it.",
                    "कृपया अपनी अपॉइंटमेंट आईडी बताएं, मैं रद्द कर दूँगा।",
                    "உங்கள் appointment ID கொடுக்கவும், நான் ரத்து செய்கிறேன்.",
                )
            else:
                try:
                    result = post_json(f"{SCHEDULER_URL}/cancel/{appointment_id}", {})
                    trace.append("cancel:success")
                    appt = result["appointment"]
                    reply = response_for_language(
                        lang,
                        f"Your appointment {appt['appointment_id']} has been canceled.",
                        f"आपकी अपॉइंटमेंट {appt['appointment_id']} रद्द कर दी गई है।",
                        f"உங்கள் appointment {appt['appointment_id']} ரத்து செய்யப்பட்டது.",
                    )
                except HTTPException as exc:
                    detail = _extract_http_detail(exc)
                    trace.append(f"cancel:error:{detail}")
                    pending_fields["appointment_id"] = ""
                    reply = response_for_language(
                        lang,
                        "I could not find that appointment ID. Please share it again.",
                        "वह अपॉइंटमेंट आईडी नहीं मिली। कृपया फिर से बताएं।",
                        "அந்த appointment ID கிடைக்கவில்லை. மீண்டும் சொல்லுங்கள்.",
                    )
        else:
            reply = response_for_language(
                lang,
                "I can help with booking, rescheduling, or cancellation.",
                "मैं बुकिंग, रीशेड्यूल और कैंसिलेशन में मदद कर सकता हूँ।",
                "முன்பதிவு, மாற்றம், ரத்து செய்வதில் உதவ முடியும்.",
            )

    with tracker.span("memory_write"):
        memory_intent = intent.value if intent != Intent.UNKNOWN else session.get("intent")
        post_json(
            f"{MEMORY_URL}/session",
            {
                "call_id": payload.call_id,
                "intent": memory_intent,
                "pending_fields": pending_fields,
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
