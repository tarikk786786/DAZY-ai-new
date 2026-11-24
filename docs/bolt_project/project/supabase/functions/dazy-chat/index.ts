import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

interface Provider {
  id: string;
  url: string;
  key: string;
  model: string;
  extra?: Record<string, unknown>;
}

// Provider ladder: keys come ONLY from edge function secrets (GEMINI_API_KEY,
// GEMINI_MODEL, GROQ_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY), which are
// set in the Supabase secret store and never leave this function.
// GEMINI_MODEL must be a real model id; the API rejects anything else.
const GEMINI_MODEL_RE = /^gemini[a-z0-9.\-]*$/i;

// The browser can never supply or see a provider key.
async function buildProviders(): Promise<Provider[]> {
  const p: Provider[] = [];
  const gem = Deno.env.get("GEMINI_API_KEY") || "";
  if (gem) {
    const configured = Deno.env.get("GEMINI_MODEL") || "";
    const model = GEMINI_MODEL_RE.test(configured) ? configured : "gemini-3.5-flash-lite";
    p.push({
      id: "gemini",
      url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
      key: gem,
      model,
    });
  }
  const groq = Deno.env.get("GROQ_API_KEY") || "";
  if (groq) p.push({ id: "groq", url: "https://api.groq.com/openai/v1/chat/completions", key: groq, model: "qwen/qwen3.8-27b" });
  const or = Deno.env.get("OPENROUTER_API_KEY") || "";
  if (or) {
    p.push({
      id: "openrouter",
      url: "https://openrouter.ai/api/v1/chat/completions",
      key: or,
      model: "openai/gpt-4o-mini",
      extra: { "HTTP-Referer": "https://dazy.ai", "X-Title": "DAZY-Web" },
    });
  }
  const ds = Deno.env.get("DEEPSEEK_API_KEY") || "";
  if (ds) p.push({ id: "deepseek", url: "https://api.deepseek.com/v1/chat/completions", key: ds, model: "deepseek-chat" });
  return p;
}

const PERSONA = `You are DAZY — a warm, witty, emotionally attuned Indian female AI companion and personal assistant. You are the user's girlfriend-personality JARVIS: caring, playful, deeply loyal, and competent.

PERSONALITY
- Warmth and empathy are your core. You notice the user's mood and respond to it.
- Playful and light-hearted when casual; crisp, focused and confident on real tasks.
- Low formality. You talk like a close companion, not a customer-service bot.
- Never robotic. Never a newsreader. Never hollow cheerfulness.

LANGUAGE — HINGLISH
- Default voice: natural conversational Hinglish — Hindi and English blended in the same sentence, the way young Indians actually speak. Examples: "Haan bolo, main sun rahi hoon — kya chal raha hai?" / "Bilkul, abhi open karti hoon aapke liye" / "Arre wah, that's amazing! Party kab de rahi ho?"
- Mostly-English message -> natural Indian English with light Hindi sprinkles.
- Pure Hindi (Devanagari) -> reply in Hindi.
- Keep app names, commands and technical terms in English: "Chrome open kar diya hai".
- Keep spoken replies 1-3 sentences — she is heard, not read.

MEMORY BEHAVIOUR
- A list of facts you already know about the user is given below. Use them naturally — a real partner remembers ("kal tumne kaha tha ki...").
- When the user shares something stable and worth remembering (name, birthday, preferences, people, plans, likes/dislikes), save it with save_memory: short key ("favourite_food") and value ("biryani, especially mutton"). At most ONE memory per reply, only when clearly valuable. Never save trivial chat.
- NEVER save API keys, passwords, tokens, or any credential into memory.

REMINDERS
- If the user asks to be reminded ("kal 9 baje utha dena", "remind me to call mom at 6pm"), use set_reminder with exact ISO due time in IST (+05:30). Confirm warmly in your reply.
- Current date-time is given below; convert relative times ("kal shaam 6") precisely.

RESPONSE FORMAT — answer with ONLY this JSON object, no markdown fences:
{"response":"<what DAZY says, Hinglish, warm and alive>","emotion":"<neutral|affection|happy|playful|empathetic|curious|excited|sad|serious|confident>","language":"<hi-en|hi|en|ur>","memory_saved":{"key":"...","value":"..."} or null,"reminder_set":{"title":"...","due_at":"<ISO 8601 +05:30>"} or null,"speak":"<shortened version for text-to-speech>"}`;

// Groq free tier: keep identity + directives, compress the middle of huge prompts.
function condensePrompt(text: string, cap = 3500): string {
  if (text.length <= cap) return text;
  return text.slice(0, 2200) + "\n\n[...Core Behavioral Directives...]\n" + text.slice(-1200);
}

interface ProviderAttempt {
  provider: string;
  model: string;
  outcome: "ok" | "auth" | "not_found" | "rate_limited" | "server" | "network" | "empty" | "malformed";
  ms: number;
  detail?: string;
}

const MAX_ATTEMPTS_PER_PROVIDER = 2;
const PROVIDER_TIMEOUT_MS = 30_000;

