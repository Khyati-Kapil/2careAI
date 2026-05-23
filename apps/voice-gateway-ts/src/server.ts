import express from "express";
import { randomUUID } from "crypto";

const app = express();
app.use(express.json());

const AGENT_URL = "http://127.0.0.1:8000";
const IDENTITY_URL = "http://127.0.0.1:8003";

type TurnPayload = {
  patientId?: string;
  callerNumber?: string;
  utterance: string;
  callId?: string;
  languageHint?: "en" | "hi" | "ta";
};

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.get("/demo", (_req, res) => {
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.send(`<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>2careAI - Real-Time Multilingual Voice AI Agent</title>
    <!-- Premium Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
      :root {
        --bg-main: #070913;
        --bg-card: rgba(15, 18, 36, 0.6);
        --border-glass: rgba(255, 255, 255, 0.08);
        --border-glass-glow: rgba(99, 102, 241, 0.25);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --color-accent: #6366f1;
        --color-cyan: #06b6d4;
        --color-emerald: #10b981;
        --color-rose: #f43f5e;
        --color-amber: #f59e0b;
      }
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: radial-gradient(ellipse at top, #0f122c, #070913);
        color: var(--text-primary);
        min-height: 100vh;
        padding: 40px 24px;
        line-height: 1.5;
        overflow-x: hidden;
      }
      .container {
        max-width: 1200px;
        margin: 0 auto;
      }
      header {
        text-align: center;
        margin-bottom: 40px;
        animation: fadeIn 0.8s ease-out;
      }
      h1 {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff 30%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
        display: inline-flex;
        align-items: center;
        gap: 12px;
      }
      .badge-live {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.15));
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: var(--color-emerald);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 9999px;
        letter-spacing: 0.1em;
        display: inline-block;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
        vertical-align: middle;
      }
      .tagline {
        color: var(--text-secondary);
        font-size: 1.1rem;
        max-width: 600px;
        margin: 0 auto;
        font-weight: 300;
      }
      .grid-layout {
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        gap: 24px;
        margin-top: 30px;
      }
      @media (max-width: 1024px) {
        .grid-layout { grid-template-columns: 1fr; }
      }
      .card {
        background: var(--bg-card);
        border: 1px solid var(--border-glass);
        border-radius: 20px;
        padding: 24px;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
      }
      .card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
      }
      .card:hover {
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 25px 50px rgba(99, 102, 241, 0.05);
      }
      .section-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 20px;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        padding-bottom: 12px;
      }
      .form-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 20px;
      }
      @media (max-width: 640px) {
        .form-grid { grid-template-columns: 1fr; }
      }
      .form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .form-group.full-width {
        grid-column: span 2;
      }
      @media (max-width: 640px) {
        .form-group.full-width { grid-column: span 1; }
      }
      label {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      input, select, textarea {
        background: rgba(7, 9, 20, 0.8);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        color: var(--text-primary);
        font-size: 14px;
        padding: 12px 16px;
        outline: none;
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
        width: 100%;
      }
      input:focus, select:focus, textarea:focus {
        border-color: var(--color-accent);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        background: rgba(7, 9, 20, 0.95);
      }
      .btn-container {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 20px;
      }
      button {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        padding: 12px 20px;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
      button:active {
        transform: scale(0.98);
      }
      .btn-primary {
        background: linear-gradient(135deg, var(--color-accent) 0%, #4f46e5 100%);
        color: #fff;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
      }
      .btn-primary:hover {
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        border-color: rgba(255,255,255,0.2);
      }
      .btn-secondary {
        background: rgba(255,255,255,0.06);
        border-color: var(--border-glass);
        color: var(--text-primary);
      }
      .btn-secondary:hover {
        background: rgba(255,255,255,0.12);
        border-color: rgba(255,255,255,0.2);
      }
      .btn-accent {
        background: linear-gradient(135deg, var(--color-cyan) 0%, #0891b2 100%);
        color: #fff;
        box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3);
      }
      .btn-accent:hover {
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5);
      }
      .btn-danger {
        background: rgba(244, 63, 94, 0.1);
        border: 1px solid rgba(244, 63, 94, 0.3);
        color: var(--color-rose);
      }
      .btn-danger:hover {
        background: rgba(244, 63, 94, 0.2);
      }
      .mic-control-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(6, 182, 212, 0.04) 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
      }
      .mic-info {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .mic-status-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
      }
      .mic-status-text {
        font-family: 'Outfit', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
      }
      .mic-status-text.active {
        color: var(--color-cyan);
      }
      .wave-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        height: 36px;
        width: 100px;
        background: rgba(7, 9, 20, 0.4);
        border-radius: 20px;
        padding: 0 10px;
        border: 1px solid var(--border-glass);
      }
      .wave-bar {
        width: 4px;
        height: 8px;
        background: linear-gradient(to top, var(--color-accent), var(--color-cyan));
        border-radius: 2px;
        transition: all 0.2s ease;
      }
      .wave-container.active .wave-bar {
        animation: wave 1.2s ease-in-out infinite;
      }
      .wave-container.active .wave-bar:nth-child(1) { animation-delay: 0.0s; }
      .wave-container.active .wave-bar:nth-child(2) { animation-delay: 0.15s; }
      .wave-container.active .wave-bar:nth-child(3) { animation-delay: 0.3s; }
      .wave-container.active .wave-bar:nth-child(4) { animation-delay: 0.45s; }
      .wave-container.active .wave-bar:nth-child(5) { animation-delay: 0.3s; }
      .wave-container.active .wave-bar:nth-child(6) { animation-delay: 0.15s; }
      @keyframes wave {
        0%, 100% { height: 6px; }
        50% { height: 26px; }
      }
      .preset-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 10px;
      }
      @media (max-width: 640px) {
        .preset-grid { grid-template-columns: 1fr; }
      }
      .preset-card {
        background: rgba(7, 9, 20, 0.4);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
      }
      .preset-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        background: rgba(99, 102, 241, 0.04);
        transform: translateY(-2px);
      }
      .preset-title {
        font-size: 13px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 4px;
      }
      .preset-desc {
        font-size: 11px;
        color: var(--text-muted);
        line-height: 1.3;
      }
      .right-column {
        display: flex;
        flex-direction: column;
        gap: 24px;
      }
      .telemetry-dashboard {
        display: flex;
        align-items: center;
        justify-content: space-around;
        background: rgba(7, 9, 20, 0.4);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        gap: 16px;
      }
      @media (max-width: 640px) {
        .telemetry-dashboard { flex-direction: column; }
      }
      .latency-gauge-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
      }
      .latency-gauge {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: radial-gradient(circle, #090a16 40%, transparent 42%), conic-gradient(var(--color-accent) var(--pct, 0%), #141830 0);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow: 0 0 24px rgba(99, 102, 241, 0.15);
        transition: all 0.5s ease;
      }
      .latency-value {
        font-family: 'Fira Code', monospace;
        font-size: 24px;
        font-weight: 700;
        color: #fff;
      }
      .latency-unit {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
      }
      .telemetry-breakdown {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        gap: 10px;
        width: 100%;
      }
      .breakdown-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .breakdown-colors {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .breakdown-name { color: var(--text-secondary); }
      .breakdown-val { font-family: 'Fira Code', monospace; color: #fff; }
      .bar-outer {
        height: 6px;
        background: rgba(255,255,255,0.05);
        border-radius: 9999px;
        overflow: hidden;
      }
      .bar-inner {
        height: 100%;
        width: 0%;
        border-radius: 9999px;
        background: var(--color-accent);
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      }
      pre {
        background: rgba(5, 7, 16, 0.9);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px;
        font-family: 'Fira Code', 'Courier New', monospace;
        font-size: 12px;
        color: #d1d5db;
        max-height: 280px;
        overflow-y: auto;
        white-space: pre-wrap;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.5);
      }
      .tab-container {
        display: flex;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 12px;
        gap: 8px;
      }
      .tab {
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        color: var(--text-muted);
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
      }
      .tab:hover {
        color: var(--text-primary);
      }
      .tab.active {
        color: var(--color-cyan);
        border-bottom-color: var(--color-cyan);
      }
      .response-card {
        border-color: rgba(16, 185, 129, 0.15);
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.04) 0%, rgba(15, 18, 36, 0.6) 100%);
      }
      .stream-card {
        border-color: rgba(6, 182, 212, 0.15);
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.04) 0%, rgba(15, 18, 36, 0.6) 100%);
      }
      .trace-timeline {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 12px;
        position: relative;
        padding-left: 20px;
      }
      .trace-timeline::before {
        content: '';
        position: absolute;
        left: 6px; top: 8px; bottom: 8px;
        width: 2px;
        background: rgba(255,255,255,0.05);
      }
      .trace-step {
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .trace-dot {
        position: absolute;
        left: -20px; top: 6px;
        width: 10px; height: 10px;
        border-radius: 50%;
        background: var(--text-muted);
        border: 2px solid #070913;
      }
      .trace-step.success .trace-dot { background: var(--color-emerald); box-shadow: 0 0 8px var(--color-emerald); }
      .trace-step.error .trace-dot { background: var(--color-rose); box-shadow: 0 0 8px var(--color-rose); }
      .trace-step.info .trace-dot { background: var(--color-accent); box-shadow: 0 0 8px var(--color-accent); }
      .trace-header {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        font-weight: 700;
        color: #fff;
      }
      .trace-elapsed {
        font-family: 'Fira Code', monospace;
        font-size: 11px;
        color: var(--text-secondary);
      }
      .trace-body {
        font-size: 12px;
        color: var(--text-secondary);
        background: rgba(0,0,0,0.2);
        padding: 6px 12px;
        border-radius: 6px;
        border-left: 2px solid rgba(255,255,255,0.05);
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .speak-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 500;
        color: var(--color-amber);
        margin-top: 10px;
      }
      .speak-indicator span {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--color-amber);
        animation: pulse 1s infinite alternate;
      }
      @keyframes pulse {
        from { opacity: 0.3; transform: scale(0.8); }
        to { opacity: 1; transform: scale(1.2); }
      }
      .check-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 12px;
        background: rgba(255,255,255,0.02);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.03);
        margin-bottom: 6px;
      }
      .check-name {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
      }
      .check-status {
        font-family: 'Fira Code', monospace;
        font-size: 11px;
        font-weight: 700;
      }
      .status-ok { color: var(--color-emerald); }
      .status-pending { color: var(--color-amber); }
    </style>
  </head>
  <body>
    <div class="container">
      <header>
        <h1>2careAI <span class="badge-live">Real-Time</span></h1>
        <p class="tagline">Clinical appointment booking voice agent operating with sub-450ms response latency across English, Hindi, and Tamil.</p>
      </header>

      <div class="grid-layout">
        <!-- LEFT COLUMN: INPUTS & CONTROLS -->
        <div class="left-column">
          <!-- Mic Control Card -->
          <div class="mic-control-card">
            <div class="mic-info">
              <span class="mic-status-label">SPEECH PIPELINE STATUS</span>
              <span id="micStatusText" class="mic-status-text">Mic is Idle</span>
            </div>
            <div id="micWave" class="wave-container">
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
            </div>
            <div style="display: flex; gap: 8px;">
              <button id="micStartBtn" class="btn-primary" style="padding: 10px 16px;">
                <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/></svg>
                Listen
              </button>
              <button id="micStopBtn" class="btn-secondary" style="padding: 10px 14px;">Stop</button>
            </div>
          </div>

          <!-- Configuration Panel -->
          <div class="card" style="margin-bottom: 24px;">
            <div class="section-title">
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
              Orchestrator Settings
            </div>
            <div class="form-grid">
              <div class="form-group">
                <label for="patientId">Patient ID</label>
                <input id="patientId" value="pat-101" placeholder="pat-101" />
              </div>
              <div class="form-group">
                <label for="callerNumber">Caller Number</label>
                <input id="callerNumber" value="+919900000001" placeholder="+919900000001" />
              </div>
              <div class="form-group">
                <label for="callId">Session Call ID</label>
                <input id="callId" value="call-ui-session" placeholder="call-ui-session" />
              </div>
              <div class="form-group">
                <label for="micLang">Speech Language Hint</label>
                <select id="micLang">
                  <option value="en-IN">English (India)</option>
                  <option value="hi-IN">Hindi (India)</option>
                  <option value="ta-IN" selected>Tamil (India)</option>
                </select>
              </div>
              <div class="form-group full-width">
                <label for="utterance">Input Utterance (Type or speak)</label>
                <textarea id="utterance" rows="2" placeholder="Tell me what you want to do...">முன்பதிவு செய்ய வேண்டும் (Book an appointment)</textarea>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <label style="display: inline-flex; align-items: center; gap: 8px; cursor: pointer;">
                <input id="speakOut" type="checkbox" checked style="width: auto;" />
                Enable Text-to-Speech Output
              </label>
              <button id="speechStopBtn" class="btn-danger" style="padding: 6px 12px; font-size: 11px;">Mute Audio</button>
            </div>

            <div class="btn-container">
              <button id="turnBtn" class="btn-primary">
                Send Turn Request
              </button>
              <button id="streamBtn" class="btn-accent">
                Send SSE Stream
              </button>
              <button id="traceBtn" class="btn-secondary">
                Inspect Traces
              </button>
            </div>
          </div>

          <!-- Scenario Presets -->
          <div class="card">
            <div class="section-title">
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
              Execution Presets
            </div>
            <p class="preset-desc" style="margin-bottom: 12px; font-size:12px;">Click any preset to simulate complex appointment workflows instantly:</p>
            <div class="preset-grid">
              <div id="demoBookBtn" class="preset-card">
                <div class="preset-title">1. Success Booking (EN)</div>
                <div class="preset-desc">Creates a successful booking with Dr. Rao for tomorrow morning.</div>
              </div>
              <div id="demoConflictBtn" class="preset-card">
                <div class="preset-title">2. Conflict & Suggest (HI)</div>
                <div class="preset-desc">Triggers overlap checks and returns 3 alternative time slots.</div>
              </div>
              <div id="demoSelectBtn" class="preset-card">
                <div class="preset-title">3. Pick Slot Alternative (TA)</div>
                <div class="preset-desc">Confirms alternative Slot 1 from past conflict memory.</div>
              </div>
              <div id="demoRescheduleBtn" class="preset-card">
                <div class="preset-title">4. Reschedule Cycle</div>
                <div class="preset-desc">Performs a multi-turn change of mind using appointment ID.</div>
              </div>
              <div id="demoCancelBtn" class="preset-card">
                <div class="preset-title">5. Cancellation Flow</div>
                <div class="preset-desc">Extracts appointment ID and cancels slot confirmation.</div>
              </div>
              <div id="demoOutboundBtn" class="preset-card">
                <div class="preset-title">6. Outbound Rejection</div>
                <div class="preset-desc">Initiates campaign response simulation and registers decline.</div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: TELEMETRY & TRACES -->
        <div class="right-column">
          <!-- Real-Time Telemetry Card -->
          <div class="card">
            <div class="section-title">
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              Real-Time Latency Dashboard
            </div>
            <div class="telemetry-dashboard">
              <div class="latency-gauge-wrapper">
                <div id="latencyGauge" class="latency-gauge">
                  <span id="latencyValue" class="latency-value">0</span>
                  <span class="latency-unit">ms</span>
                </div>
                <div id="latencyRating" style="font-size: 12px; font-weight: 700; color: var(--color-emerald); text-transform: uppercase;">Idle</div>
              </div>
              <div class="telemetry-breakdown">
                <div class="breakdown-row">
                  <div class="breakdown-colors">
                    <span class="breakdown-name">Memory Fetch</span>
                    <span id="t-mem-read" class="breakdown-val">0 ms</span>
                  </div>
                  <div class="bar-outer"><div id="bar-mem-read" class="bar-inner" style="background: var(--color-cyan);"></div></div>
                </div>
                <div class="breakdown-row">
                  <div class="breakdown-colors">
                    <span class="breakdown-name">Language / NLU</span>
                    <span id="t-nlu" class="breakdown-val">0 ms</span>
                  </div>
                  <div class="bar-outer"><div id="bar-nlu" class="bar-inner" style="background: var(--color-amber);"></div></div>
                </div>
                <div class="breakdown-row">
                  <div class="breakdown-colors">
                    <span class="breakdown-name">Orchestration / Tool</span>
                    <span id="t-orch" class="breakdown-val">0 ms</span>
                  </div>
                  <div class="bar-outer"><div id="bar-orch" class="bar-inner" style="background: var(--color-rose);"></div></div>
                </div>
                <div class="breakdown-row">
                  <div class="breakdown-colors">
                    <span class="breakdown-name">Memory Commit</span>
                    <span id="t-mem-write" class="breakdown-val">0 ms</span>
                  </div>
                  <div class="bar-outer"><div id="bar-mem-write" class="bar-inner" style="background: var(--color-emerald);"></div></div>
                </div>
                <div class="breakdown-row">
                  <div class="breakdown-colors">
                    <span class="breakdown-name">Gateway Loop</span>
                    <span id="t-gateway" class="breakdown-val">0 ms</span>
                  </div>
                  <div class="bar-outer"><div id="bar-gateway" class="bar-inner" style="background: var(--color-accent);"></div></div>
                </div>
              </div>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <div class="check-item">
                <span class="check-name">Target Latency Limit</span>
                <span class="check-status status-ok">&lt; 450 ms</span>
              </div>
              <div class="check-item">
                <span class="check-name">E2E Wall Time Estimate</span>
                <span id="telemetryE2E" class="check-status status-pending">0 ms</span>
              </div>
            </div>
          </div>

          <!-- Response & Traces Display Card -->
          <div class="card response-card">
            <div class="section-title">
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
              Agent Audio / Text Output
            </div>
            <div id="speakStatus" class="speak-indicator" style="display: none;">
              <span></span> Synthesis speaking audio out...
            </div>
            <div id="responseText" style="font-size: 1.1rem; font-weight: 500; color: #fff; margin: 12px 0; min-height: 24px; line-height: 1.4;">
              Await request execution...
            </div>
            
            <div class="tab-container">
              <div id="tab1" class="tab active" onclick="switchTab('response')">JSON Payload</div>
              <div id="tab2" class="tab" onclick="switchTab('stream')">SSE Stream</div>
              <div id="tab3" class="tab" onclick="switchTab('timeline')">Tool Audit Timeline</div>
            </div>
            
            <div id="tabContentResponse">
              <pre id="response">{}</pre>
            </div>
            <div id="tabContentStream" style="display: none;">
              <pre id="stream">SSE buffer empty.</pre>
            </div>
            <div id="tabContentTimeline" style="display: none;">
              <div id="timelineContainer" class="trace-timeline">
                <div class="trace-step info">
                  <div class="trace-dot"></div>
                  <div class="trace-header">
                    <span>Awaiting Execution</span>
                  </div>
                  <div class="trace-body">Run a turn request to generate tool execution envelopes.</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Live Reasoning Trace Log -->
          <div class="card">
            <div class="section-title">
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              Live Trace Auditor
            </div>
            <p class="preset-desc" style="margin-bottom: 8px; font-size:11px;">Displays current system correlation logs from the persistent ring buffer.</p>
            <pre id="traceLive" style="max-height: 220px; font-size: 11px;">No live logs loaded. Automatically updating...</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Script Block -->
    <script>
      const byId = (id) => document.getElementById(id);
      const getPayload = () => ({
        patientId: byId("patientId").value.trim() || undefined,
        callerNumber: byId("callerNumber").value.trim() || undefined,
        callId: byId("callId").value.trim(),
        utterance: byId("utterance").value.trim()
      });
      const langMap = { en: "en-IN", hi: "hi-IN", ta: "ta-IN" };

      const pickVoice = (langCode) => {
        const voices = speechSynthesis.getVoices();
        const target = langMap[langCode] || "en-IN";
        return voices.find(v => v.lang && v.lang.toLowerCase().startsWith(target.toLowerCase().slice(0, 2)))
          || voices.find(v => v.lang && v.lang.toLowerCase().includes("en"))
          || null;
      };

      const speakText = (text, langCode) => {
        if (!byId("speakOut").checked || !("speechSynthesis" in window) || !text) return;
        speechSynthesis.cancel(); // Stop active speak
        const utt = new SpeechSynthesisUtterance(text);
        utt.lang = langMap[langCode] || "en-IN";
        const voice = pickVoice(langCode);
        if (voice) utt.voice = voice;
        
        utt.onstart = () => {
          byId("speakStatus").style.display = "inline-flex";
        };
        utt.onend = () => {
          byId("speakStatus").style.display = "none";
        };
        utt.onerror = () => {
          byId("speakStatus").style.display = "none";
        };
        speechSynthesis.speak(utt);
      };

      function updateTelemetry(latencies) {
        if (!latencies) return;
        const total = Number(latencies.total || 0);
        const gateway = Number(latencies.gateway || 0);
        const e2e = Number(latencies.e2e_estimated || total + gateway);
        
        byId("latencyValue").textContent = Math.round(total);
        byId("telemetryE2E").textContent = Math.round(e2e) + " ms";
        
        // Gauge conic gradient percentage calculation (cap at 600ms = 100%)
        const pct = Math.min(100, Math.round((total / 600) * 100));
        byId("latencyGauge").style.setProperty("--pct", pct + "%");
        
        const rating = byId("latencyRating");
        if (e2e <= 250) {
          rating.textContent = "EXTREMELY FAST";
          rating.style.color = "var(--color-emerald)";
        } else if (e2e <= 450) {
          rating.textContent = "MEETS TARGET";
          rating.style.color = "var(--color-cyan)";
        } else {
          rating.textContent = "LATENCY EXCEEDED";
          rating.style.color = "var(--color-rose)";
        }

        // Horizontal Bars updates
        const updateBar = (barId, valId, valueMs) => {
          const rounded = Number(valueMs || 0).toFixed(1);
          byId(valId).textContent = rounded + " ms";
          const barPct = Math.min(100, Math.round((valueMs / 300) * 100));
          byId(barId).style.width = barPct + "%";
        };

        updateBar("bar-mem-read", "t-mem-read", latencies.memory_read);
        updateBar("bar-nlu", "t-nlu", latencies.nlu);
        updateBar("bar-orch", "t-orch", latencies.orchestration);
        updateBar("bar-mem-write", "t-mem-write", latencies.memory_write);
        updateBar("bar-gateway", "t-gateway", latencies.gateway);
      }

      function updateTimeline(toolTrace, latencies) {
        const container = byId("timelineContainer");
        container.innerHTML = "";
        
        if (!toolTrace || toolTrace.length === 0) {
          container.innerHTML = \`
            <div class="trace-step info">
              <div class="trace-dot"></div>
              <div class="trace-header"><span>No Tool Calls</span></div>
              <div class="trace-body">This turn was resolved entirely in cache or prompt logic.</div>
            </div>\`;
          return;
        }

        toolTrace.forEach((stepStr) => {
          const parts = stepStr.split(":");
          const name = parts[0] || "Unknown Service";
          const status = parts[1] || "ok";
          const timeText = parts[2] || "";
          
          const stepDiv = document.createElement("div");
          stepDiv.className = "trace-step " + (status === "error" ? "error" : "success");
          
          stepDiv.innerHTML = \`
            <div class="trace-dot"></div>
            <div class="trace-header">
              <span>\${name}</span>
              <span class="trace-elapsed">\${timeText}</span>
            </div>
            <div class="trace-body">Audited transaction: status=\${status}</div>
          \`;
          container.appendChild(stepDiv);
        });
      }

      function switchTab(tabName) {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        byId("tabContentResponse").style.display = "none";
        byId("tabContentStream").style.display = "none";
        byId("tabContentTimeline").style.display = "none";

        if (tabName === "response") {
          byId("tab1").classList.add("active");
          byId("tabContentResponse").style.display = "block";
        } else if (tabName === "stream") {
          byId("tab2").classList.add("active");
          byId("tabContentStream").style.display = "block";
        } else if (tabName === "timeline") {
          byId("tab3").classList.add("active");
          byId("tabContentTimeline").style.display = "block";
        }
      }

      byId("turnBtn").onclick = async () => {
        byId("responseText").textContent = "Analyzing speech turn...";
        byId("response").textContent = "Requesting gateway...";
        const started = performance.now();
        
        try {
          const resp = await fetch("/voice/turn", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(getPayload())
          });
          const data = await resp.json();
          byId("response").textContent = JSON.stringify(data, null, 2);
          
          if (data.error) {
            byId("responseText").textContent = "Error: " + (data.message || "Unresolved turn");
            byId("responseText").style.color = "var(--color-rose)";
            return;
          }
          
          byId("responseText").textContent = data.textResponse;
          byId("responseText").style.color = "#fff";
          
          updateTelemetry(data.latencyMs);
          updateTimeline(data.trace, data.latencyMs);
          speakText(data.textResponse, data.language);
        } catch (e) {
          byId("responseText").textContent = "Failed to communicate with gateway.";
          byId("responseText").style.color = "var(--color-rose)";
        }
      };

      const postTurn = async (payload) => {
        const resp = await fetch("/voice/turn", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        return await resp.json();
      };

      byId("streamBtn").onclick = async () => {
        byId("responseText").textContent = "Streaming agent response...";
        byId("stream").textContent = "Listening to SSE feed:\\n";
        switchTab("stream");
        
        if ("speechSynthesis" in window) speechSynthesis.cancel();
        
        try {
          const resp = await fetch("/voice/turn/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(getPayload())
          });
          const text = await resp.text();
          byId("stream").textContent += text;
          
          const lines = text.split("\\n");
          let fullResponseText = "";
          let finalLang = "en";
          
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const payload = JSON.parse(line.slice(6));
              if (payload.chunk) {
                fullResponseText += " " + payload.chunk;
                speakText(payload.chunk, payload.language || "en");
              }
              if (payload.language) {
                finalLang = payload.language;
              }
            } catch (_e) {}
          }
          
          byId("responseText").textContent = fullResponseText.trim() || "SSE Streaming complete.";
          byId("responseText").style.color = "var(--color-cyan)";
        } catch (e) {
          byId("responseText").textContent = "SSE endpoint connection failed.";
          byId("responseText").style.color = "var(--color-rose)";
        }
      };

      byId("traceBtn").onclick = async () => {
        const callId = byId("callId").value.trim();
        byId("response").textContent = "Loading trace logs...";
        switchTab("response");
        const resp = await fetch("/voice/traces/" + encodeURIComponent(callId));
        const data = await resp.json();
        byId("response").textContent = JSON.stringify(data, null, 2);
      };

      // Preset click animations and handlers
      const setupPreset = (btnId, clickHandler) => {
        const btn = byId(btnId);
        if (btn) {
          btn.addEventListener("click", async () => {
            btn.style.borderColor = "var(--color-cyan)";
            btn.style.boxShadow = "0 0 10px rgba(6, 182, 212, 0.2)";
            byId("responseText").textContent = "Running preset sequence...";
            await clickHandler();
            setTimeout(() => {
              btn.style.borderColor = "";
              btn.style.boxShadow = "";
            }, 1000);
          });
        }
      };

      setupPreset("demoBookBtn", async () => {
        const callId = "call-demo-book";
        byId("callId").value = callId;
        byId("micLang").value = "en-IN";
        const data = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "book appointment tomorrow morning with dr rao"
        });
        byId("response").textContent = JSON.stringify(data, null, 2);
        byId("responseText").textContent = data.textResponse;
        updateTelemetry(data.latencyMs);
        updateTimeline(data.trace, data.latencyMs);
        speakText(data.textResponse, data.language);
      });

      setupPreset("demoConflictBtn", async () => {
        const callId = "call-demo-conflict";
        byId("callId").value = callId;
        byId("micLang").value = "hi-IN";
        await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "book appointment tomorrow evening with dr rao"
        });
        const data = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "book appointment tomorrow evening with dr rao"
        });
        byId("response").textContent = JSON.stringify(data, null, 2);
        byId("responseText").textContent = data.textResponse;
        updateTelemetry(data.latencyMs);
        updateTimeline(data.trace, data.latencyMs);
        speakText(data.textResponse, data.language);
      });

      setupPreset("demoSelectBtn", async () => {
        const callId = "call-demo-conflict";
        byId("callId").value = callId;
        byId("micLang").value = "ta-IN";
        const data = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "1"
        });
        byId("response").textContent = JSON.stringify(data, null, 2);
        byId("responseText").textContent = data.textResponse;
        updateTelemetry(data.latencyMs);
        updateTimeline(data.trace, data.latencyMs);
        speakText(data.textResponse, data.language);
      });

      setupPreset("demoRescheduleBtn", async () => {
        const callId = "call-demo-reschedule";
        byId("callId").value = callId;
        const first = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "book appointment tomorrow afternoon with dr mehta"
        });
        const apptId = (first.textResponse || "").match(/apt-[a-z0-9]+/i)?.[0];
        const data = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "reschedule " + (apptId || "") + " to tomorrow evening"
        });
        byId("response").textContent = JSON.stringify({ first, second: data }, null, 2);
        byId("responseText").textContent = data.textResponse;
        updateTelemetry(data.latencyMs);
        updateTimeline(data.trace, data.latencyMs);
        speakText(data.textResponse, data.language);
      });

      setupPreset("demoCancelBtn", async () => {
        const callId = "call-demo-cancel";
        byId("callId").value = callId;
        const first = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "book appointment tomorrow morning with dr rao"
        });
        const apptId = (first.textResponse || "").match(/apt-[a-z0-9]+/i)?.[0];
        const data = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "cancel " + (apptId || "")
        });
        byId("response").textContent = JSON.stringify({ first, second: data }, null, 2);
        byId("responseText").textContent = data.textResponse;
        updateTelemetry(data.latencyMs);
        updateTimeline(data.trace, data.latencyMs);
        speakText(data.textResponse, data.language);
      });

      setupPreset("demoOutboundBtn", async () => {
        const callId = "call-demo-outbound";
        byId("callId").value = callId;
        const data = await postTurn({
          callerNumber: byId("callerNumber").value.trim(),
          callId,
          utterance: "no thanks, not now"
        });
        byId("response").textContent = JSON.stringify(data, null, 2);
        byId("responseText").textContent = data.textResponse;
        updateTelemetry(data.latencyMs);
        updateTimeline(data.trace, data.latencyMs);
        speakText(data.textResponse, data.language);
      });

      // Poll live correlation logs
      setInterval(async () => {
        const callId = byId("callId").value.trim();
        if (!callId) return;
        try {
          const resp = await fetch("/voice/traces/" + encodeURIComponent(callId));
          const data = await resp.json();
          byId("traceLive").textContent = JSON.stringify(data, null, 2);
        } catch (_e) {}
      }, 3000);

      byId("speechStopBtn").onclick = () => {
        if ("speechSynthesis" in window) speechSynthesis.cancel();
      };

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      let recognition = null;

      if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onstart = () => {
          byId("micStatusText").textContent = "Orchestrator Listening...";
          byId("micStatusText").className = "mic-status-text active";
          byId("micWave").classList.add("active");
        };
        recognition.onend = () => {
          byId("micStatusText").textContent = "Mic stopped";
          byId("micStatusText").className = "mic-status-text";
          byId("micWave").classList.remove("active");
        };
        recognition.onerror = (e) => {
          byId("micStatusText").textContent = "Mic Error: " + (e.error || "unknown");
          byId("micStatusText").className = "mic-status-text";
          byId("micWave").classList.remove("active");
        };
        recognition.onresult = (event) => {
          let finalText = "";
          let interimText = "";
          for (let i = event.resultIndex; i < event.results.length; i += 1) {
            const txt = event.results[i][0].transcript || "";
            if (event.results[i].isFinal) {
              finalText += txt + " ";
            } else {
              interimText += txt + " ";
            }
          }
          const combined = (finalText + interimText).trim();
          if (combined) {
            byId("utterance").value = combined;
          }
        };
      } else {
        byId("micStatusText").textContent = "Speech API Not Supported";
      }

      byId("micStartBtn").onclick = () => {
        if (!recognition) return;
        recognition.lang = byId("micLang").value;
        recognition.start();
      };

      byId("micStopBtn").onclick = () => {
        if (!recognition) return;
        recognition.stop();
      };
    </script>
  </body>
</html>`);
});

