"""integrations/credential_manager.py — Secure Credential Storage for DAZY.

Integrates with Windows Credential Manager (via keyring if installed)
with a fallback to local encrypted/obscured storage. Never writes plaintext
secrets to general config or logs.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
_VAULT_FILE = _ROOT / "memory" / ".vault.dat"


class CredentialManager:
    """Stores and retrieves API tokens and OAuth secrets securely."""

    def __init__(self, service_prefix: str = "DAZY_ASSISTANT"):
        self.service_prefix = service_prefix
        self._has_keyring = False
        try:
            import keyring
            self._keyring = keyring
            self._has_keyring = True
        except ImportError:
            self._keyring = None

    def store_secret(self, service: str, account: str, secret: str) -> bool:
        """Stores a secret key or token securely."""
        if not service or not secret:
            return False

        sec_name = f"{self.service_prefix}_{service.upper()}"
        if self._has_keyring and self._keyring:
            try:
                self._keyring.set_password(sec_name, account, secret)
                return True
            except Exception:
                pass

        # Fallback to local obscured vault file
        try:
            vault = self._load_vault()
            key = f"{sec_name}:{account}"
            vault[key] = base64.b64encode(secret.encode("utf-8")).decode("ascii")
            self._save_vault(vault)
            return True
        except Exception:
            return False

    def get_secret(self, service: str, account: str = "default") -> Optional[str]:
        """Retrieves a stored secret token."""
        sec_name = f"{self.service_prefix}_{service.upper()}"
        if self._has_keyring and self._keyring:
            try:
                secret = self._keyring.get_password(sec_name, account)
                if secret:
                    return secret
            except Exception:
                pass

        # Check local vault fallback
        vault = self._load_vault()
        key = f"{sec_name}:{account}"
        b64_val = vault.get(key)
        if b64_val:
            try:
                return base64.b64decode(b64_val.encode("ascii")).decode("utf-8")
            except Exception:
                pass

        # Also check environment variables (DAZY_<SERVICE>_KEY or <SERVICE>_API_KEY)
        env_candidates = [
            f"{self.service_prefix}_{service.upper()}_KEY",
            f"{service.upper()}_API_KEY",
            f"{service.upper()}_TOKEN",
        ]
        for env_var in env_candidates:
            val = os.environ.get(env_var)
            if val:
                return val.strip()

        return None

    def delete_secret(self, service: str, account: str = "default") -> bool:
        """Removes a stored secret."""
        sec_name = f"{self.service_prefix}_{service.upper()}"
        if self._has_keyring and self._keyring:
            try:
                self._keyring.delete_password(sec_name, account)
            except Exception:
                pass
        vault = self._load_vault()
        key = f"{sec_name}:{account}"
        if key in vault:
            vault.pop(key, None)
            self._save_vault(vault)
        return True

    def _load_vault(self) -> dict[str, str]:
        if not _VAULT_FILE.is_file():
            return {}
        try:
            return json.loads(_VAULT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_vault(self, data: dict[str, str]) -> None:
        _VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
        _VAULT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


_GLOBAL_CRED_MANAGER: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    global _GLOBAL_CRED_MANAGER
    if _GLOBAL_CRED_MANAGER is None:
        _GLOBAL_CRED_MANAGER = CredentialManager()
    return _GLOBAL_CRED_MANAGER
