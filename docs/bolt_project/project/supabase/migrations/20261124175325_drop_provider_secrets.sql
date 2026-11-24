/*
# Remove provider_secrets table (superseded by Edge Function secret storage)

1. Why
   Provider API keys are now read from Supabase Edge Function environment
   secrets (GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, OPENROUTER_API_KEY,
   DEEPSEEK_API_KEY), which are never queryable and never leave the function.
   The provider_secrets table is therefore redundant attack surface.

2. Data safety
   The table contains only API key strings (no user data). The user's Gemini
   key has already been copied into the function-secret store before this
   migration runs, so no credential is lost.

3. Changes
   - Drops table public.provider_secrets.
   - No other object references it (verified: only the edge function read it).

4. Security
   - Removes a server-side credential store in favour of the platform secret
     store, shrinking the auditable surface.
*/
DROP TABLE IF EXISTS public.provider_secrets;