app.get("/voice/traces/:callId", async (req, res) => {
  const response = await fetch(`${AGENT_URL}/traces/${req.params.callId}`);
  const payload = await response.json();
  res.json(payload);
});

app.post("/voice/turn", async (req, res) => {
  const body = req.body as TurnPayload;
  const callId = body.callId ?? `call-${randomUUID().slice(0, 8)}`;
  const startedAt = performance.now();
  const correlationId = `corr-${randomUUID().slice(0, 8)}`;

  const identityResp = await fetch(`${IDENTITY_URL}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      call_id: callId,
      caller_number: body.callerNumber ?? null,
      provided_patient_id: body.patientId ?? null
    })
  });
  const identityPayload = await identityResp.json();
  if (!identityPayload?.resolved || !identityPayload?.patient_id) {
    return res.status(400).json({
      callId,
      error: true,
      message: "patient_identity_unresolved",
      identity: identityPayload
    });
  }

  const response = await fetch(`${AGENT_URL}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-correlation-id": correlationId },
    body: JSON.stringify({
      call_id: callId,
      patient_id: identityPayload.patient_id,
      utterance: body.utterance,
      language_hint: body.languageHint ?? null
    })
  });

  const payload = await response.json();
  if (!response.ok) {
    return res.status(response.status).json({
      callId,
      error: true,
      message: payload?.detail ?? "agent_error",
      raw: payload
    });
  }
  const gatewayMs = Number((performance.now() - startedAt).toFixed(2));
  const agentLatency = payload?.latency_ms ?? {};
  const agentTotal = Number(agentLatency?.total ?? 0);

  res.json({
    callId,
    patientId: identityPayload.patient_id,
    correlationId,
    textResponse: payload.response_text,
    language: payload.language,
    intent: payload.intent,
    trace: payload.tool_trace,
    latencyMs: {
      ...agentLatency,
      gateway: gatewayMs,
      e2e_estimated: Number((agentTotal + gatewayMs).toFixed(2))
    }
  });
});

