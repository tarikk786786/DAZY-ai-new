import { FormEvent, useCallback, useEffect, useState } from "react";
import { useDazy } from "./useDazy";
import { useVoiceInput } from "./useVoiceInput";
import { VOICE_OPTIONS, setVoiceChoice, playChime, type VoiceChoice } from "./lib/speech";
import {
  Reactor,
  RemindersPanel,
  StatusPanel,
  Toasts,
  Waveform,
  MemoryPanel,
  ProviderPanel,
  HistoryDrawer,
  ConfirmDialog,
  useAutoScroll,
  useIstClock,
} from "./hud";

const EMOTION_BADGES: Record<string, string> = {
  affection: "affectionate",
  happy: "happy",
  playful: "playful",
  empathetic: "empathetic",
  curious: "curious",
  excited: "excited",
  sad: "feeling low",
  serious: "serious",
  confident: "confident",
  neutral: "calm",
};

export default function App() {
  const dazy = useDazy();
  const { messages, state, error, setState, send, interrupt, retryLast, status } = dazy;
  const [draft, setDraft] = useState("");
  const [voice, setVoice] = useState<VoiceChoice>("neerja");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [testingProviders, setTestingProviders] = useState(false);
  const clock = useIstClock();

  useEffect(() => setVoiceChoice(voice), [voice]);

  const paused = state === "speaking" || state === "thinking";
  const onFinalVoice = useCallback((text: string) => send(text), [send]);
  const { alwaysOn, toggleAlways, interim, supported } = useVoiceInput({ onFinal: onFinalVoice, paused });
  const chatRef = useAutoScroll(messages.length + state + interim);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim() || state === "thinking") return;
    const text = draft;
    setDraft("");
    playChime("send");
    send(text);
  };

  const copyMsg = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch {
      // clipboard unavailable (permissions); silently ignore
    }
  };

  const testProviders = () => {
    setTestingProviders(true);
    dazy.deepStatus();
    setTimeout(() => setTestingProviders(false), 4000);
  };

  const err = error;
  const backend = status?.backend;
  const primary = status?.providers?.[0];
  const dbTone = !backend ? "idle" : backend.state === "healthy" ? "ok" : "bad";
  const primaryTone = !primary ? "idle" : primary.state === "healthy" ? "ok" : primary.state === "unhealthy" ? "bad" : "idle";

  const items = [
    { label: "Local time", value: clock },
    { label: "Backend", value: !backend ? "…" : backend.state === "healthy" ? `Healthy · ${backend.latency_ms}ms` : "Down", tone: dbTone as "ok" | "bad" | "idle" },
    { label: "Primary brain", value: !primary ? "…" : primary.state === "healthy" ? `gemini · ${(primary.latency_ms / 1000).toFixed(1)}s` : primary.state === "unhealthy" ? primary.detail : "standby", tone: primaryTone as "ok" | "bad" | "idle" },
    { label: "Memories", value: String(dazy.memories.length) },
    { label: "Reminders", value: String(dazy.reminders.length) },
    { label: "Mic", value: supported ? (alwaysOn ? "Always ON" : "Ready") : "Text only", tone: supported && alwaysOn ? ("ok" as const) : ("idle" as const) },
    { label: "Msgs last 24h", value: backend ? String(backend.messages_24h) : "…" },
  ];

  return (
    <div className="app-shell">
      <header className="hud-header">
        <div className="hud-logo">
          <button className="icon-btn" onClick={() => setHistoryOpen(true)} title="Conversation history">
            <HistoryIcon />
          </button>
          <div>
            <div className="hud-title">DAZY</div>
            <div className="hud-subtitle">Personal AI · Hinglish Companion</div>
          </div>
        </div>
        <div className="header-status">
          <span className={`status-dot ${err || (backend && backend.state === "unhealthy") ? "off" : state === "idle" ? "" : "busy"}`} />
          {err || (backend && backend.state === "unhealthy")
            ? "ATTENTION"
            : state === "idle"
              ? "ONLINE"
              : state.toUpperCase()}
        </div>
      </header>

      {interim && (
        <div className="interim-banner">
          <span className="status-dot busy" /> {interim}
        </div>
      )}

      <main className="hud-main">
        <aside className="side-panel">
          <div className="glass core-panel">
            <div className="panel-title">Core</div>
            <Reactor state={state === "idle" && alwaysOn ? "listening" : state} hasError={!!err || backend?.state === "unhealthy"} />
            <Waveform state={state} />
            <label className="voice-pick">
              Voice
              <select value={voice} onChange={(e) => setVoice(e.target.value as VoiceChoice)}>
                {VOICE_OPTIONS.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.label}
                  </option>
                ))}
              </select>
            </label>
            {state === "speaking" && (
              <button className="btn-secondary interrupt-btn" onClick={interrupt}>
                Stop speaking
              </button>
            )}
          </div>
          <StatusPanel items={items} />
          <ProviderPanel providers={status?.providers ?? null} onTest={testProviders} testing={testingProviders} />
        </aside>

        <section className="chat-column">
          <div className="chat-scroll glass" ref={chatRef}>
            {dazy.booted && messages.length === 0 && (
              <div className="msg-row assistant">
                <div className="msg-avatar">D</div>
                <div>
                  <div className="msg-bubble">
                    Hi! Main DAZY hoon — aapki personal AI companion. Batao, aaj kya chal raha hai?
                    Mujhse kuch bhi kaha jaa sakta hai — apni pasand, important dates, ya bas
                    "kal 7 baje mujhe remind kar dena".
                  </div>
                </div>
              </div>
            )}

            {messages.map((m) => (
              <div className={`msg-row ${m.role}`} key={m.id}>
                {m.role === "assistant" && <div className="msg-avatar">D</div>}
                <div style={{ maxWidth: "100%" }}>
                  <div className="msg-bubble">
                    {m.content}
                    <div className="msg-meta">
                      <span className="msg-time">{new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
                      {m.role === "assistant" && m.provider && (
                        <span className="msg-provider" title={m.model ?? ""}>
                          {m.provider}
                          {m.latency_ms ? ` · ${(m.latency_ms / 1000).toFixed(1)}s` : ""}
                        </span>
                      )}
                      <button className="msg-copy" onClick={() => copyMsg(m.id, m.content)}>
                        {copiedId === m.id ? "copied" : "copy"}
                      </button>
                    </div>
                  </div>
                  {m.role === "assistant" && m.emotion && (
                    <div className="msg-emotion">{EMOTION_BADGES[m.emotion] ?? m.emotion}</div>
                  )}
                </div>
              </div>
            ))}

            {state === "thinking" && (
              <div className="msg-row assistant">
                <div className="msg-avatar">D</div>
                <div className="msg-bubble">
                  <span className="typing-dots"><span /><span /><span /></span>
                </div>
              </div>
            )}
          </div>

          {err && (
            <div className="error-bar">
              <span>{err.detail}</span>
              {lastRetryable(err.code) && (
                <button className="btn-retry" onClick={retryLast}>
                  Retry
                </button>
              )}
            </div>
          )}

          <form className="input-bar glass" onSubmit={onSubmit}>
            <button
              type="button"
              className={`mic-btn ${alwaysOn ? "always" : ""} ${state === "listening" ? "recording" : ""}`}
              onClick={toggleAlways}
              title={supported ? "Toggle always-listening" : "Voice not supported in this browser"}
              disabled={!supported}
            >
              <MicIcon />
            </button>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder={state === "listening" ? "Sun rahi hoon — bolo..." : "Kuch bhi bolo... type ya mic on karo"}
            />
            <button className="send-btn" type="submit" disabled={!draft.trim() || state === "thinking"}>
              Send
            </button>
          </form>
        </section>

        <aside className="side-panel">
          <MemoryPanel memories={dazy.memories} onForget={dazy.forgetMemory} onEdit={dazy.editMemory} />
          <RemindersPanel
            reminders={dazy.reminders}
            onEdit={dazy.editReminder}
            onDelete={dazy.deleteReminder}
            onSnooze={dazy.snoozeReminder}
            onComplete={dazy.completeReminder}
          />
          <div className="glass">
            <button className="btn-secondary full-width" onClick={() => setConfirmClear(true)}>
              Clear this conversation
            </button>
          </div>
        </aside>
      </main>

      {historyOpen && (
        <HistoryDrawer
          conversations={dazy.conversations}
          activeId={dazy.conversation?.id ?? null}
          onOpen={dazy.openConversation}
          onNew={() => {
            void dazy.newConversation();
            setHistoryOpen(false);
          }}
          onClose={() => setHistoryOpen(false)}
        />
      )}

      {confirmClear && (
        <ConfirmDialog
          text="Clear all messages in this conversation? DAZY's memories and reminders stay."
          onConfirm={() => {
            void dazy.clearChat();
            setConfirmClear(false);
          }}
          onCancel={() => setConfirmClear(false)}
        />
      )}

      <Toasts toasts={dazy.toasts} onDismiss={dazy.dismissToast} />
    </div>
  );
}

function lastRetryable(code?: string): boolean {
  return code === "ALL_PROVIDERS_FAILED" || code === "RATE_LIMIT" || code === "UNKNOWN";
}

function MicIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}

function HistoryIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M12 7v5l4 2" />
    </svg>
  );
}
