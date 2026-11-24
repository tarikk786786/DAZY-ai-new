/*
# Add provider health telemetry (30-day rolling log)

1. Why
   The dashboard needs REAL health data — never simulated. The edge function
   now writes one row per provider attempt with outcome and latency. This
   gives: last success, latency, failure counts, and rate-limit events, all
   sourced from actual traffic.

2. New table
   - public.provider_health
     * id uuid pk default gen_random_uuid()
     * ts timestamptz default now()
     * provider text (gemini|groq|openrouter|deepseek)
     * model text
     * outcome text (ok|auth|not_found|rate_limited|server|network|empty|malformed)
     * latency_ms integer
     * request_id uuid
   - Index on ts for rolling-window queries.

3. Security
   - RLS enabled; no public policies; no grants to anon/authenticated —
     only the edge function (service role) writes and reads it.
     The frontend gets health via a read-only service-computed view later
     if needed; for now nothing leaks to the browser.
*/
CREATE TABLE IF NOT EXISTS public.provider_health (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ts timestamptz NOT NULL DEFAULT now(),
  provider text NOT NULL,
  model text NOT NULL,
  outcome text NOT NULL,
  latency_ms integer NOT NULL DEFAULT 0,
  request_id uuid
);
CREATE INDEX IF NOT EXISTS idx_provider_health_ts ON public.provider_health (ts DESC);

ALTER TABLE public.provider_health ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.provider_health FROM anon, authenticated;
GRANT ALL ON public.provider_health TO service_role;
