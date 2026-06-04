import json
import urllib.error

from webapp.tools.chat_weather_tools import ChatWeatherTools


class FakeWeatherResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_chat_weather_tool_returns_open_meteo_current_weather(monkeypatch):
    responses = [
        {
            "results": [
                {
                    "name": "Bilbao",
                    "country": "Spain",
                    "latitude": 43.2627,
                    "longitude": -2.9253,
                }
            ]
        },
        {
            "timezone": "Europe/Madrid",
            "current_units": {
                "temperature_2m": "°C",
                "relative_humidity_2m": "%",
                "wind_speed_10m": "km/h",
            },
            "current": {
                "time": "2026-06-03T18:45",
                "temperature_2m": 21.4,
                "relative_humidity_2m": 63,
                "wind_speed_10m": 9.2,
                "weather_code": 2,
            },
        },
    ]
    requested_urls = []

    def urlopen(req, timeout):
        requested_urls.append(req.full_url)
        return FakeWeatherResponse(responses.pop(0))

    monkeypatch.setattr("webapp.tools.chat_weather_tools.urllib.request.urlopen", urlopen)
    tools = ChatWeatherTools()

    assert tools.dispatch()["get_weather"](city="Oviedo") == {
        "city": "Oviedo",
        "resolved_city": "Bilbao",
        "country": "Spain",
        "latitude": 43.2627,
        "longitude": -2.9253,
        "timezone": "Europe/Madrid",
        "time": "2026-06-03T18:45",
        "temperature": 21.4,
        "temperature_unit": "°C",
        "relative_humidity": 63,
        "relative_humidity_unit": "%",
        "wind_speed": 9.2,
        "wind_speed_unit": "km/h",
        "weather_code": 2,
    }
    assert len(requested_urls) == 2
    assert requested_urls[0].startswith("https://geocoding-api.open-meteo.com/v1/search?")
    assert "name=Oviedo" in requested_urls[0]
    assert requested_urls[1].startswith("https://api.open-meteo.com/v1/forecast?")


def test_chat_weather_tool_returns_error_when_city_not_found(monkeypatch):
    requested_urls = []

    def urlopen(req, timeout):
        requested_urls.append(req.full_url)
        return FakeWeatherResponse({})

    monkeypatch.setattr("webapp.tools.chat_weather_tools.urllib.request.urlopen", urlopen)
    tools = ChatWeatherTools()

    assert tools.dispatch()["get_weather"](city="Unknown City") == {"error": "City not found", "city": "Unknown City"}
    assert len(requested_urls) == 1
    assert requested_urls[0].startswith("https://geocoding-api.open-meteo.com/v1/search?")


def test_chat_weather_tool_returns_error_when_city_is_blank():
    tools = ChatWeatherTools()

    assert tools.dispatch()["get_weather"](city="   ") == {"error": "City is required", "city": ""}


def test_chat_weather_tool_returns_error_when_api_fails(monkeypatch):
    def urlopen(req, timeout):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr("webapp.tools.chat_weather_tools.urllib.request.urlopen", urlopen)
    tools = ChatWeatherTools()

    response = tools.dispatch()["get_weather"](city="Bilbao")

    assert response["error"] == "Weather lookup failed"
    assert response["city"] == "Bilbao"
    assert "network down" in response["details"]
