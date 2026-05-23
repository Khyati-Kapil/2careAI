# Latency Report

Date: 2026-05-23
Environment: local (loopback)

## Method
- Start scheduler, memory, agent, and gateway services.
- Run:
  - `python benchmarks/latency_benchmark.py`
- Capture p50/p95/p99 from output.

## Results
- e2e p50: TODO ms
- e2e p95: TODO ms
- e2e p99: TODO ms
- gateway p50: TODO ms
- agent p50: TODO ms

## Interpretation
- Target is `<450ms` speech-end to first audio response.
- Current benchmark measures text-turn e2e over local HTTP.
- For production-equivalent measurement, replace simulated stream chunking with real streaming ASR + TTS first-byte timing.

## Follow-up Optimization Plan
1. ASR partial hypothesis prefetch to reduce planning wait.
2. Keep warm tool connections and Redis pooling.
3. Stream TTS on first clause, not full sentence.
4. Prioritize short confirmation templates for yes/no turns.
