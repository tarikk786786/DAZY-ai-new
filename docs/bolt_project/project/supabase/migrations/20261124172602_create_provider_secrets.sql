/*
# Add private secrets store for provider keys

1. Purpose
   Stores third-party AI provider API keys (Groq, OpenRouter, DeepSeek) where the
   DAZY edge function can read them server-side. These must never be readable by
   browsers, so this table deliberately has NO public policies.

2. New Tables
   - `provider_secrets`
     - `name` (text, primary key) — e.g. "groq", "openrouter", "deepseek"
     - `value` (text) — the API key
     - `updated_at` (timestamptz)

3. Security
   - RLS ENABLED with NO policies → deny-all for anon/authenticated.
   - SELECT granted only to service_role (used by the edge function).
   - No anon or authenticated grants at all.

4. Notes
   - The earlier temporary copy of these keys in `preferences` is removed by the
     application immediately after this migration; this table is the only home.
*/

CREATE TABLE IF NOT EXISTS provider_secrets (
  name text PRIMARY KEY,
  value text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE provider_secrets ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON provider_secrets FROM anon, authenticated;
GRANT SELECT ON provider_secrets TO service_role;