# core/commands.py
"""
Command handlers for Nova. Each handler takes the detected intent, the
raw query, and extracted entities, performs any side effect (opening a
browser, launching an app, ...), and returns the sentence Nova should
speak back -- or None if it can't handle the intent, so the caller can
fall back to conversation.
"""

import random
import webbrowser
from datetime import datetime
import logging

from core import apps, tools, weather
from core.intent import (
    INTENT_EXIT,
    INTENT_GET_WEATHER,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_PLAY_MOOD_PLAYLIST,
    INTENT_PLAY_YOUTUBE,
    INTENT_SEARCH_WIKIPEDIA,
    INTENT_SYSTEM_CONTROL,
    INTENT_TELL_DATE,
    INTENT_TELL_JOKE,
    INTENT_TELL_TIME,
)
import config

SITE_URLS = {
    "wikipedia": "https://www.wikipedia.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "stackoverflow": "https://stackoverflow.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp": "https://www.whatsapp.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "reddit": "https://www.reddit.com",
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
}

MOOD_PLAYLISTS = {
    "relaxing": [
        "lofi chill beats", "relaxing rain sounds", "ambient ocean waves",
        "soft piano music", "nature sounds with birds",
    ],
    "fun_fact": [
        "amazing facts you didn't know", "mind blowing science facts",
        "facts about the universe", "unbelievable history facts",
    ],
    "motivation": [
        "motivational speech", "powerful gym motivation",
        "morning motivation", "never give up speech",
    ],
}

MOOD_INTROS = {
    "relaxing": "Playing something relaxing for you.",
    "fun_fact": "Here's something interesting!",
    "motivation": "Get ready to feel pumped!",
}

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break, and it said no problem, it'll go to sleep too.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I would tell you a UDP joke, but you might not get it.",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
]


def _handle_open_website(entities: dict) -> str:
    site = entities.get("site")
    url = SITE_URLS.get(site)
    if not url:
        return None
    webbrowser.open(url)
    return f"Opening {site}, sir."


def _handle_search_wikipedia(query: str, entities: dict) -> str:
    topic = entities.get("topic") or query
    result = tools.searchWikipedia(topic)
    return result or "Sorry, I couldn't find anything on Wikipedia."


def _handle_play_youtube(entities: dict) -> str:
    search_term = entities.get("query")
    if not search_term:
        return "What would you like me to play?"
    tools.playOnYouTube(search_term)
    return f"Playing {search_term} on YouTube."


def _handle_play_mood_playlist(entities: dict) -> str:
    mood = entities.get("mood", "relaxing")
    choice = random.choice(MOOD_PLAYLISTS.get(mood, MOOD_PLAYLISTS["relaxing"]))
    tools.playOnYouTube(choice)
    return MOOD_INTROS.get(mood, "Playing something for you.")


def _handle_tell_joke() -> str:
    return random.choice(JOKES)


def _handle_tell_time() -> str:
    return f"Sir, the time is {datetime.now().strftime('%H:%M:%S')}"


def _handle_tell_date() -> str:
    return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"


def _handle_get_weather(entities: dict) -> str:
    city = entities.get("city") or config.DEFAULT_CITY
    return weather.get_weather(city)


def _handle_open_app(entities: dict) -> str:
    app_name = entities.get("app")
    if not app_name:
        return "Which application should I open?"
    if apps.open_app(app_name):
        return f"Opening {app_name}, sir."
    return f"I couldn't open {app_name}."


def _handle_system_control(entities: dict) -> str:
    action = entities.get("action")
    if action == "lock":
        return "Locking the screen." if apps.lock_screen() else "I couldn't lock the screen."
    if action == "mute":
        return "Muted." if apps.mute() else "I couldn't change the volume."
    if action == "volume_up":
        return "Turning it up." if apps.volume_up() else "I couldn't change the volume."
    if action == "volume_down":
        return "Turning it down." if apps.volume_down() else "I couldn't change the volume."
    return "I didn't catch what to do."


HANDLERS = {
    INTENT_OPEN_WEBSITE: lambda q, e: _handle_open_website(e),
    INTENT_SEARCH_WIKIPEDIA: lambda q, e: _handle_search_wikipedia(q, e),
    INTENT_PLAY_YOUTUBE: lambda q, e: _handle_play_youtube(e),
    INTENT_PLAY_MOOD_PLAYLIST: lambda q, e: _handle_play_mood_playlist(e),
    INTENT_TELL_JOKE: lambda q, e: _handle_tell_joke(),
    INTENT_TELL_TIME: lambda q, e: _handle_tell_time(),
    INTENT_TELL_DATE: lambda q, e: _handle_tell_date(),
    INTENT_GET_WEATHER: lambda q, e: _handle_get_weather(e),
    INTENT_OPEN_APP: lambda q, e: _handle_open_app(e),
    INTENT_SYSTEM_CONTROL: lambda q, e: _handle_system_control(e),
    INTENT_EXIT: lambda q, e: "Goodbye, sir!",
}


def handle_command(intent: str, query: str, entities: dict) -> str:
    """
    Execute the handler for a detected intent.

    Returns:
        str: the response Nova should speak, or None if the intent has
        no matching handler (caller should fall back to conversation).
    """
    handler = HANDLERS.get(intent)
    if not handler:
        return None
    try:
        return handler(query, entities or {})
    except Exception:
        logging.exception(f"Error while handling intent '{intent}':")
        return "Sorry, something went wrong with that."
