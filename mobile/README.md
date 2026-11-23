# DAZY Mobile Companion — Architecture & Integration

## 1. Overview
The DAZY Mobile Companion is a lightweight Android application designed to keep Tarik connected to DAZY wherever he goes without running heavy local neural nets or draining battery.

## 2. Key Capabilities
1. **Shared Memory Access**:
   - Reads user preferences, reminders, and knowledge from Supabase Cloud (`https://mllmkgwlkmbnaclanunr.supabase.co`).
2. **Proactive Mobile Alerts**:
   - Receives high-priority alerts (e.g. background task completed, urgent email) pushed from the Coolify FastAPI backend.
3. **Cross-Device Task Handoff**:
   - Allows Tarik to start a research or automation task on Windows PC, leave his desk, and inspect the verified results on Android.
4. **Secure QR / One-Time Code Pairing**:
   - Scans DAZY desktop QR code or enters a 6-digit one-time code to establish cryptographically signed mutual trust.
5. **Zero Screen Spying**:
   - Does not record the phone screen or collect unapproved private apps. Only communicates through authorized DAZY APIs.

## 3. Technology Stack
* **Language**: Kotlin with Jetpack Compose (or lightweight React Native)
* **Networking**: HTTPX / Retrofit2 + WebSockets
* **Cloud Sync**: Supabase Auth + Supabase PostgREST Client
* **Backend**: FastAPI on Coolify VPS
