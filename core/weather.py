# core/weather.py
"""
Free, keyless weather lookups via Open-Meteo (geocoding + forecast).
No API key required, which keeps Nova's "no accounts needed" story intact.
"""

import logging
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Subset of Open-Meteo's weather codes, good enough for spoken summaries.
WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy with rime",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "rain showers", 81: "rain showers", 82: "violent rain showers",
    95: "thunderstorms", 96: "thunderstorms with hail", 99: "severe thunderstorms",
}


def get_weather(city: str, timeout: float = 6.0) -> str:
    """Return a short, voice-friendly weather summary for a city."""
    try:
        geo = requests.get(
            GEOCODE_URL, params={"name": city, "count": 1}, timeout=timeout
        ).json()
        results = geo.get("results")
        if not results:
            return f"I couldn't find a place called {city}."

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        resolved_name = place.get("name", city)

        forecast = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,relative_humidity_2m",
                "temperature_unit": "celsius",
            },
            timeout=timeout,
        ).json()

        current = forecast.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        code = current.get("weather_code")
        condition = WEATHER_CODES.get(code, "changeable conditions")

        if temp is None:
            return f"I couldn't get the current weather for {resolved_name}."

        summary = f"It's {temp} degrees and {condition} in {resolved_name}"
        if humidity is not None:
            summary += f", with {humidity} percent humidity"
        return summary + "."

    except requests.RequestException:
        logging.exception("Weather lookup failed.")
        return "Sorry, I couldn't reach the weather service right now."
    except Exception:
        logging.exception("Unexpected error while getting weather.")
        return "Sorry, something went wrong getting the weather."
