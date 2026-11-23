"""integrations/google/gmail.py — Gmail REST API Integration."""
from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import Any, Optional
from integrations.base import BaseIntegration, HealthReport, IntegrationStatus
from integrations.auth_manager import get_auth_manager
from integrations.http_client import get_shared_client


class GmailIntegration(BaseIntegration):
    """Interacts with Gmail REST API via OAuth 2.0."""

    def __init__(self):
        super().__init__(name="Gmail", category="google")
        self.auth_mgr = get_auth_manager()
        self.http_client = get_shared_client()
        self.base_url = "https://gmail.googleapis.com/gmail/v1/users/me"

    async def _get_headers(self) -> dict[str, str]:
        token = await self.auth_mgr.get_valid_token("gmail")
        if not token:
            raise RuntimeError("Gmail account is not connected. Authenticate in DAZY settings.")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def list_recent_emails(self, query: str = "is:unread", max_results: int = 5) -> list[dict[str, Any]]:
        """Lists recent messages matching query."""
        try:
            headers = await self._get_headers()
            url = f"{self.base_url}/messages"
            params = {"q": query, "maxResults": max_results}
            resp = await self.http_client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                return resp.json().get("messages", [])
        except Exception as e:
            self.last_error = str(e)
        return []

    async def create_draft(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """Creates an email draft in Gmail."""
        headers = await self._get_headers()
        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        url = f"{self.base_url}/drafts"
        resp = await self.http_client.post(url, headers=headers, json_data={"message": {"raw": raw}})
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Failed to create draft: HTTP {resp.status_code}"}
