from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta, timezone
from urllib import error, request
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from shared.latency import LatencyTracker
from shared.models import AgentTurnRequest, AgentTurnResponse, Intent, Language

app = FastAPI(title="agent-service")

SCHEDULER_URL = "http://127.0.0.1:8001"
MEMORY_URL = "http://127.0.0.1:8002"

APPOINTMENT_ID_RE = re.compile(r"\bapt-[a-zA-Z0-9]{4,}\b", re.IGNORECASE)
TRACE_STORE: list[dict] = []
MAX_TRACE_ITEMS = 300


LANG_SWITCH_PATTERNS: dict[Language, tuple[str, ...]] = {
    Language.EN: ("english", "speak english", "switch to english"),
    Language.HI: ("hindi", "हिंदी", "हिन्दी", "switch to hindi"),
    Language.TA: ("tamil", "தமிழ்", "switch to tamil"),
}
DOCTOR_LABELS = {"doc-1": "Dr. Rao", "doc-2": "Dr. Mehta"}


def post_json(url: str, payload: dict, correlation_id: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if correlation_id:
        headers["x-correlation-id"] = correlation_id
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=1.5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise HTTPException(status_code=exc.code, detail=detail) from exc


def get_json(url: str, correlation_id: str | None = None) -> dict:
    headers = {}
    if correlation_id:
        headers["x-correlation-id"] = correlation_id
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=1.5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def detect_language(text: str, hint: Language | None, preferred: str | None) -> Language:
    if hint:
        return hint
    lower = text.lower()
    if re.search(r"[\u0B80-\u0BFF]", text):
        return Language.TA
    if re.search(r"[\u0900-\u097F]", text):
        return Language.HI
    # Strong English fallback: if text is mostly ASCII words (including times like 3:00), keep English.
    if re.fullmatch(r"[a-z0-9 ,.!?':/-]+", lower or ""):
        return Language.EN
    ascii_words = re.findall(r"[a-z]+", lower)
    if len(ascii_words) >= 3 and not re.search(r"[\u0B80-\u0BFF\u0900-\u097F]", text):
        return Language.EN
    if any(w in lower for w in ["vanakkam", "naalai"]):
        return Language.TA
    if any(w in lower for w in ["kal", "namaste"]):
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


def detect_polite_rejection(text: str) -> bool:
    lower = text.lower()
    phrases = ["not now", "no thanks", "can't", "cannot", "nahi", "नहीं", "வேண்டாம்", "later"]
    return any(p in lower for p in phrases)


def detect_language_switch(text: str) -> Language | None:
    lower = text.lower()
    for lang, patterns in LANG_SWITCH_PATTERNS.items():
        if any(p in lower for p in patterns):
            return lang
    return None


def extract_appointment_id(text: str) -> str | None:
    match = APPOINTMENT_ID_RE.search(text)
    if not match:
        return None
    return match.group(0).lower()


def parse_requested_start(text: str) -> datetime:
    lower = text.lower()
    base = datetime.now(timezone.utc)
    if any(w in lower for w in ["yesterday", "kal raat", "நேற்று"]):
        day_offset = -1
    elif "day after tomorrow" in lower:
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
        if day_offset < 0:
            return start
        start = base + timedelta(hours=2)
    return start


def extract_option_index(text: str) -> int | None:
    m = re.search(r"\b([1-3])\b", text)
    if not m:
        return None
    return int(m.group(1)) - 1


def detect_doctor(text: str) -> str:
    lower = text.lower()
    if "mehta" in lower:
        return "doc-2"
    if "rao" in lower:
        return "doc-1"
    if "unknown doctor" in lower:
        return "doc-99"
    return "doc-1"


def doctor_label(doctor_id: str) -> str:
    return DOCTOR_LABELS.get(doctor_id, doctor_id)


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


def _alternatives_text(alternatives: list[dict], lang: Language) -> str:
    if not alternatives:
        return response_for_language(
            lang,
            "Please share another preferred time.",
            "कृपया कोई दूसरा समय बताएं।",
            "தயவுசெய்து வேறு நேரம் சொல்லுங்கள்.",
        )
    options = [f"{idx + 1}) {item['start_time']}" for idx, item in enumerate(alternatives[:3])]
    joined = " | ".join(options)
    return response_for_language(
        lang,
        f"Available alternatives: {joined}. Reply with option number.",
        f"उपलब्ध विकल्प: {joined}. कृपया विकल्प संख्या बताएं।",
        f"கிடைக்கும் மாற்று நேரங்கள்: {joined}. எண் தெரிவுசெய்யுங்கள்.",
    )


def _get_selected_alternative(session: dict, text: str) -> dict | None:
    option_index = extract_option_index(text)
    if option_index is None:
        return None
    pending = session.get("pending_fields", {}).get("alternatives_json")
    if not pending:
        return None
    try:
        options = json.loads(pending)
        if 0 <= option_index < len(options):
            return options[option_index]
    except json.JSONDecodeError:
        return None
    return None


def _push_trace(trace_item: dict) -> None:
    TRACE_STORE.append(trace_item)
    if len(TRACE_STORE) > MAX_TRACE_ITEMS:
        del TRACE_STORE[0 : len(TRACE_STORE) - MAX_TRACE_ITEMS]


def _call_tool(
    trace: list[str],
    tool_audit: list[dict],
    tool_name: str,
    fn,
):
    started = time.perf_counter()
    try:
        result = fn()
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        tool_audit.append({"tool": tool_name, "status": "ok", "latency_ms": elapsed})
        trace.append(f"{tool_name}:ok:{elapsed}ms")
        return result
    except Exception as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        tool_audit.append({"tool": tool_name, "status": "error", "latency_ms": elapsed, "error": str(exc)})
        trace.append(f"{tool_name}:error:{elapsed}ms")
        raise


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "trace_items": str(len(TRACE_STORE))}


