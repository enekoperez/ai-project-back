import requests

from webapp.tools.chat_weather_tools import ChatWeatherTools


class FakeWeatherResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


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
    requests_seen = []

    def get(url, params, headers, timeout):
        requests_seen.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return FakeWeatherResponse(responses.pop(0))

    monkeypatch.setattr("webapp.tools.chat_weather_tools.requests.get", get)
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
    assert len(requests_seen) == 2
    assert requests_seen[0]["url"] == "https://geocoding-api.open-meteo.com/v1/search"
    assert requests_seen[0]["params"]["name"] == "Oviedo"
    assert requests_seen[1]["url"] == "https://api.open-meteo.com/v1/forecast"


def test_declarations_returns_get_weather_function_declaration():
    declaration = ChatWeatherTools().declarations()[0]

    assert declaration["name"] == "get_weather"
    assert declaration["description"] == "Get the current weather for a city."


def test_dispatch_returns_get_weather_handler():
    dispatch = ChatWeatherTools().dispatch()

    assert list(dispatch) == ["get_weather"]
    assert callable(dispatch["get_weather"])


def test_chat_weather_tool_returns_error_when_city_not_found(monkeypatch):
    requests_seen = []

    def get(url, params, headers, timeout):
        requests_seen.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return FakeWeatherResponse({})

    monkeypatch.setattr("webapp.tools.chat_weather_tools.requests.get", get)
    tools = ChatWeatherTools()

    assert tools.dispatch()["get_weather"](city="Unknown City") == {"error": "City not found", "city": "Unknown City"}
    assert len(requests_seen) == 1
    assert requests_seen[0]["url"] == "https://geocoding-api.open-meteo.com/v1/search"


def test_chat_weather_tool_returns_error_when_city_is_blank():
    tools = ChatWeatherTools()

    assert tools.dispatch()["get_weather"](city="   ") == {"error": "City is required", "city": ""}


def test_chat_weather_tool_returns_error_when_api_fails(monkeypatch):
    def get(url, params, headers, timeout):
        raise requests.RequestException("network down")

    monkeypatch.setattr("webapp.tools.chat_weather_tools.requests.get", get)
    tools = ChatWeatherTools()

    response = tools.dispatch()["get_weather"](city="Bilbao")

    assert response["error"] == "Weather lookup failed"
    assert response["city"] == "Bilbao"
    assert "network down" in response["details"]
