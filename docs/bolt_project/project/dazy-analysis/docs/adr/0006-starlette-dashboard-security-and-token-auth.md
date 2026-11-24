# ADR-0006: Starlette Dashboard Security & AES-256-GCM Audio Security

* **Status:** Accepted
* **Deciders:** Security Auditor, Principal Architect
* **Date:** 2026-11-24

## Context and Problem Statement
The remote web dashboard provides system status, command input, pronunciation dictionaries, and real-time audio streaming. Unauthenticated or insecure endpoints on local networks expose host control and microphone audio to unauthorized LAN actors.

## Decision Drivers
* Protection against unauthorized LAN access.
* Tamper-proof, authenticated transport for phone microphone audio relays.
* Rate limiting and brute-force protection against PIN guessing.

## Considered Options
1. **Bearer Token Authentication with HMAC PIN verification and AES-256-GCM**:
   - Constant-time PIN comparison (`secrets.compare_digest`).
   - Ephemeral bearer tokens with 12-hour TTL.
   - Lockout after 6 failed attempts.
   - AES-256-GCM with unique 12-byte IV per audio block.
2. Unauthenticated local dashboard.
3. AES-CBC encryption without integrity authentication.

## Decision Outcome
Chosen option: **Bearer Token Authentication with HMAC PIN verification and AES-256-GCM**.
Implemented in `dashboard/server.py`. All sensitive REST endpoints (`/api/voice-diagnostics`, `/api/pronunciation`, `/api/voice-mode`) and WebSockets require valid bearer tokens.

### Positive Consequences
* Zero unauthorized command execution.
* Eavesdropping and bit-flipping attacks on phone audio relays are prevented.
* Seamless single-page app (SPA) experience with secure session storage.
