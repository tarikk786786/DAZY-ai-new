# Identity Bug Fix — DAZY says “John” instead of “Tarik”

## Severity
High — trust and personalization defect. Must be fixed in web, desktop, backend prompt context, notifications, demo fixtures and tests.

## Desired behavior
The real user's DAZY display name is **Tarik**.

DAZY must not greet this user as John or Alex. Do not create fake email/account identifiers.

## Root-cause investigation checklist
Search the full repository for:
- `John`, `john`, `John Doe`
- `Alex`, `alex`
- `Demo User`, `defaultUser`, `mockUser`
- hard-coded greetings such as `Hello John`, `Welcome John`
- fallback objects in frontend stores
- seed users and demo fixtures accidentally loaded in production
- server-side prompt templates containing a static user name
- localStorage/session state shadowing the backend profile
- desktop companion constants or tray notification templates
- stale cached profile responses

Classify every match as production code, fixture, documentation, test, user content or irrelevant data. Do not replace unrelated occurrences such as author names in a sample repository.

## Canonical profile model

```ts
interface UserProfile {
  id: string;
  displayName: string;          // user-editable; Tarik for this account
  legalName?: string | null;    // optional, not inferred
  email?: string | null;        // verified value only
  avatarUrl?: string | null;
  timezone: string;             // Asia/Kolkata for this user's current setting
  locale?: string;
  profileVersion: number;
  updatedAt: string;
}
```

## Name resolution
1. Read canonical profile from authenticated backend `/api/me` (or existing equivalent).
2. Use `profile.displayName` when non-empty.
3. Otherwise use verified identity-provider display name and offer profile completion.
4. If still missing, use “Welcome back” or “there”; never default to John.
5. For the current configured account, save displayName = “Tarik” through the authenticated profile settings flow.
6. Propagate the same profileVersion into worker task context and notification rendering.

## Required fixes
- Main header and greeting.
- Avatar menu.
- Conversation header and new-chat greeting.
- Primary Brain system context.
- Worker/co-worker task context.
- Daily briefing salutation.
- Desktop mini panel and tray notifications.
- Email/notification templates.
- Welcome/onboarding screen.
- Demo fixture isolation.

Do not trust an LLM to infer the user's name from conversation history. The app profile is authoritative.

## Regression tests
- Signed-in profile displayName Tarik renders Tarik on web.
- Desktop uses the same profile API and displays Tarik.
- Reload preserves Tarik.
- Logout/login refreshes identity from authenticated profile, not stale local storage.
- Empty profile renders neutral greeting, not John.
- Prompt context includes the profile display name.
- Worker-created notifications use Tarik.
- Demo identity is shown only in explicit Demo Mode.
- Search for hard-coded John/Alex production fallbacks fails CI or is covered by an allowlisted fixture scan.

## Acceptance
No real-user screen, system prompt or notification uses “John” for this account. Display name is editable in Settings → Personalization and all surfaces update after save.
