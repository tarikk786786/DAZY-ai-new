"""integrations/communication/telegram.py — Telegram Bot API Integration."""
from __future__ import annotations

from typing import Any, Optional
from integrations.base import BaseIntegration, HealthReport, IntegrationStatus
from integrations.credential_manager import get_credential_manager
from integrations.http_client import get_shared_client


class TelegramIntegration(BaseIntegration):
    """Sends notifications and alerts via Telegram Bot API."""

    def __init__(self):
        super().__init__(name="Telegram", category="communication")
        self.cred_mgr = get_credential_manager()
        self.http_client = get_shared_client()

    def _get_bot_token(self) -> Optional[str]:
        return self.cred_mgr.get_secret("telegram", "bot_token")

    async def check_health(self) -> HealthReport:
        token = self._get_bot_token()
        if not token:
            return HealthReport(healthy=False, status=IntegrationStatus.UNCONFIGURED, message="Bot token not configured")
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            resp = await self.http_client.get(url)
            ok = resp.status_code == 200 and resp.json().get("ok") is True
            return HealthReport(healthy=ok, status=IntegrationStatus.CONNECTED if ok else IntegrationStatus.ERROR)
        except Exception as e:
            return HealthReport(healthy=False, status=IntegrationStatus.ERROR, message=str(e))

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> dict[str, Any]:
        """Dispatches an alert or message to the user's Telegram chat."""
        token = self._get_bot_token()
        if not token:
            return {"error": "Telegram bot token is not configured"}

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        resp = await self.http_client.post(url, json_data=payload)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Failed to send message: HTTP {resp.status_code}"}
