from shared.models import Intent
from shared.models import Language
from services.agent_py.app.main import (
    _alternatives_text,
    detect_intent,
    detect_language_switch,
    extract_appointment_id,
    parse_requested_start,
)


def test_extract_appointment_id() -> None:
    assert extract_appointment_id("please cancel apt-1a2b3c") == "apt-1a2b3c"
    assert extract_appointment_id("no id here") is None


def test_detect_intent_multilingual() -> None:
    assert detect_intent("मुझे appointment बुक करनी है") == Intent.BOOK
    assert detect_intent("please cancel my appointment") == Intent.CANCEL
    assert detect_intent("reschedule this") == Intent.RESCHEDULE


def test_parse_requested_start_future() -> None:
    dt = parse_requested_start("tomorrow morning")
    assert dt is not None


def test_language_switch_detection() -> None:
    assert detect_language_switch("switch to hindi please") == Language.HI
    assert detect_language_switch("தமிழ் பேசலாம்") == Language.TA
    assert detect_language_switch("no switch command") is None


def test_alternatives_text() -> None:
    msg = _alternatives_text([{"start_time": "2026-05-24T10:00:00+00:00"}], Language.EN)
    assert "1)" in msg
