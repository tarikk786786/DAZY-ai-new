import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface ProviderDef {
  id: string;
  url: string;
  model: string;
  envKey: string;
  testMessage: string;
}

// GEMINI_MODEL must be a real model id; the API rejects anything else.
const GEMINI_MODEL_RE = /^gemini[a-z0-9.\-]*$/i;
const GEMINI_DEFAULT = "gemini-3.5-flash-lite";
const GEMINI_EFFECTIVE = GEMINI_MODEL_RE.test(Deno.env.get("GEMINI_MODEL") || "") ? Deno.env.get("GEMINI_MODEL")! : GEMINI_DEFAULT;

// Mirrors the chat ladder's order. Test requests are 5-token pings —
// real requests, real outcomes, never simulated.
const PROVIDERS: ProviderDef[] = [
  {
    id: "gemini",
    url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    model: GEMINI_EFFECTIVE,
    envKey: "GEMINI_API_KEY",
    testMessage: "Reply with exactly: online",
  },
  { id: "groq", url: "https://api.groq.com/openai/v1/chat/completions", model: "qwen/qwen3.8-27b", envKey: "GROQ_API_KEY", testMessage: "Reply with exactly: online" },
  {
    id: "openrouter",
    url: "https://openrouter.ai/api/v1/chat/completions",
    model: "openai/gpt-4o-mini",
    envKey: "OPENROUTER_API_KEY",
    testMessage: "Reply with exactly: online",
  },
  { id: "deepseek", url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-chat", envKey: "DEEPSEEK_API_KEY", testMessage: "Reply with exactly: online" },
];

async function testProvider(p: ProviderDef): Promise<{ id: string; configured: boolean; state: "healthy" | "unhealthy" | "unknown"; model: string; latency_ms: number; detail: string }> {
  const key = Deno.env.get(p.envKey) || "";
  if (!key) {
    return { id: p.id, configured: false, state: "unknown", model: p.model, latency_ms: 0, detail: "not configured" };
  }
  const started = Date.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15_000);
  try {
    const res = await fetch(p.url, {
      method: "POST",
      signal: controller.signal,
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: p.model,
        messages: [{ role: "user", content: p.testMessage }],
        max_tokens: 5,
      }),
    });
    const ms = Date.now() - started;
    if (res.ok) {
      const data = await res.json();
      const text: string = data?.choices?.[0]?.message?.content ?? "";
      if (text.trim()) return { id: p.id, configured: true, state: "healthy", model: p.model, latency_ms: ms, detail: "ok" };
      return { id: p.id, configured: true, state: "unhealthy", model: p.model, latency_ms: ms, detail: "empty reply" };
    }
    // Status code only — never log the body (could echo the key).
    const label = res.status === 401 || res.status === 403 ? "auth failed" : res.status === 404 ? "model not found" : res.status === 429 ? "rate limited" : `http ${res.status}`;
    return { id: p.id, configured: true, state: "unhealthy", model: p.model, latency_ms: ms, detail: label };
  } catch (e) {
    const ms = Date.now() - started;
    const msg = e?.message ?? "network";
    return { id: p.id, configured: true, state: "unhealthy", model: p.model, latency_ms: ms, detail: msg.includes("Abort") ? "timeout" : "network error" };
  } finally {
    clearTimeout(timer);
  }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const auth = req.headers.get("Authorization") ?? "";
  if (!auth.startsWith("Bearer ")) {
    return new Response(JSON.stringify({ error: "UNAUTHORIZED" }), { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } });
  }

  try {
    const url = new URL(req.url);
    const deep = url.searchParams.get("deep") === "true";

    const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
    // Aggregate REAL attempt telemetry from the last 24h.
    const since = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    const { data: stats, error: statsErr } = await admin
      .from("provider_health")
      .select("provider, outcome, latency_ms")
      .gte("ts", since);
    if (statsErr) console.error("provider_health query failed");

    const byProvider = new Map<string, { total: number; ok: number; rateLimited: number; avgLatency: number }>();
    for (const row of stats ?? []) {
      const s = byProvider.get(row.provider) ?? { total: 0, ok: 0, rateLimited: 0, avgLatency: 0 };
      s.total++;
      if (row.outcome === "ok") { s.ok++; s.avgLatency += row.latency_ms; }
      if (row.outcome === "rate_limited") s.rateLimited++;
      byProvider.set(row.provider, s);
    }

    // Deep mode actually pings each provider (slower, ~1-3s). Default: cheap.
    const providers = await Promise.all(
      PROVIDERS.map(async (p) => {
        const base = deep ? await testProvider(p) : { id: p.id, configured: !!Deno.env.get(p.envKey), state: "unknown" as const, model: p.model, latency_ms: 0, detail: deep ? "" : "not probed (use ?deep=true)" };
        const s = byProvider.get(p.id);
        return {
          ...base,
          role: p.id === "gemini" ? "primary" : "fallback",
          stats_24h: s
            ? {
                total: s.total,
                ok: s.ok,
                rate_limited: s.rateLimited,
                avg_ok_latency_ms: s.ok > 0 ? Math.round(s.avgLatency / s.ok) : 0,
              }
            : { total: 0, ok: 0, rate_limited: 0, avg_ok_latency_ms: 0 },
        };
      })
    );

    // Database health: real read probe through service role (non-destructive).
    let dbState: "healthy" | "unhealthy" = "unhealthy";
    const dbStarted = Date.now();
    const { count, error: countErr } = await admin.from("memories").select("id", { count: "exact", head: true });
    const dbLatency = Date.now() - dbStarted;
    if (!countErr && count !== null) dbState = "healthy";

    // Config health from real tables.
    const { count: memCount } = await admin.from("memories").select("id", { count: "exact", head: true });
    const { count: remCount } = await admin.from("reminders").select("id", { count: "exact", head: true }).is("completed_at", null);
    const { count: msgCount24h } = await admin
      .from("messages")
      .select("id", { count: "exact", head: true })
      .gte("created_at", since);

    return new Response(
      JSON.stringify({
        ok: true,
        backend: { state: dbState, latency_ms: dbLatency, memories: memCount ?? 0, open_reminders: remCount ?? 0, messages_24h: msgCount24h ?? 0 },
        rate_limit: { max_turns: 30, window_secs: 300 },
        providers,
        checked_at: new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    console.error("dazy-status error");
    return new Response(JSON.stringify({ error: "INTERNAL" }), { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } });
  }
});
