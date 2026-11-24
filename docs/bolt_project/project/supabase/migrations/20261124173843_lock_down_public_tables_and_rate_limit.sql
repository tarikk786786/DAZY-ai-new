/*
# Tighten security: lock public chat tables, add rate limiting (retry 1)

Same as previous attempt; fixes column name `policyname` (not `policy_name`)
in the pg_policies catalog query.
*/
CREATE OR REPLACE FUNCTION public.rls_guard() RETURNS boolean
LANGUAGE plpgsql STABLE AS $$
BEGIN
  RETURN coalesce(
    current_setting('app.shared_secret', true) =
    current_setting('app.dazy_passphrase', true),
    false
  );
END;
$$;

REVOKE EXECUTE ON FUNCTION public.rls_guard() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.rls_guard() TO service_role;

DO $$
DECLARE
  t text;
  v text;
BEGIN
  FOREACH t IN ARRAY ARRAY['conversations','messages','memories','preferences','reminders'] LOOP
    FOR v IN SELECT policyname FROM pg_policies
             WHERE schemaname='public' AND tablename=t LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', v, t);
    END LOOP;

    EXECUTE format('CREATE POLICY rls_guard_select ON public.%I FOR SELECT TO anon, authenticated USING (public.rls_guard())', t);
    EXECUTE format('CREATE POLICY rls_guard_insert ON public.%I FOR INSERT TO anon, authenticated WITH CHECK (public.rls_guard())', t);
    EXECUTE format('CREATE POLICY rls_guard_update ON public.%I FOR UPDATE TO anon, authenticated USING (public.rls_guard()) WITH CHECK (public.rls_guard())', t);
    EXECUTE format('CREATE POLICY rls_guard_delete ON public.%I FOR DELETE TO anon, authenticated USING (public.rls_guard())', t);
  END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS public.chat_rate_limit (
  window_start timestamptz NOT NULL,
  turn_count integer NOT NULL DEFAULT 0,
  PRIMARY KEY (window_start)
);

ALTER TABLE public.chat_rate_limit ENABLE ROW LEVEL SECURITY;
GRANT ALL ON public.chat_rate_limit TO service_role;
REVOKE ALL ON public.chat_rate_limit FROM anon, authenticated;
