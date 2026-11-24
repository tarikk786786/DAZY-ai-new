import { useCallback, useEffect, useRef, useState } from "react";
import { supabase } from "./lib/supabase";
import { speak, stopSpeaking, playChime } from "./lib/speech";
import type { ChatMessage, Conversation, DazyReply, DazyState, DazyStatus, Memory, Reminder } from "./lib/types";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

export function useDazy() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [state, setState] = useState<DazyState>("idle");
  const [error, setError] = useState<{ code: string; detail: string } | null>(null);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [toasts, setToasts] = useState<{ id: string; title: string; when: string }[]>([]);
  const [booted, setBooted] = useState(false);
  const [status, setStatus] = useState<DazyStatus | null>(null);
  const [lastUserMsg, setLastUserMsg] = useState<string | null>(null);
  const busyRef = useRef(false);

  const refreshMemories = useCallback(async () => {
    const { data } = await supabase
      .from("memories")
      .select("*")
      .order("importance", { ascending: false })
      .order("updated_at", { ascending: false })
      .limit(14);
    setMemories(data ?? []);
  }, []);

  const refreshReminders = useCallback(async () => {
    const { data } = await supabase
      .from("reminders")
      .select("*")
      .is("completed_at", null)
      .order("due_at", { ascending: true })
      .limit(8);
    setReminders(data ?? []);
  }, []);

  const forgetMemory = useCallback(async (id: string) => {
    await supabase.from("memories").delete().eq("id", id);
    setMemories((m) => m.filter((x) => x.id !== id));
  }, []);

  const clearChat = useCallback(async () => {
    if (!conversation) return;
    await supabase.from("messages").delete().eq("conversation_id", conversation.id);
    setMessages([]);
  }, [conversation]);

  const editMemory = useCallback(async (id: string, value: string) => {
    const v = value.trim();
    if (!v) return;
    await supabase.from("memories").update({ value: v.slice(0, 500) }).eq("id", id);
    setMemories((m) => m.map((x) => (x.id === id ? { ...x, value: v.slice(0, 500) } : x)));
  }, []);

  const editReminder = useCallback(async (id: string, title: string) => {
    const t = title.trim();
    if (!t) return;
    await supabase.from("reminders").update({ title: t.slice(0, 300) }).eq("id", id);
    setReminders((r) => r.map((x) => (x.id === id ? { ...x, title: t.slice(0, 300) } : x)));
  }, []);

  const deleteReminder = useCallback(async (id: string) => {
    await supabase.from("reminders").delete().eq("id", id);
    setReminders((r) => r.filter((x) => x.id !== id));
  }, []);

  const snoozeReminder = useCallback(async (id: string, minutes: number) => {
    const r = reminders.find((x) => x.id === id);
    if (!r) return;
    const newDue = new Date(Math.max(Date.now(), new Date(r.due_at).getTime()) + minutes * 60_000).toISOString();
    const { data, error: e } = await supabase.from("reminders").update({ due_at: newDue, completed_at: null }).eq("id", id).select().maybeSingle();
    if (!e && data) setReminders((list) => list.map((x) => (x.id === id ? data : x)));
  }, [reminders]);

  const completeReminder = useCallback(async (id: string) => {
    const { error: e } = await supabase.from("reminders").update({ completed_at: new Date().toISOString() }).eq("id", id);
    if (!e) setReminders((list) => list.filter((x) => x.id !== id));
  }, []);

  useEffect(() => {
    (async () => {
      const { data: existing } = await supabase
        .from("conversations")
        .select("*")
        .order("last_message_at", { ascending: false })
        .limit(1)
        .maybeSingle();

      let conv = existing;
      if (!conv) {
        const { data: created } = await supabase
          .from("conversations")
          .insert({ title: "Baatein with DAZY" })
          .select()
          .maybeSingle();
        conv = created;
      }
      if (conv) {
        setConversation(conv);
        const { data: msgs } = await supabase
          .from("messages")
          .select("*")
          .eq("conversation_id", conv.id)
          .order("created_at", { ascending: true })
          .limit(80);
        setMessages(msgs ?? []);
      }
      const { data: convs } = await supabase
        .from("conversations")
        .select("*")
        .order("last_message_at", { ascending: false })
        .limit(20);
      setConversations(convs ?? []);
      await Promise.all([refreshMemories(), refreshReminders()]);
      setBooted(true);
    })();
  }, [refreshMemories, refreshReminders]);

  // Real backend health: cheap poll every 60s, deep provider probe every 10min.
  const fetchStatus = useCallback(async (deep = false) => {
    try {
      const res = await fetch(`${SUPABASE_URL}/functions/v1/dazy-status${deep ? "?deep=true" : ""}`, {
        headers: { Authorization: `Bearer ${SUPABASE_ANON_KEY}` },
      });
      if (!res.ok) return;
      const body = await res.json();
      if (body && body.ok) setStatus(body as DazyStatus);
    } catch {
      // keep last known status; connection loss shows in backend.state via staleness
    }
  }, []);

  useEffect(() => {
    void fetchStatus(false);
    void fetchStatus(true);
    const cheap = setInterval(() => void fetchStatus(false), 60_000);
    const deep = setInterval(() => void fetchStatus(true), 600_000);
    return () => {
      clearInterval(cheap);
      clearInterval(deep);
    };
  }, [fetchStatus]);

  // Reminder watcher: spoken, chime-backed toasts when due.
  useEffect(() => {
    const fired = new Set<string>();
    const timer = setInterval(() => {
      const now = Date.now();
      for (const r of reminders) {
        const due = new Date(r.due_at).getTime();
        if (due <= now && now - due < 120_000 && !fired.has(r.id)) {
          fired.add(r.id);
          const when = new Date(r.due_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
          setToasts((t) => [...t, { id: r.id, title: r.title, when }]);
          playChime("alert");
          speak(`Reminder: ${r.title}`, "speaking", () => setState("idle"));
          supabase.from("reminders").update({ completed_at: new Date().toISOString() }).eq("id", r.id);
          setTimeout(() => setToasts((t) => t.filter((x) => x.id !== r.id)), 45_000);
          refreshReminders();
        }
      }
    }, 10_000);
    return () => clearInterval(timer);
  }, [reminders, refreshReminders]);

  const send = useCallback(
    async (text: string) => {
      if (!conversation || busyRef.current) return;
      const trimmed = text.trim();
      if (!trimmed) return;

      busyRef.current = true;
      setError(null);
      setState("thinking");
      setLastUserMsg(trimmed);

      const { data: userMsg, error: insertErr } = await supabase
        .from("messages")
        .insert({ conversation_id: conversation.id, role: "user", content: trimmed })
        .select()
        .maybeSingle();

      if (insertErr || !userMsg) {
        setError({ code: "DB", detail: "Message save nahi hua — connection check karo." });
        setState("idle");
        busyRef.current = false;
        return;
      }
      setMessages((m) => [...m, userMsg]);

      try {
        const res = await fetch(`${SUPABASE_URL}/functions/v1/dazy-chat`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ conversation_id: conversation.id, message: trimmed }),
        });

        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw Object.assign(new Error(body.detail ?? `Request failed (${res.status})`), { code: body.error });
        }
        const reply = body as DazyReply;
        if (!reply || typeof reply.response !== "string") {
          throw new Error("Unexpected reply shape");
        }

        setMessages((m) => [
          ...m,
          {
            id: `tmp-${Date.now()}`,
            conversation_id: conversation.id,
            role: "assistant",
            content: reply.response,
            emotion: reply.emotion,
            created_at: new Date().toISOString(),
            provider: reply.provider_used,
            model: reply.model_used,
            latency_ms: reply.latency_ms,
          },
        ]);

        if (reply.memory_saved) void refreshMemories();
        if (reply.reminder_set) void refreshReminders();

        setState("speaking");
        speak(reply.speak || reply.response, "speaking", () => setState("idle"));
      } catch (err) {
        const e = err as Error & { code?: string };
        setError({ code: e.code ?? "UNKNOWN", detail: e.message });
        setState("idle");
      } finally {
        busyRef.current = false;
        void supabase.from("conversations").update({ last_message_at: new Date().toISOString() }).eq("id", conversation.id);
      }
    },
    [conversation, refreshMemories, refreshReminders]
  );

  const retryLast = useCallback(() => {
    if (lastUserMsg && !busyRef.current) void send(lastUserMsg);
  }, [lastUserMsg, send]);

  const deepStatus = useCallback(() => {
    void fetchStatus(true);
  }, [fetchStatus]);

  const dismissToast = useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const interrupt = useCallback(() => {
    stopSpeaking();
    setState("idle");
  }, []);

  const openConversation = useCallback(async (id: string) => {
    const { data: msgs } = await supabase
      .from("messages")
      .select("*")
      .eq("conversation_id", id)
      .order("created_at", { ascending: true })
      .limit(80);
    setMessages(msgs ?? []);
    const conv = conversations.find((c) => c.id === id) ?? null;
    setConversation(conv);
  }, [conversations]);

  const newConversation = useCallback(async () => {
    const { data: created } = await supabase
      .from("conversations")
      .insert({ title: `Baatein ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short" })}` })
      .select()
      .maybeSingle();
    if (created) {
      setConversation(created);
      setMessages([]);
      setConversations((c) => [created, ...c.filter((x) => x.id !== created.id)]);
    }
  }, []);

  return {
    conversation,
    conversations,
    messages,
    state,
    error,
    setError,
    memories,
    reminders,
    toasts,
    dismissToast,
    booted,
    status,
    send,
    setState,
    refreshReminders,
    forgetMemory,
    editMemory,
    editReminder,
    deleteReminder,
    snoozeReminder,
    completeReminder,
    clearChat,
    interrupt,
    retryLast,
    deepStatus,
    openConversation,
    newConversation,
  };
}
