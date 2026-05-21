import express from "express";
import { randomUUID } from "crypto";

const app = express();
app.use(express.json());

const AGENT_URL = "http://127.0.0.1:8000";

type TurnPayload = {
  patientId: string;
  utterance: string;
  callId?: string;
  languageHint?: "en" | "hi" | "ta";
};

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.post("/voice/turn", async (req, res) => {
  const body = req.body as TurnPayload;
  const callId = body.callId ?? `call-${randomUUID().slice(0, 8)}`;
  const startedAt = performance.now();

  const response = await fetch(`${AGENT_URL}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      call_id: callId,
      patient_id: body.patientId,
      utterance: body.utterance,
      language_hint: body.languageHint ?? null
    })
  });

  const payload = await response.json();
  const gatewayMs = Number((performance.now() - startedAt).toFixed(2));

  res.json({
    callId,
    textResponse: payload.response_text,
    language: payload.language,
    intent: payload.intent,
    trace: payload.tool_trace,
    latencyMs: {
      ...payload.latency_ms,
      gateway: gatewayMs,
      e2e_estimated: Number((payload.latency_ms.total + gatewayMs).toFixed(2))
    }
  });
});

app.listen(3000, () => {
  console.log("voice-gateway listening on :3000");
});