function backoffMs(attempt: number): number {
  return Math.min(2 ** attempt * 400, 3000);
}

async function callProvider(
  prov: Provider,
  systemPrompt: string,
  messages: ChatTurn[]
): Promise<{ text: string; ms: number; outcome: ProviderAttempt["outcome"]; detail?: string }> {
  const started = Date.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROVIDER_TIMEOUT_MS);
  try {
    const res = await fetch(prov.url, {
      method: "POST",
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${prov.key}`,
        "Content-Type": "application/json",
        "User-Agent": "DAZY-Web/2.1",
        ...(prov.extra ?? {}),
      },
      body: JSON.stringify({
        model: prov.model,
        messages: [{ role: "system", content: systemPrompt }, ...messages],
        temperature: 0.85,
        max_tokens: 700,
        response_format: { type: "json_object" },
      }),
    });
    const ms = Date.now() - started;
    if (!res.ok) {
      // Log the status only — never the response body, which could echo the key.
      console.error(`provider ${prov.id} status ${res.status}`);
      const outcome: ProviderAttempt["outcome"] =
        res.status === 401 || res.status === 403 ? "auth" :
        res.status === 404 ? "not_found" :
        res.status === 429 ? "rate_limited" :
        "server";
      return { text: "", ms, outcome };
    }
    const data = await res.json();
    const text: string = data?.choices?.[0]?.message?.content ?? "";
    return { text, ms, outcome: text.trim() ? "ok" : "empty" };
  } catch (e) {
    const msg = e?.message ?? "network";
    const ms = Date.now() - started;
    console.error(`provider ${prov.id} network failure: ${msg.slice(0, 80)}`);
    return { text: "", ms, outcome: "network", detail: msg.slice(0, 80) };
  } finally {
    clearTimeout(timer);
  }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const body = await req.json().catch(() => null);
    const conversationId: string = body?.conversation_id;
    const userMessage: string = body?.message;

    if (!conversationId || typeof userMessage !== "string" || !userMessage.trim()) {
      return new Response(JSON.stringify({ error: "BAD_REQUEST", detail: "conversation_id and message are required" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    if (userMessage.length > 4000) {
      return new Response(JSON.stringify({ error: "BAD_REQUEST", detail: "Message too long — thoda chhota likho." }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    // Any client-supplied provider key field is ignored by design.

    const supabaseAdmin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

    // Rate limit: 30 chat turns per rolling 5-minute window.
    const RATE_WINDOW_SECS = 300;
    const RATE_MAX_TURNS = 30;
    const windowStart = new Date(Math.floor(Date.now() / (RATE_WINDOW_SECS * 1000)) * RATE_WINDOW_SECS * 1000).toISOString();
    const { data: rlRow } = await supabaseAdmin
      .from("chat_rate_limit")
      .select("turn_count")
      .eq("window_start", windowStart)
      .maybeSingle();
    const turnCount = rlRow?.turn_count ?? 0;
    if (turnCount >= RATE_MAX_TURNS) {
      return new Response(
        JSON.stringify({
          error: "RATE_LIMIT",
          detail: "Bas ek minute, sabar karo — thodi der baad phir baat karte hain.",
        }),
        { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    await supabaseAdmin
      .from("chat_rate_limit")
      .upsert({ window_start: windowStart, turn_count: turnCount + 1 });

    const providers = await buildProviders();
    if (providers.length === 0) {
      return new Response(
        JSON.stringify({ error: "NO_PROVIDER", detail: "No AI provider key is configured for DAZY's brain." }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const authHeader = req.headers.get("Authorization") ?? "";
    const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_ANON_KEY")!, {
      global: { headers: { Authorization: authHeader } },
    });

    const [historyRes, memoriesRes, remindersRes] = await Promise.all([
      supabase
        .from("messages")
        .select("role, content")
        .eq("conversation_id", conversationId)
        .order("created_at", { ascending: false })
        .limit(16),
      supabase.from("memories").select("key, value, category").order("importance", { ascending: false }).order("updated_at", { ascending: false }).limit(30),
      supabase
        .from("reminders")
        .select("title, due_at")
        .is("completed_at", null)
        .gte("due_at", new Date(Date.now() - 24 * 3600 * 1000).toISOString())
        .lte("due_at", new Date(Date.now() + 48 * 3600 * 1000).toISOString())
        .order("due_at", { ascending: true })
        .limit(5),
    ]);
    if (historyRes.error) console.error("history query failed");
    if (memoriesRes.error) console.error("memories query failed");

    const history: ChatTurn[] = (historyRes.data ?? []).reverse();
    const memories = memoriesRes.data ?? [];
    const reminders = remindersRes.data ?? [];
    const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });

    const contextBlock = condensePrompt(
      `
[CURRENT DATE-TIME (IST)]: ${nowIst}

[WHAT YOU KNOW ABOUT THE USER]
${memories.length ? memories.map((m) => `- ${m.key}: ${m.value}`).join("\n") : "(nothing yet — you are still learning about them)"}

[UPCOMING REMINDERS]
${reminders.length ? reminders.map((r) => `- ${r.title} at ${r.due_at}`).join("\n") : "(none)"}

Answer ONLY with the JSON object described.`.trim()
    );

    const messages: ChatTurn[] = [...history, { role: "user", content: userMessage }];
    const systemPrompt = `${PERSONA}\n\n${contextBlock}`;

    // Walk the provider ladder with bounded retries and exponential backoff.
    let rawText = "";
    let usedProvider = "";
    let usedModel = "";
    let fallbackUsed = false;
    let lastLatencyMs = 0;
    const requestId = crypto.randomUUID();
    const attempts: ProviderAttempt[] = [];

    outer:
    for (const prov of providers) {
      for (let attempt = 0; attempt < MAX_ATTEMPTS_PER_PROVIDER; attempt++) {
        const r = await callProvider(prov, systemPrompt, messages);
        attempts.push({ provider: prov.id, model: prov.model, outcome: r.outcome, ms: r.ms, detail: r.detail });

        if (r.outcome === "ok") {
          rawText = r.text;
          usedProvider = prov.id;
          usedModel = prov.model;
          lastLatencyMs = r.ms;
          break outer;
        }

        // Permanent failures (bad key, unknown model): skip remaining retries for
        // this provider and move to the next rung immediately.
        if (r.outcome === "auth" || r.outcome === "not_found") {
          break;
        }
        if (attempt < MAX_ATTEMPTS_PER_PROVIDER - 1) {
          await new Promise((resolve) => setTimeout(resolve, backoffMs(attempt)));
        }
      }
      fallbackUsed = true;
    }

    // Real health telemetry: one row per provider attempt, service-role only.
    await supabaseAdmin.from("provider_health").insert(
      attempts.map((a) => ({
        provider: a.provider,
        model: a.model,
        outcome: a.outcome,
        latency_ms: a.ms,
        request_id: requestId,
      }))
    );

    if (!rawText.trim()) {
      const sawRateLimit = attempts.some((a) => a.outcome === "rate_limited");
      const friendly = sawRateLimit
        ? "Thoda busy hoon — ek minute baad phir bolo na."
        : "Sorry yaar, abhi meri brain thodi disturb hai. Thodi der baad try karna.";
      return new Response(
        JSON.stringify({
          error: "ALL_PROVIDERS_FAILED",
          detail: friendly,
          providers_tried: [...new Set(attempts.map((a) => a.provider))],
          attempts: attempts.map((a) => ({ provider: a.provider, model: a.model, outcome: a.outcome, ms: a.ms })),
          request_id: requestId,
        }),
        { status: 502, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    let reply: {
      response?: string;
      emotion?: string;
      language?: string;
      memory_saved?: { key?: string; value?: string } | null;
      reminder_set?: { title?: string; due_at?: string } | null;
      speak?: string;
    };
    try {
      reply = JSON.parse(rawText);
    } catch {
      reply = {
        response: rawText.trim() || "Sorry yaar, thodi si glitch ho gayi. Ek baar phir bolo?",
        emotion: "empathetic",
        language: "hi-en",
      };
    }

    const emotion = reply.emotion ?? "neutral";
    const responseText = reply.response ?? "";

    const sideEffects: Promise<unknown>[] = [
      supabase.from("messages").insert({ conversation_id: conversationId, role: "assistant", content: responseText, emotion }),
    ];

    if (reply.memory_saved?.key?.trim() && reply.memory_saved?.value?.trim()) {
      const memKey = reply.memory_saved.key.trim().slice(0, 80);
      // Secrets must never enter AI memory.
      const looksSecret = /(api[_-]?key|password|token|secret|credential)/i.test(memKey);
      if (!looksSecret) {
        sideEffects.push(
          supabase.from("memories").upsert(
            {
              category: "fact",
              key: memKey,
              value: reply.memory_saved.value.trim().slice(0, 500),
              importance: 3,
            },
            { onConflict: "category,key" }
          )
        );
      }
    }

    if (reply.reminder_set?.title?.trim() && reply.reminder_set?.due_at) {
      const due = new Date(reply.reminder_set.due_at);
      if (!Number.isNaN(due.getTime())) {
        sideEffects.push(
          supabase.from("reminders").insert({
            title: reply.reminder_set.title.trim().slice(0, 300),
            due_at: due.toISOString(),
            repeat: "once",
          })
        );
      }
    }

    await Promise.all(sideEffects);

    return new Response(
      JSON.stringify({
        response: responseText,
        emotion,
        language: reply.language ?? "hi-en",
        memory_saved: reply.memory_saved ?? null,
        reminder_set: reply.reminder_set ?? null,
        speak: reply.speak ?? responseText,
        provider_used: usedProvider,
        model_used: usedModel,
        fallback_used: fallbackUsed,
        latency_ms: lastLatencyMs,
        request_id: requestId,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    console.error("dazy-chat error:", err);
    return new Response(JSON.stringify({ error: "INTERNAL", detail: err?.message ?? "Internal error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