app.post("/voice/turn/stream", async (req, res) => {
  const body = req.body as TurnPayload;
  const callId = body.callId ?? `call-${randomUUID().slice(0, 8)}`;
  const correlationId = `corr-${randomUUID().slice(0, 8)}`;
  const identityResp = await fetch(`${IDENTITY_URL}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      call_id: callId,
      caller_number: body.callerNumber ?? null,
      provided_patient_id: body.patientId ?? null
    })
  });
  const identityPayload = await identityResp.json();
  if (!identityPayload?.resolved || !identityPayload?.patient_id) {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders();
    res.write(`event: error\\ndata: ${JSON.stringify({ callId, message: "patient_identity_unresolved", identity: identityPayload })}\\n\\n`);
    return res.end();
  }
  const response = await fetch(`${AGENT_URL}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-correlation-id": correlationId },
    body: JSON.stringify({
      call_id: callId,
      patient_id: identityPayload.patient_id,
      utterance: body.utterance,
      language_hint: body.languageHint ?? null
    })
  });
  const payload = await response.json();
  if (!response.ok) {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders();
    res.write(`event: error\\ndata: ${JSON.stringify({ callId, message: payload?.detail ?? "agent_error" })}\\n\\n`);
    return res.end();
  }
  const chunks = String(payload.response_text).split(/([,.!?])/).filter(Boolean);

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  for (let i = 0; i < chunks.length; i += 1) {
    const data = {
      callId,
      seq: i + 1,
      chunk: chunks[i].trim(),
      language: payload.language
    };
    res.write(`event: chunk\\ndata: ${JSON.stringify(data)}\\n\\n`);
  }
  res.write(`event: done\\ndata: ${JSON.stringify({ callId, intent: payload.intent, trace: payload.tool_trace })}\\n\\n`);
  res.end();
});

app.listen(3000, () => {
  console.log("voice-gateway listening on :3000");
});
