import { useEffect, useRef, useState } from "react";
import type { DazyState, Memory, ProviderHealth, Reminder } from "./lib/types";

const REACTOR_LABELS: Record<DazyState | "error", string> = {
  idle: "STANDBY",
  listening: "LISTENING",
  thinking: "PROCESSING",
  speaking: "SPEAKING",
  error: "ATTENTION",
};

export function Reactor({ state, hasError }: { state: DazyState; hasError?: boolean }) {
  const shown = hasError && state === "idle" ? "error" : state;
  const labels = { ...REACTOR_LABELS } as Record<string, string>;
  return (
    <div className="reactor-wrap">
      <div className={`reactor ${shown}`}>
        <div className="reactor-ring" />
        <div className="reactor-ring r2" />
        <div className="reactor-ring r3" />
        <div className="reactor-orbit" />
        <div className="reactor-orbit o2" />
        <div className="reactor-core" />
        <div className="reactor-glow" />
      </div>
      <div className={`reactor-state ${shown === "error" ? "err" : ""}`}>{labels[shown]}</div>
    </div>
  );
}

export function Waveform({ state }: { state: DazyState }) {
  const active = state === "speaking" || state === "listening";
  return (
    <div className={`waveform ${active ? "active" : ""}`}>
      {Array.from({ length: 24 }, (_, i) => (
        <span
          key={i}
          style={{
            animationDelay: `${(i % 6) * 0.09}s`,
            animationDuration: `${0.7 + ((i * 7) % 5) * 0.12}s`,
          }}
        />
      ))}
    </div>
  );
}

export function StatusPanel({
  items,
}: {
  items: { label: string; value: string; tone?: "ok" | "warn" | "bad" | "idle" }[];
}) {
  return (
    <div className="glass">
      <div className="panel-title">System Status</div>
      {items.map((g) => (
        <div className="gauge-row" key={g.label}>
          <span className="gauge-label">{g.label}</span>
          <span className={`gauge-value ${g.tone ?? ""}`}>{g.value}</span>
        </div>
      ))}
    </div>
  );
}

