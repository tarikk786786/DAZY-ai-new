"""plugins/public_apis.py — Fast Public API Lookups (Weather, Wikipedia, Quran)."""
from __future__ import annotations

import asyncio

PLUGIN = {
    "name": "public_api_lookup",
    "description": (
        "Queries zero-cost public internet APIs: Open-Meteo weather forecasts, "
        "Wikipedia summaries, and authentic Quran verses without heavy local dependencies."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "service": {
                "type": "STRING",
                "enum": ["weather", "wikipedia", "quran"],
                "description": "Which public service to query",
            },
            "query": {
                "type": "STRING",
                "description": "City name for weather, topic title for Wikipedia, or 'Surah:Ayah' for Quran (e.g. '2:255')",
            },
        },
        "required": ["service", "query"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    service = str(parameters.get("service", "")).lower()
    query = str(parameters.get("query", "")).strip()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if service == "weather":
            from integrations.utilities.weather import OpenMeteoWeather
            w = OpenMeteoWeather()
            geo = loop.run_until_complete(w.geocode_city(query or "New Delhi"))
            if not geo:
                return f"City '{query}' nahi mili."
            data = loop.run_until_complete(w.get_weather(geo["latitude"], geo["longitude"]))
            if "temperature" in data:
                return f"{geo['name']}, {geo['country']} me current temperature {data['temperature']}°C hai aur wind speed {data['windspeed']} km/h hai."
            return "Weather fetch karne me error aaya."

        elif service == "wikipedia":
            from integrations.research.wikipedia import WikipediaIntegration
            wiki = WikipediaIntegration()
            res = loop.run_until_complete(wiki.get_summary(query))
            if "extract" in res and res["extract"]:
                return f"{res['title']}: {res['extract'][:280]}..."
            return f"Wikipedia par '{query}' ke bare me summary nahi mili."

        elif service == "quran":
            from integrations.knowledge.quran import QuranKnowledgeIntegration
            q = QuranKnowledgeIntegration()
            surah, ayah = 1, 1
            if ":" in query:
                parts = query.split(":")
                try:
                    surah, ayah = int(parts[0]), int(parts[1])
                except Exception:
                    pass
            res = loop.run_until_complete(q.get_verse(surah, ayah))
            if "translation" in res:
                return f"Surah {surah}:{ayah} — {res['translation']}"
            return "Verse information fetch nahi ho saki."

    except Exception as e:
        return f"Public API lookup failed: {e}"
    finally:
        loop.close()

    return "No result found."
