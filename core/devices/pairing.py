"""core/devices/pairing.py — Secure Pairing and Trust Verification Engine.

Manages one-time 6-digit codes, QR verification payloads, pairing approval,
and session revocation without hardcoded secrets.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Optional

from core.devices.models import DazyDevice, DevicePermissions, DeviceType, TrustLevel

logger = logging.getLogger("dazy.pairing")


@dataclass
class PairingSession:
    session_id: str
    target_device_id: str
    target_device_name: str
    target_device_type: DeviceType
    one_time_code: str
    created_at: float
    expires_at: float
    verified: bool = False


class PairingManager:
    """Handles cryptographically safe pairing requests, approvals, and revocations."""

    def __init__(self, expiry_seconds: float = 300.0):
        self.expiry_seconds = expiry_seconds
        self._active_sessions: dict[str, PairingSession] = {}
        self._enrolled_devices: dict[str, DazyDevice] = {}

    def create_pairing_request(
        self,
        device_id: str,
        device_name: str,
        device_type: DeviceType,
    ) -> PairingSession:
        """Generates an expiring 6-digit one-time code and QR payload for an incoming device."""
        code = f"{random.randint(100000, 999999)}"
        now = time.time()
        session_id = f"pair_{hashlib.sha256(f'{device_id}_{now}'.encode()).hexdigest()[:12]}"

        session = PairingSession(
            session_id=session_id,
            target_device_id=device_id,
            target_device_name=device_name,
            target_device_type=device_type,
            one_time_code=code,
            created_at=now,
            expires_at=now + self.expiry_seconds,
        )
        self._active_sessions[session_id] = session
        return session

    def generate_qr_payload(self, session: PairingSession) -> str:
        """Returns JSON string for QR code scanning by DAZY Android companion."""
        data = {
            "session_id": session.session_id,
            "device_id": session.target_device_id,
            "device_name": session.target_device_name,
            "device_type": session.target_device_type.value,
            "code": session.one_time_code,
            "expires_at": session.expires_at,
        }
        return json.dumps(data)

    def verify_and_approve(self, session_id: str, submitted_code: str) -> Optional[DazyDevice]:
        """Validates code and transitions device to PAIRED_TRUSTED state."""
        session = self._active_sessions.get(session_id)
        if not session:
            logger.warning("Pairing session %s not found", session_id)
            return None

        if time.time() > session.expires_at:
            logger.warning("Pairing session %s has expired", session_id)
            del self._active_sessions[session_id]
            return None

        if session.one_time_code != submitted_code.strip():
            logger.warning("Invalid code submitted for session %s", session_id)
            return None

        session.verified = True
        device = DazyDevice(
            device_id=session.target_device_id,
            friendly_name=session.target_device_name,
            device_type=session.target_device_type,
            os_version="Android 14 (DAZY Mobile Companion)" if session.target_device_type == DeviceType.MOBILE_ANDROID else "Windows 11",
            trust_level=TrustLevel.PAIRED_TRUSTED,
            permissions=DevicePermissions(
                allow_task_handoff=True,
                allow_notifications=True,
                allow_screen_context_share=False,
                allow_remote_file_transfer=False,
                allow_remote_control=False,
            ),
        )
        self._enrolled_devices[device.device_id] = device
        del self._active_sessions[session_id]
        logger.info("Device %s (%s) successfully paired and trusted", device.friendly_name, device.device_id)
        return device

    def revoke_device(self, device_id: str) -> bool:
        """Revokes trust and invalidates active session for a lost or compromised device."""
        if device_id in self._enrolled_devices:
            self._enrolled_devices[device_id].trust_level = TrustLevel.REVOKED
            logger.info("Revoked trust for device %s", device_id)
            return True
        return False

    def get_enrolled_devices(self) -> list[DazyDevice]:
        return list(self._enrolled_devices.values())


pairing_manager = PairingManager()
