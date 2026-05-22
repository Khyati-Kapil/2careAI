from shared.models import Intent
from services.agent_py.app.main import detect_intent, extract_appointment_id, parse_requested_start


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
