from datetime import datetime, timedelta, timezone

from services.scheduler_py.app.main import APPOINTMENTS, _is_conflicting


def test_conflict_check() -> None:
    APPOINTMENTS.clear()
    now = datetime.now(timezone.utc) + timedelta(hours=3)
    start = now.replace(second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    assert _is_conflicting("doc-1", start, end) is False
