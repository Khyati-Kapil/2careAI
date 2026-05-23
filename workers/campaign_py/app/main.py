from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib import request


AGENT_URL = "http://127.0.0.1:8000/turn"
OUTCOME_LOG = Path("/Users/khyati/2careAI/workers/campaign_py/outbound_outcomes.jsonl")


@dataclass
class CampaignJob:
    job_id: str
    patient_id: str
    utterance: str
    campaign_type: str
    preferred_language: str | None = None
    max_retries: int = 2
    attempts: int = 0
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def classify_outcome(utterance: str, result: dict | None) -> str:
    lower = utterance.lower()
    if any(x in lower for x in ["not now", "no thanks", "नहीं", "வேண்டாம்"]):
        return "politely_declined"
    intent = (result or {}).get("intent")
    if intent == "book":
        return "booked_or_booking_flow"
    if intent == "reschedule":
        return "reschedule_flow"
    if intent == "cancel":
        return "cancel_flow"
    return "informational"


def trigger_outbound(job: CampaignJob) -> dict:
    payload = {
        "call_id": f"outbound-{job.job_id}",
        "patient_id": job.patient_id,
        "utterance": job.utterance,
        "language_hint": job.preferred_language,
    }
    req = request.Request(
        AGENT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def append_outcome(job: CampaignJob, result: dict | None, error_msg: str | None = None) -> None:
    OUTCOME_LOG.parent.mkdir(parents=True, exist_ok=True)
    outcome = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "job": asdict(job),
        "outcome_type": classify_outcome(job.utterance, result),
        "result": result,
        "error": error_msg,
    }
    with OUTCOME_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(outcome, ensure_ascii=False) + "\n")


def run_queue(jobs: list[CampaignJob]) -> None:
    pending = list(jobs)
    while pending:
        job = pending.pop(0)
        try:
            job.attempts += 1
            job.status = "running"
            result = trigger_outbound(job)
            job.status = "completed"
            append_outcome(job, result)
            print(f"completed job={job.job_id} attempts={job.attempts} intent={result.get('intent')}")
        except Exception as exc:  # pragma: no cover
            if job.attempts <= job.max_retries:
                job.status = "retrying"
                pending.append(job)
                print(f"retry job={job.job_id} attempt={job.attempts} error={exc}")
                time.sleep(0.2)
            else:
                job.status = "failed"
                append_outcome(job, None, str(exc))
                print(f"failed job={job.job_id} attempts={job.attempts} error={exc}")


if __name__ == "__main__":
    jobs = [
        CampaignJob(
            job_id="cmp-001",
            patient_id="pat-101",
            utterance="Reminder: your appointment is tomorrow morning. Reply to reschedule if needed.",
            campaign_type="reminder",
            preferred_language="en",
        ),
        CampaignJob(
            job_id="cmp-002",
            patient_id="pat-102",
            utterance="कल की appointment confirm करनी है या change करनी है?",
            campaign_type="followup",
            preferred_language="hi",
        ),
    ]
    run_queue(jobs)
