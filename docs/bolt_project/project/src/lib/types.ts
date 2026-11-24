export interface Memory {
  id: string;
  category: string;
  key: string;
  value: string;
  importance: number;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  started_at: string;
  last_message_at: string;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  emotion: string | null;
  created_at: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
}

export interface ProviderHealth {
  id: string;
  configured: boolean;
  state: "healthy" | "unhealthy" | "unknown";
  model: string;
  latency_ms: number;
  detail: string;
  role: string;
  stats_24h: { total: number; ok: number; rate_limited: number; avg_ok_latency_ms: number };
}

export interface DazyStatus {
  ok: boolean;
  backend: { state: "healthy" | "unhealthy"; latency_ms: number; memories: number; open_reminders: number; messages_24h: number };
  rate_limit: { max_turns: number; window_secs: number };
  providers: ProviderHealth[];
  checked_at: string;
}

export interface Reminder {
  id: string;
  title: string;
  due_at: string;
  repeat: "once" | "daily" | "weekly";
  completed_at: string | null;
  created_at: string;
}

export type DazyEmotion =
  | "neutral"
  | "affection"
  | "happy"
  | "playful"
  | "empathetic"
  | "curious"
  | "excited"
  | "sad"
  | "serious"
  | "confident";

export type DazyState = "idle" | "listening" | "thinking" | "speaking";

export interface DazyReply {
  response: string;
  emotion: DazyEmotion;
  language: string;
  memory_saved?: { key: string; value: string } | null;
  reminder_set?: { title: string; due_at: string } | null;
  speak: string;
  provider_used?: string;
  model_used?: string;
  fallback_used?: boolean;
  latency_ms?: number;
  request_id?: string;
}