export function ProviderPanel({
  providers,
  onTest,
  testing,
}: {
  providers: ProviderHealth[] | null;
  onTest: () => void;
  testing: boolean;
}) {
  const stateLabel = { healthy: "HEALTHY", unhealthy: "DOWN", unknown: "IDLE" };
  return (
    <div className="glass">
      <div className="panel-title">
        AI Brains
        <button className="panel-action" onClick={onTest} disabled={testing}>
          {testing ? "Testing…" : "Test now"}
        </button>
      </div>
      {!providers ? (
        <div className="empty-hint">Checking provider health…</div>
      ) : (
        providers.map((p) => (
          <div className="prov-row" key={p.id} title={p.detail}>
            <span className={`prov-dot ${p.state}`} />
            <div className="prov-main">
              <div className="prov-name">
                {p.id}
                <span className={`prov-role ${p.role}`}>{p.role}</span>
              </div>
              <div className="prov-model">{p.model}</div>
            </div>
            <div className="prov-side">
              <div className={`prov-state ${p.state}`}>{stateLabel[p.state]}</div>
              {p.stats_24h.total > 0 && (
                <div className="prov-stats">
                  {p.stats_24h.ok}/{p.stats_24h.total} ok
                  {p.stats_24h.avg_ok_latency_ms > 0 && ` · ${(p.stats_24h.avg_ok_latency_ms / 1000).toFixed(1)}s`}
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export function MemoryPanel({
  memories,
  onForget,
  onEdit,
}: {
  memories: Memory[];
  onForget: (id: string) => void;
  onEdit: (id: string, value: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const filtered = memories.filter(
    (m) => !query.trim() || m.key.toLowerCase().includes(query.toLowerCase()) || m.value.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="glass">
      <div className="panel-title">What She Remembers</div>
      {memories.length > 3 && (
        <input
          className="panel-search"
          placeholder="Search memories…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      )}
      {memories.length === 0 ? (
        <div className="empty-hint">Kuch bhi nahi abhi — talk to her and she'll start remembering the little things.</div>
      ) : filtered.length === 0 ? (
        <div className="empty-hint">No memories match "{query}".</div>
      ) : (
        filtered.map((m) =>
          editingId === m.id ? (
            <div className="mem-row editing" key={m.id}>
              <input
                className="mem-edit-input"
                value={editValue}
                autoFocus
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    onEdit(m.id, editValue);
                    setEditingId(null);
                  }
                  if (e.key === "Escape") setEditingId(null);
                }}
              />
              <button
                className="mem-forget save"
                onClick={() => {
                  onEdit(m.id, editValue);
                  setEditingId(null);
                }}
                title="Save"
              >
                ✓
              </button>
              <button className="mem-forget" onClick={() => setEditingId(null)} title="Cancel">
                ✕
              </button>
            </div>
          ) : (
            <div className="mem-row" key={m.id}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="mem-key">{m.key}</div>
                <div className="mem-value">{m.value}</div>
                <div className="mem-when">{new Date(m.updated_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</div>
              </div>
              <button
                className="mem-forget edit"
                onClick={() => {
                  setEditingId(m.id);
                  setEditValue(m.value);
                }}
                title="Edit"
              >
                ✎
              </button>
              <button className="mem-forget" onClick={() => onForget(m.id)} title="Make her forget this">
                ✕
              </button>
            </div>
          )
        )
      )}
    </div>
  );
}

export function RemindersPanel({
  reminders,
  onEdit,
  onDelete,
  onSnooze,
  onComplete,
}: {
  reminders: Reminder[];
  onEdit: (id: string, title: string) => void;
  onDelete: (id: string) => void;
  onSnooze: (id: string, minutes: number) => void;
  onComplete: (id: string) => void;
}) {
  const [menuId, setMenuId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  return (
    <div className="glass">
      <div className="panel-title">Upcoming</div>
      {reminders.length === 0 ? (
        <div className="empty-hint">No reminders yet. Try: "kal 9 baje mujhe utha dena".</div>
      ) : (
        reminders.map((r) => {
          const when = new Date(r.due_at).toLocaleString("en-IN", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
          });
          return (
            <div className="rem-row" key={r.id}>
              {editingId === r.id ? (
                <input
                  className="mem-edit-input"
                  value={editValue}
                  autoFocus
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      onEdit(r.id, editValue);
                      setEditingId(null);
                    }
                    if (e.key === "Escape") setEditingId(null);
                  }}
                  onBlur={() => {
                    onEdit(r.id, editValue);
                    setEditingId(null);
                  }}
                />
              ) : (
                <>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="rem-title">{r.title}</div>
                    <div className="rem-when">{when}</div>
                  </div>
                  <button className="rem-act done" onClick={() => onComplete(r.id)} title="Mark done">
                    ✓
                  </button>
                  <button
                    className="rem-act"
                    onClick={() => {
                      setMenuId(menuId === r.id ? null : r.id);
                    }}
                    title="More"
                  >
                    ⋯
                  </button>
                  {menuId === r.id && (
                    <div className="rem-menu" onMouseLeave={() => setMenuId(null)}>
                      <button
                        onClick={() => {
                          setEditingId(r.id);
                          setEditValue(r.title);
                          setMenuId(null);
                        }}
                      >
                        Rename
                      </button>
                      <button
                        onClick={() => {
                          onSnooze(r.id, 10);
                          setMenuId(null);
                        }}
                      >
                        Snooze 10m
                      </button>
                      <button
                        onClick={() => {
                          onSnooze(r.id, 60);
                          setMenuId(null);
                        }}
                      >
                        Snooze 1h
                      </button>
                      <button
                        className="danger"
                        onClick={() => {
                          onDelete(r.id);
                          setMenuId(null);
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}

export function Toasts({
  toasts,
  onDismiss,
}: {
  toasts: { id: string; title: string; when: string }[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="toast-wrap">
      {toasts.map((t) => (
        <div className="toast" key={t.id} onClick={() => onDismiss(t.id)}>
          <div className="toast-label">REMINDER</div>
          <div className="rem-title">{t.title}</div>
          <div className="rem-when">due {t.when} — tap to dismiss</div>
        </div>
      ))}
    </div>
  );
}

export function HistoryDrawer({
  conversations,
  activeId,
  onOpen,
  onNew,
  onClose,
}: {
  conversations: { id: string; title: string; last_message_at: string }[];
  activeId: string | null;
  onOpen: (id: string) => void;
  onNew: () => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer glass" onClick={(e) => e.stopPropagation()} ref={ref}>
        <div className="panel-title">
          Conversations
          <button className="panel-action" onClick={onNew}>
            + New
          </button>
        </div>
        {conversations.length === 0 ? (
          <div className="empty-hint">No conversations yet.</div>
        ) : (
          conversations.map((c) => (
            <button
              className={`conv-row ${c.id === activeId ? "active" : ""}`}
              key={c.id}
              onClick={() => {
                onOpen(c.id);
                onClose();
              }}
            >
              <div className="conv-title">{c.title}</div>
              <div className="conv-when">{new Date(c.last_message_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

export function ConfirmDialog({ text, onConfirm, onCancel }: { text: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="drawer-backdrop" onClick={onCancel}>
      <div className="drawer confirm glass" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-text">{text}</div>
        <div className="confirm-actions">
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-danger" onClick={onConfirm}>
            Yes, clear it
          </button>
        </div>
      </div>
    </div>
  );
}

export function useIstClock(): string {
  const [now, setNow] = useState("");
  useEffect(() => {
    const tick = () =>
      setNow(
        new Date().toLocaleTimeString("en-IN", {
          timeZone: "Asia/Kolkata",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        })
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

export function useAutoScroll(dep: unknown) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [dep]);
  return ref;
}
