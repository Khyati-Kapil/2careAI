from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass
from urllib import request


@dataclass
class SampleResult:
    e2e_ms: float
    gateway_ms: float
    agent_total_ms: float


def post_turn(payload: dict) -> dict:
    req = request.Request(
        "http://127.0.0.1:3000/voice/turn",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def pct(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    idx = max(0, min(len(values) - 1, int((p / 100) * (len(values) - 1))))
    sorted_vals = sorted(values)
    return round(sorted_vals[idx], 2)


def run(samples: int = 20) -> None:
    results: list[SampleResult] = []
    for i in range(samples):
        payload = {
            "patientId": "pat-bench-001",
            "callId": "call-bench-001",
            "utterance": "I want to book an appointment tomorrow morning",
            "languageHint": "en",
        }
        start = time.perf_counter()
        body = post_turn(payload)
        wall_ms = round((time.perf_counter() - start) * 1000, 2)
        latency = body.get("latencyMs", {})
        results.append(
            SampleResult(
                e2e_ms=wall_ms,
                gateway_ms=float(latency.get("gateway", 0)),
                agent_total_ms=float(latency.get("total", 0)),
            )
        )
        print(f"sample={i+1} e2e={wall_ms}ms intent={body.get('intent')} lang={body.get('language')}")

    e2e = [r.e2e_ms for r in results]
    gateway = [r.gateway_ms for r in results]
    agent = [r.agent_total_ms for r in results]

    print("\n=== Latency Summary (ms) ===")
    print(f"samples: {len(results)}")
    print(f"e2e  p50={pct(e2e, 50)} p95={pct(e2e, 95)} p99={pct(e2e, 99)} avg={round(statistics.mean(e2e), 2)}")
    print(f"gateway p50={pct(gateway, 50)} p95={pct(gateway, 95)}")
    print(f"agent   p50={pct(agent, 50)} p95={pct(agent, 95)}")


if __name__ == "__main__":
    run(samples=20)
