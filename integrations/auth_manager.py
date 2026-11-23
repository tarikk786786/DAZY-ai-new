"""integrations/auth_manager.py — OAuth 2.0 and API Token Lifecycle Manager."""
from __future__ import annotations

import time
from typing import Any, Optional
from integrations.credential_manager import get_credential_manager
from integrations.http_client import get_shared_client


class AuthManager:
    """Manages OAuth2 token refresh and validation for integrated services."""

    def __init__(self):
        self.cred_mgr = get_credential_manager()
        self.http_client = get_shared_client()
        self._tokens: dict[str, dict[str, Any]] = {}

    def set_token(
        self,
        service: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: int = 3600,
        account: str = "default"
    ) -> None:
        expiry = time.time() + expires_in
        self._tokens[f"{service}:{account}"] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expiry": expiry,
        }
        self.cred_mgr.store_secret(service, f"{account}_access", access_token)
        if refresh_token:
            self.cred_mgr.store_secret(service, f"{account}_refresh", refresh_token)

    async def get_valid_token(
        self,
        service: str,
        refresh_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        account: str = "default"
    ) -> Optional[str]:
        """Returns active token, refreshing automatically if expired."""
        key = f"{service}:{account}"
        cached = self._tokens.get(key)
        
        # Check in-memory or stored secret
        access_token = cached.get("access_token") if cached else self.cred_mgr.get_secret(service, f"{account}_access")
        refresh_token = cached.get("refresh_token") if cached else self.cred_mgr.get_secret(service, f"{account}_refresh")
        expiry = cached.get("expiry", 0) if cached else 0

        # If token is still valid (with 60s buffer), return it
        if access_token and (expiry == 0 or time.time() < (expiry - 60)):
            return access_token

        # Attempt refresh if refresh_token and endpoint are provided
        if refresh_token and refresh_url and client_id and client_secret:
            try:
                resp = await self.http_client.post(
                    refresh_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    }
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    new_access = payload.get("access_token")
                    new_refresh = payload.get("refresh_token", refresh_token)
                    expires = int(payload.get("expires_in", 3600))
                    self.set_token(service, new_access, new_refresh, expires, account=account)
                    return new_access
            except Exception:
                pass

        return access_token


_GLOBAL_AUTH_MANAGER: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    global _GLOBAL_AUTH_MANAGER
    if _GLOBAL_AUTH_MANAGER is None:
        _GLOBAL_AUTH_MANAGER = AuthManager()
    return _GLOBAL_AUTH_MANAGER