@app.get("/traces")
def get_traces(limit: int = 50) -> dict:
    clipped = TRACE_STORE[-max(1, min(limit, 200)) :]
    return {"count": len(clipped), "items": clipped}


@app.get("/traces/{call_id}")
def get_call_traces(call_id: str) -> dict:
    items = [t for t in TRACE_STORE if t.get("call_id") == call_id]
    return {"count": len(items), "items": items}


@app.post("/turn", response_model=AgentTurnResponse)
def turn(payload: AgentTurnRequest, req: Request) -> AgentTurnResponse:
    tracker = LatencyTracker()
    trace: list[str] = []
    tool_audit: list[dict] = []
    correlation_id = req.headers.get("x-correlation-id", f"corr-{uuid4().hex[:8]}")

    with tracker.span("memory_read"):
        patient = _call_tool(
            trace,
            tool_audit,
            "memory.get_patient",
            lambda: get_json(f"{MEMORY_URL}/patient/{payload.patient_id}", correlation_id),
        )
        session = _call_tool(
            trace,
            tool_audit,
            "memory.get_session",
            lambda: get_json(f"{MEMORY_URL}/session/{payload.call_id}", correlation_id),
        )

    with tracker.span("nlu"):
        forced_lang = detect_language_switch(payload.utterance)
        intent = detect_intent(payload.utterance)
        if intent == Intent.UNKNOWN and session.get("intent") in {"reschedule", "cancel"}:
            intent = Intent(session.get("intent"))
        lang = detect_language(payload.utterance, payload.language_hint, patient.get("preferred_language"))
        if forced_lang:
            lang = forced_lang
            trace.append(f"language_switch:{lang.value}")
        appointment_id = extract_appointment_id(payload.utterance) or session.get("pending_fields", {}).get("appointment_id")

    reply = ""
    conversation_state = session.get("conversation_state", "idle")
    pending_confirmation = session.get("pending_confirmation")
    pending_fields: dict[str, str] = {}
    with tracker.span("orchestration"):
        selected_alt = _get_selected_alternative(session, payload.utterance)
        if selected_alt and session.get("intent") in {"book", "reschedule"}:
            intent = Intent(session.get("intent"))
            start = datetime.fromisoformat(selected_alt["start_time"].replace("Z", "+00:00"))
            selected_doctor = selected_alt.get("doctor_id", "doc-1")
            if intent == Intent.BOOK:
                booking = _call_tool(
                    trace,
                    tool_audit,
                    "scheduler.book",
                    lambda: post_json(
                        f"{SCHEDULER_URL}/book",
                        {
                            "patient_id": payload.patient_id,
                            "doctor_id": selected_doctor,
                            "start_time": start.isoformat(),
                            "duration_minutes": 30,
                        },
                        correlation_id,
                    ),
                )
                appt_id = booking["appointment"]["appointment_id"]
                reply = response_for_language(
                    lang,
                    f"Confirmed. Your appointment is booked with {doctor_label(selected_doctor)}. ID: {appt_id}",
                    f"कन्फर्म हो गया। आपकी अपॉइंटमेंट {doctor_label(selected_doctor)} के साथ बुक हो गई है। आईडी: {appt_id}",
                    f"உறுதி செய்யப்பட்டது. உங்கள் appointment {doctor_label(selected_doctor)} உடன் பதிவு செய்யப்பட்டது. ஐடி: {appt_id}",
                )
            else:
                result = _call_tool(
                    trace,
                    tool_audit,
                    "scheduler.reschedule",
                    lambda: post_json(
                        f"{SCHEDULER_URL}/reschedule",
                        {
                            "appointment_id": appointment_id,
                            "doctor_id": selected_doctor,
                            "start_time": start.isoformat(),
                            "duration_minutes": 30,
                        },
                        correlation_id,
                    ),
                )
                reply = response_for_language(
                    lang,
                    f"Confirmed. Rescheduled to {result['appointment']['start_time']} with {doctor_label(selected_doctor)}.",
                    f"कन्फर्म हो गया। नया समय {result['appointment']['start_time']} है, {doctor_label(selected_doctor)} के साथ।",
                    f"உறுதி செய்யப்பட்டது. புதிய நேரம் {result['appointment']['start_time']}, {doctor_label(selected_doctor)} உடன்.",
                )
            pending_fields["alternatives_json"] = ""
            conversation_state = "completed"
            pending_confirmation = None
        elif trace and trace[0].startswith("language_switch") and intent == Intent.UNKNOWN:
            reply = response_for_language(
                lang,
                "Language switched. I can help with booking, rescheduling, or cancellation.",
                "भाषा बदल दी गई है। मैं बुकिंग, रीशेड्यूल या कैंसिलेशन में मदद कर सकता हूँ।",
                "மொழி மாற்றப்பட்டது. முன்பதிவு, மாற்றம், ரத்து உதவி செய்யலாம்.",
            )
        elif detect_polite_rejection(payload.utterance):
            conversation_state = "closed_by_patient"
            pending_confirmation = None
            reply = response_for_language(
                lang,
                "Understood. I will not make any changes right now. Let me know when you want to continue.",
                "समझ गया। अभी कोई बदलाव नहीं करूंगा। जब चाहें तब बताइए।",
                "புரிந்தது. இப்போது எந்த மாற்றமும் செய்யமாட்டேன். தொடர வேண்டுமெனில் சொல்லுங்கள்.",
            )
        elif intent == Intent.BOOK:
            doctor_id = detect_doctor(payload.utterance)
            start = parse_requested_start(payload.utterance)
            end = start + timedelta(minutes=30)
            availability = _call_tool(
                trace,
                tool_audit,
                "scheduler.check_availability",
                lambda: post_json(
                    f"{SCHEDULER_URL}/check_availability",
                    {
                        "doctor_id": doctor_id,
                        "start_time": start.isoformat(),
                        "end_time": end.isoformat(),
                    },
                    correlation_id,
                ),
            )
            trace.append(f"check_availability:{availability.get('reason')}")
            if availability.get("available"):
                booking = _call_tool(
                    trace,
                    tool_audit,
                    "scheduler.book",
                    lambda: post_json(
                        f"{SCHEDULER_URL}/book",
                        {
                            "patient_id": payload.patient_id,
                            "doctor_id": doctor_id,
                            "start_time": start.isoformat(),
                            "duration_minutes": 30,
                        },
                        correlation_id,
                    ),
                )
                trace.append("book:success")
                appt_id = booking["appointment"]["appointment_id"]
                reply = response_for_language(
                    lang,
                    f"Your appointment is confirmed with {doctor_label(doctor_id)}. ID: {appt_id}",
                    f"आपकी अपॉइंटमेंट {doctor_label(doctor_id)} के साथ कन्फर्म हो गई है। आईडी: {appt_id}",
                    f"உங்கள் முன்பதிவு {doctor_label(doctor_id)} உடன் உறுதி செய்யப்பட்டது. ஐடி: {appt_id}",
                )
                conversation_state = "completed"
                pending_confirmation = None
            else:
                trace.append("book:conflict")
                reply = _alternatives_text(availability.get("alternatives", []), lang)
                pending_fields["alternatives_json"] = json.dumps(availability.get("alternatives", [])[:3])
                conversation_state = "awaiting_slot_confirmation"
                pending_confirmation = "slot_option"
        elif intent == Intent.RESCHEDULE:
            if not appointment_id:
                pending_fields["appointment_id"] = ""
                conversation_state = "awaiting_appointment_id"
                trace.append("reschedule:ask_appointment_id")
                reply = response_for_language(
                    lang,
                    "Please share your appointment ID and preferred new time.",
                    "कृपया अपनी अपॉइंटमेंट आईडी और नया समय बताएं।",
                    "தயவுசெய்து உங்கள் appointment ID மற்றும் புதிய நேரத்தை சொல்லுங்கள்.",
                )
            else:
                start = parse_requested_start(payload.utterance)
                doctor_id = detect_doctor(payload.utterance)
                try:
                    result = _call_tool(
                        trace,
                        tool_audit,
                        "scheduler.reschedule",
                        lambda: post_json(
                            f"{SCHEDULER_URL}/reschedule",
                            {
                                "appointment_id": appointment_id,
                                "doctor_id": doctor_id,
                                "start_time": start.isoformat(),
                                "duration_minutes": 30,
                            },
                            correlation_id,
                        ),
                    )
                    trace.append("reschedule:success")
                    appt = result["appointment"]
                    reply = response_for_language(
                        lang,
                        f"Rescheduled successfully. New time is {appt['start_time']} with {doctor_label(doctor_id)}.",
                        f"रीशेड्यूल सफल रहा। नया समय {appt['start_time']} है, {doctor_label(doctor_id)} के साथ।",
                        f"மாற்றம் வெற்றிகரமாக முடிந்தது. புதிய நேரம் {appt['start_time']}, {doctor_label(doctor_id)} உடன்.",
                    )
                    conversation_state = "completed"
                    pending_confirmation = None
                except HTTPException as exc:
                    detail = _extract_http_detail(exc)
                    trace.append(f"reschedule:error:{detail}")
                    if "slot_conflict" in detail:
                        pending_fields["appointment_id"] = appointment_id
                        q = {
                            "doctor_id": doctor_id,
                            "start_time": start.isoformat(),
                            "end_time": (start + timedelta(minutes=30)).isoformat(),
                        }
                        availability = _call_tool(
                            trace,
                            tool_audit,
                            "scheduler.check_availability",
                            lambda: post_json(f"{SCHEDULER_URL}/check_availability", q, correlation_id),
                        )
                        reply = _alternatives_text(availability.get("alternatives", []), lang)
                        pending_fields["alternatives_json"] = json.dumps(availability.get("alternatives", [])[:3])
                        conversation_state = "awaiting_slot_confirmation"
                        pending_confirmation = "slot_option"
                    elif "appointment_not_found" in detail:
                        pending_fields["appointment_id"] = ""
                        conversation_state = "awaiting_appointment_id"
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
                conversation_state = "awaiting_appointment_id"
                trace.append("cancel:ask_appointment_id")
                reply = response_for_language(
                    lang,
                    "Please share your appointment ID and I will cancel it.",
                    "कृपया अपनी अपॉइंटमेंट आईडी बताएं, मैं रद्द कर दूँगा।",
                    "உங்கள் appointment ID கொடுக்கவும், நான் ரத்து செய்கிறேன்.",
                )
            else:
                try:
                    result = _call_tool(
                        trace,
                        tool_audit,
                        "scheduler.cancel",
                        lambda: post_json(f"{SCHEDULER_URL}/cancel/{appointment_id}", {}, correlation_id),
                    )
                    trace.append("cancel:success")
                    appt = result["appointment"]
                    reply = response_for_language(
                        lang,
                        f"Your appointment {appt['appointment_id']} has been canceled.",
                        f"आपकी अपॉइंटमेंट {appt['appointment_id']} रद्द कर दी गई है।",
                        f"உங்கள் appointment {appt['appointment_id']} ரத்து செய்யப்பட்டது.",
                    )
                    conversation_state = "completed"
                    pending_confirmation = None
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
            conversation_state = "awaiting_intent"

    with tracker.span("memory_write"):
        memory_intent = intent.value if intent != Intent.UNKNOWN else session.get("intent")
        session_upsert_result = _call_tool(
            trace,
            tool_audit,
            "memory.upsert_session",
            lambda: post_json(
                f"{MEMORY_URL}/session",
                {
                    "call_id": payload.call_id,
                    "intent": memory_intent,
                    "pending_fields": pending_fields,
                    "conversation_state": conversation_state,
                    "pending_confirmation": pending_confirmation,
                    "language": lang.value,
                },
                correlation_id,
            ),
        )
        _call_tool(
            trace,
            tool_audit,
            "memory.upsert_patient",
            lambda: post_json(
                f"{MEMORY_URL}/patient",
                {
                    "patient_id": payload.patient_id,
                    "preferred_language": lang.value,
                    "note": f"intent={intent.value};ts={int(time.time())}",
                },
                correlation_id,
            ),
        )

    response = AgentTurnResponse(
        call_id=payload.call_id,
        language=lang,
        intent=intent,
        response_text=reply,
        tool_trace=trace,
        latency_ms={**tracker.data, "total": tracker.total()},
    )
    _push_trace(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "call_id": payload.call_id,
            "correlation_id": correlation_id,
            "patient_id": payload.patient_id,
            "utterance": payload.utterance,
            "intent": intent.value,
            "language": lang.value,
            "tool_trace": trace,
            "tool_audit": tool_audit,
            "memory_summary": {
                "preferred_language": patient.get("preferred_language"),
                "session_intent": session.get("intent"),
                "pending_fields": session.get("pending_fields", {}),
            },
            "latency_ms": response.latency_ms,
            "reply": response.response_text,
        }
    )
    return response
