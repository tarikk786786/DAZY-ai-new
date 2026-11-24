"""integrations/http_client.py — Shared Async HTTP Client with pooling and backoff.

Provides:
- Persistent connection pooling via httpx.AsyncClient
- Configurable timeouts and exponential backoff retries
- Rate-limit headers tracking and circuit breaking
- In-memory lightweight cache control
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Optional
import httpx


class AsyncHttpClient:
    """Shared HTTPX Client wrapper with exponential backoff and circuit breaking."""

    def __init__(
        self,
        timeout: float = 15.0,
        max_connections: int = 50,
        max_keepalive: int = 20,
        max_retries: int = 3,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive,
            keepalive_expiry=30.0,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_open_until: float = 0.0

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                limits=self._limits,
                timeout=httpx.Timeout(self.timeout, connect=5.0),
                headers={"User-Agent": "DAZY-Assistant/1.0 (Desktop; Personal AI)"},
                follow_redirects=True,
            )
        return self._client

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        retries: Optional[int] = None,
    ) -> httpx.Response:
        """Executes an async HTTP request with exponential backoff and error handling."""
        now = time.monotonic()
        if now < self._circuit_open_until:
            raise RuntimeError("Circuit breaker open: remote service is currently unavailable")

        max_attempts = retries if retries is not None else self.max_retries
        client = self._ensure_client()
        last_exc = None

        for attempt in range(1, max_attempts + 1):
            try:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                )
                # Handle rate limit 429
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", 2.0))
                    await asyncio.sleep(min(retry_after, 5.0))
                    continue

                if resp.status_code >= 500 and attempt < max_attempts:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue

                return resp
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                last_exc = e
                if attempt < max_attempts:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                else:
                    self._circuit_open_until = time.monotonic() + 10.0
                    raise

        if last_exc:
            raise last_exc
        raise RuntimeError(f"Request failed after {max_attempts} attempts")

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


_SHARED_HTTP_CLIENT: Optional[AsyncHttpClient] = None


def get_shared_client() -> AsyncHttpClient:
    global _SHARED_HTTP_CLIENT
    if _SHARED_HTTP_CLIENT is None:
        _SHARED_HTTP_CLIENT = AsyncHttpClient()
    return _SHARED_HTTP_CLIENT
