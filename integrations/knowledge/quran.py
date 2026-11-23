"""integrations/knowledge/quran.py — Quran Foundation & QuranEnc Authentic API."""
from __future__ import annotations

from typing import Any, Optional
from integrations.base import BaseIntegration, HealthReport, IntegrationStatus
from integrations.http_client import get_shared_client


class QuranKnowledgeIntegration(BaseIntegration):
    """Retrieves authentic Quranic verses, transliterations, and authorized translations."""

    def __init__(self):
        super().__init__(name="QuranFoundation", category="knowledge")
        self.http_client = get_shared_client()
        self.status = IntegrationStatus.CONNECTED

    async def get_verse(self, surah: int, ayah: int, translation_id: int = 131) -> dict[str, Any]:
        """Fetches Arabic text and authorized translation (131 = Clear Quran by Mustafa Khattab)."""
        url = f"https://api.quran.com/api/v4/verses/by_key/{surah}:{ayah}"
        params = {"language": "en", "words": "false", "translations": str(translation_id)}
        resp = await self.http_client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json().get("verse", {})
            translations = data.get("translations", [])
            translation_text = translations[0].get("text", "") if translations else ""
            return {
                "verse_key": data.get("verse_key"),
                "translation": translation_text,
                "juz_number": data.get("juz_number"),
                "hizb_number": data.get("hizb_number"),
            }
        return {"error": f"Verse {surah}:{ayah} not found"}

    async def get_chapter_info(self, surah: int) -> dict[str, Any]:
        """Fetches Surah metadata (name, revelation place, verses count)."""
        url = f"https://api.quran.com/api/v4/chapters/{surah}"
        resp = await self.http_client.get(url)
        if resp.status_code == 200:
            return resp.json().get("chapter", {})
        return {}
