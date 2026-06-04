import json
import urllib.error
import urllib.parse
import urllib.request

from google.genai import types
from loguru import logger

_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_REQUEST_TIMEOUT_SECONDS = 15


class ChatWeatherTools:
    def __init__(self):
        # self.headers = dict(request_headers)
        # self.user_id = user_id
        pass

    def declarations(self):
        return [
            types.FunctionDeclaration(
                name="get_weather",
                description="Get the current weather for a city.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "city": types.Schema(
                            type=types.Type.STRING,
                            description="City to get the weather for.",
                        ),
                    },
                    required=["city"],
                ),
            ),
        ]

    def dispatch(self):
        return {
            "get_weather": self._get_weather,
        }

    def _get_weather(self, city: str) -> dict:
        logger.info("TOOL CALLED: get_weather city={}", city)
        city = city.strip()
        if not city:
            return {"error": "City is required", "city": city}

        try:
            location = self._resolve_city(city=city)
            if not location:
                return {"error": "City not found", "city": city}
            weather = self._fetch_current_weather(
                latitude=location["latitude"],
                longitude=location["longitude"],
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError) as e:
            return {"error": "Weather lookup failed", "city": city, "details": str(e)}

        current = weather["current"]
        units = weather.get("current_units", {})
        return {
            "city": city,
            "resolved_city": location.get("name"),
            "country": location.get("country"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "timezone": weather.get("timezone"),
            "time": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "temperature_unit": units.get("temperature_2m"),
            "relative_humidity": current.get("relative_humidity_2m"),
            "relative_humidity_unit": units.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_speed_unit": units.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
        }

    def _resolve_city(self, city: str):
        data = self._get_json(
            _GEOCODING_URL,
            {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            },
        )
        results = data.get("results") or []
        return results[0] if results else None

    def _fetch_current_weather(self, latitude, longitude):
        return self._get_json(
            _FORECAST_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
        )

    @staticmethod
    def _get_json(url: str, params: dict) -> dict:
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{url}?{query}",
            headers={"User-Agent": "ai-project-weather-tool/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
