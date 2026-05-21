from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request


@dataclass
class CampaignTarget:
    patient_id: str
    utterance: str


AGENT_URL = "http://127.0.0.1:8000/turn"


def trigger_outbound(target: CampaignTarget) -> dict:
    payload = {
        "call_id": f"outbound-{target.patient_id}",
        "patient_id": target.patient_id,
        "utterance": target.utterance,
    }
    req = request.Request(
        AGENT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=2.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    targets = [
        CampaignTarget(patient_id="pat-101", utterance="Reminder: you can reschedule if needed"),
        CampaignTarget(patient_id="pat-102", utterance="कल की appointment confirm करनी है"),
    ]
    for target in targets:
        result = trigger_outbound(target)
        print(target.patient_id, result["language"], result["intent"], result["response_text"])
