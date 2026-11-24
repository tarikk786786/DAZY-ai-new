# 12 — Security, privacy, known gaps and verification checklist

## High-priority findings from source inspection

### Desktop repository hygiene

The tracked `.agent/PROJECT_STATE.md` was observed to contain a dashboard PIN value and a truncated provider credential fragment. Treat any credential-like material committed to a public repository as potentially exposed. Do not reproduce it in this inventory. Rotate related API keys/session secrets/PINs where applicable, scrub Git history if a real secret was committed, and keep runtime secrets in ignored local files or a secret manager. Deleting a value only from the latest commit does not remove it from Git history.

The desktop `.gitignore` lists `config/api_keys.json`, OAuth credential/token files, `.env`, local memory DB/files and other personal/runtime data. Confirm no ignored files were accidentally committed in any branch/history.

### Web backend

- `supabase/config.toml`: `[functions.dazy-chat] verify_jwt = false`.
- Edge Function CORS allows `*`.
- Request body currently accepts `groq_api_key` and can pass it to the Groq provider.
- The function uses service-role Supabase client for `provider_secrets` and an anon client forwarding Authorization for user data.
- User identity ownership is not explicitly validated in the inspected function before use of `conversation_id`; confirm RLS, ownership policies and JWT handling.
- Edge Function logs provider error response snippets; sanitize logs and never emit request headers/keys.
- Provider calls have no explicit AbortSignal deadline in the inspected loop.
- Error response returns `providers_tried` and friendly fallback text but does not report actual provider/model metadata on success.
- Model JSON parse fallback can treat raw model output as response; validate schema and side effects server-side.

### Database/schema verification

Web README says run migrations in `supabase/migrations/`, but the inspected recursive tree did not include that directory. Confirm migrations are stored elsewhere or schema is managed in Supabase dashboard. Inspect RLS policies for `conversations`, `messages`, `memories`, `reminders` and `provider_secrets`. Verify no cross-user reads or writes are possible.

### Emotion and speech limitations

- Emotion2Vec adapter's inspected prediction method returns empty dict; not a full active emotion classifier.
- IndicConformer adapter in streaming ASR sets unavailable and returns empty unless implementation/runtime is added.
- Faster Whisper, Kokoro, Piper, openWakeWord and other local engines are optional and may require large downloads or extra packages.
- Web Speech API is browser-controlled and can behave differently across browsers/OS versions.
- Camera/face/speaker features require explicit consent, data minimization and clear indication. Do not treat facial or vocal emotion as a factual assessment.

### Integration and deployment gaps

- MCP framework exists; active external MCP server configuration has not been confirmed.
- Activepieces integration exists; remote instance connectivity and workflow state are unverified.
- Gmail/Telegram integrations exist; OAuth/bot credential setup is unverified.
- Mobile companion source exists; complete native Android/iOS builds are not established by this audit.
- Web and desktop do not yet share a single audited identity/memory/tool authorization contract.
- Web Gemini-primary provider upgrade is still pending in the inspected source.

## Must-run validation before production

1. Rotate any exposed credentials and audit full Git history.
2. Add server-side auth and ownership checks; do not leave user data endpoints unauthenticated.
3. Remove any provider API key field from browser payloads.
4. Put provider secrets in Edge Function secrets or a secure secret manager.
5. Restrict CORS to actual origins and supported methods.
6. Add provider-specific timeouts, bounded retries, circuit breaker and safe error sanitization.
7. Test all RLS policies using two independent test users.
8. Validate reminder timestamps, timezone, recurrence and idempotency.
9. Validate model output JSON before saving memory/reminders.
10. Add tests for rate limits, provider failures, empty/malformed responses and cross-user access.
11. Check local model memory/CPU on target 8GB PC.
12. Require human approval for sending messages, publishing workflows, file deletion, purchases and OS/security changes.
13. Pin MCP server versions and isolate untrusted execution.
14. Back up memory and provide export/delete controls.
