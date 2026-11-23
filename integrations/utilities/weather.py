"""integrations/utilities/weather.py — Open-Meteo Weather Integration (Zero API Keys)."""
from __future__ import annotations

from typing import Any, Optional
from integrations.base import BaseIntegration, HealthReport, IntegrationStatus
from integrations.http_client import get_shared_client


class OpenMeteoWeather(BaseIntegration):
    """Fetches real-time weather and daily forecasts from Open-Meteo."""

    def __init__(self):
        super().__init__(name="Open-Meteo", category="utilities")
        self.http_client = get_shared_client()
        self.status = IntegrationStatus.CONNECTED

    async def check_health(self) -> HealthReport:
        try:
            res = await self.get_weather(28.6139, 77.2090)  # New Delhi test coordinates
            return HealthReport(healthy="temperature" in res, status=IntegrationStatus.CONNECTED)
        except Exception as e:
            return HealthReport(healthy=False, status=IntegrationStatus.ERROR, message=str(e))

    async def get_weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Queries current weather parameters."""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "hourly": "temperature_2m,relativehumidity_2m,weathercode",
        }
        resp = await self.http_client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            curr = data.get("current_weather", {})
            return {
                "temperature": curr.get("temperature"),
                "windspeed": curr.get("windspeed"),
                "winddirection": curr.get("winddirection"),
                "weathercode": curr.get("weathercode"),
                "time": curr.get("time"),
            }
        return {"error": f"HTTP {resp.status_code}"}

    async def geocode_city(self, city_name: str) -> Optional[dict[str, float]]:
        """Resolves city name to latitude and longitude."""
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
        resp = await self.http_client.get(url, params=params)
        if resp.status_code == 200:
            results = resp.json().get("results")
            if results:
                return {
                    "latitude": float(results[0]["latitude"]),
                    "longitude": float(results[0]["longitude"]),
                    "name": results[0]["name"],
                    "country": results[0].get("country", ""),
                }
        return None
