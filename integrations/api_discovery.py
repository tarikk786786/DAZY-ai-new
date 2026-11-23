"""integrations/api_discovery.py — Lightweight Public API and Integration Discovery.

Queries:
- public-apis catalogue
- APIs.guru OpenAPI directory
- GitHub REST API for libraries and tools
Fetches metadata on demand without cloning giant repositories.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional
from integrations.http_client import get_shared_client


@dataclass
class APISpecSummary:
    name: str
    category: str
    description: str
    auth_type: str             # "None" | "apiKey" | "OAuth"
    is_free: bool = True
    docs_url: str = ""
    openapi_url: str = ""


# Vetted curated free public APIs readily usable by DAZY
CURATED_FREE_APIS: list[APISpecSummary] = [
    APISpecSummary(
        name="Open-Meteo",
        category="Weather",
        description="Free weather forecasts and historical climate data without API keys",
        auth_type="None",
        is_free=True,
        docs_url="https://open-meteo.com/en/docs",
    ),
    APISpecSummary(
        name="Wikipedia REST API",
        category="Knowledge",
        description="Structured encyclopedic summaries and article search",
        auth_type="None",
        is_free=True,
        docs_url="https://en.wikipedia.org/api/rest_v1/",
    ),
    APISpecSummary(
        name="OpenAlex",
        category="Research",
        description="Open catalog of 250M+ scientific research papers, authors, and institutions",
        auth_type="None",
        is_free=True,
        docs_url="https://docs.openalex.org/",
    ),
    APISpecSummary(
        name="Crossref",
        category="Research",
        description="Digital object identifier (DOI) metadata and scholarly publication lookup",
        auth_type="None",
        is_free=True,
        docs_url="https://api.crossref.org/",
    ),
    APISpecSummary(
        name="arXiv API",
        category="Research",
        description="Search preprints across computer science, physics, mathematics, and quantitative biology",
        auth_type="None",
        is_free=True,
        docs_url="https://arxiv.org/help/api/",
    ),
    APISpecSummary(
        name="Quran Foundation & QuranEnc",
        category="Islamic Knowledge",
        description="Authentic multi-lingual translations, Arabic text, and verse commentary",
        auth_type="None",
        is_free=True,
        docs_url="https://api-docs.quran.com/",
    ),
]


class APIDiscoveryManager:
    """Discovers and caches external public API capabilities."""

    def __init__(self):
        self.http_client = get_shared_client()
        self._curated = {api.name.lower(): api for api in CURATED_FREE_APIS}

    def search_curated(self, query: str) -> list[APISpecSummary]:
        """Searches vetted zero-cost APIs by keyword."""
        q = query.lower().strip()
        results = []
        for api in self._curated.values():
            if q in api.name.lower() or q in api.category.lower() or q in api.description.lower():
                results.append(api)
        return results or list(self._curated.values())

    async def search_apis_guru(self, query: str) -> list[dict[str, Any]]:
        """Queries APIs.guru directory API for machine-readable OpenAPI specifications."""
        try:
            url = "https://api.apis.guru/v2/list.json"
            resp = await self.http_client.get(url, retries=1)
            if resp.status_code == 200:
                data = resp.json()
                matches = []
                q = query.lower()
                for key, val in data.items():
                    if q in key.lower():
                        preferred = val.get("preferred")
                        ver_data = val.get("versions", {}).get(preferred, {})
                        info = ver_data.get("info", {})
                        matches.append({
                            "name": info.get("title", key),
                            "description": info.get("description", "")[:160],
                            "swaggerUrl": ver_data.get("swaggerUrl", ""),
                        })
                        if len(matches) >= 5:
                            break
                return matches
        except Exception:
            pass
        return []


_GLOBAL_API_DISCOVERY: Optional[APIDiscoveryManager] = None


def get_api_discovery_manager() -> APIDiscoveryManager:
    global _GLOBAL_API_DISCOVERY
    if _GLOBAL_API_DISCOVERY is None:
        _GLOBAL_API_DISCOVERY = APIDiscoveryManager()
    return _GLOBAL_API_DISCOVERY
