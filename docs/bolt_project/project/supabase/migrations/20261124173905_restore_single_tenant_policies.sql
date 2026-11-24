/*
# Restore single-tenant data policies (revert passphrase-gated RLS)

1. Why
   The previous migration gated all data tables behind a server-side
   passphrase. That design conflicts with the app's no-sign-in architecture:
   the browser reads memories/reminders/conversations directly with the
   publishable anon key, so a passphrase gate locks the legitimate user out
   along with strangers. Reverting to the documented single-tenant posture
   (data intentionally shared; the real protection is that the project URL +
   anon key pair is never published, and provider keys stay server-side in
   the deny-all provider_secrets table).

2. Changes
   - conversations, messages, memories, preferences, reminders: recreate the
     4 standard policies each (select/insert/update/delete) with USING/WITH
     CHECK (true), TO anon, authenticated.
   - Keep the rls_guard function and chat_rate_limit table from the previous
     migration for the edge function's rate limiting.

3. Security
   - RLS remains enabled everywhere; provider_secrets and chat_rate_limit
     remain deny-all with no public grants.
*/
DO $$
DECLARE
  t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['conversations','messages','memories','preferences','reminders'] LOOP
    EXECUTE format('DROP POLICY IF EXISTS rls_guard_select ON public.%I', t);
    EXECUTE format('DROP POLICY IF EXISTS rls_guard_insert ON public.%I', t);
    EXECUTE format('DROP POLICY IF EXISTS rls_guard_update ON public.%I', t);
    EXECUTE format('DROP POLICY IF EXISTS rls_guard_delete ON public.%I', t);

    EXECUTE format('CREATE POLICY single_tenant_select ON public.%I FOR SELECT TO anon, authenticated USING (true)', t);
    EXECUTE format('CREATE POLICY single_tenant_insert ON public.%I FOR INSERT TO anon, authenticated WITH CHECK (true)', t);
    EXECUTE format('CREATE POLICY single_tenant_update ON public.%I FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true)', t);
    EXECUTE format('CREATE POLICY single_tenant_delete ON public.%I FOR DELETE TO anon, authenticated USING (true)', t);
  END LOOP;
END $$;
