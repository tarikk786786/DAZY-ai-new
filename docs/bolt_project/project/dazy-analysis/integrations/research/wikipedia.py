"""integrations/research/wikipedia.py — Wikipedia REST API Integration."""
from __future__ import annotations

import urllib.parse
from typing import Any, Optional
from integrations.base import BaseIntegration, HealthReport, IntegrationStatus
from integrations.http_client import get_shared_client


class WikipediaIntegration(BaseIntegration):
    """Retrieves encyclopedic summaries and article links via Wikipedia REST API."""

    def __init__(self):
        super().__init__(name="Wikipedia", category="research")
        self.http_client = get_shared_client()
        self.status = IntegrationStatus.CONNECTED

    async def get_summary(self, title: str, lang: str = "en") -> dict[str, Any]:
        """Fetches page summary including extract and thumbnail."""
        enc_title = urllib.parse.quote(title.strip().replace(" ", "_"))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{enc_title}"
        resp = await self.http_client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title"),
                "extract": data.get("extract"),
                "description": data.get("description"),
                "page_url": data.get("content_urls", {}).get("desktop", {}).get("page"),
            }
        return {"error": f"Page '{title}' not found (HTTP {resp.status_code})"}

    async def search_articles(self, query: str, lang: str = "en", limit: int = 5) -> list[dict[str, str]]:
        """Searches Wikipedia pages by keyword query."""
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "namespace": 0,
            "format": "json",
        }
        resp = await self.http_client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) >= 4:
                titles = data[1]
                snippets = data[2]
                urls = data[3]
                return [{"title": t, "snippet": s, "url": u} for t, s, u in zip(titles, snippets, urls)]
        return []
