# Focused Prompt — Fix “John” to “Tarik” and Main UI

Audit the full DAZY project and fix the incorrect user greeting.

1. Search all production source, prompts, templates, state stores, seed data, desktop UI and notification code for hard-coded `John`, `John Doe`, `Alex`, `Demo User` and default identity objects.
2. Identify the real source of the wrong name. Do not perform a blind global replace.
3. Add or repair one canonical authenticated `/api/me` profile endpoint (or the existing equivalent).
4. Store editable `displayName = "Tarik"` for this user's profile.
5. Resolve greeting from profile data; use neutral greeting if profile is unavailable.
6. Propagate profile data to the primary brain, secondary agents, worker contexts, daily briefing and notifications.
7. Ensure desktop and web consume the same profile.
8. Add Settings → Personalization with name, avatar and timezone controls.
9. Add a top-right profile chip and main page greeting “Good [time of day], Tarik”.
10. Add regression tests for login, reload, token refresh, desktop launch, worker prompts, notification templates and empty profile.
11. Ensure dummy identities only render in explicit Demo Mode.
12. Update main UI fixtures and documentation. Reference screenshots may contain placeholders; do not copy them into real runtime data.

Acceptance: no production user-facing surface calls this account John. All components use the canonical profile and changes persist after restart.
