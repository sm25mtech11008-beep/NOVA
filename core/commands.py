# core/commands.py
"""
Command handlers for Nova. Each handler takes the raw query and extracted
entities, performs any side effect (opening a browser, launching an app,
...), and returns the sentence Nova should speak back -- or None if it
can't handle the request, so the caller can fall back to conversation.

A handler that needs more information returns an `Ask` (a str subclass).
Nova speaks it and treats the user's next sentence as the answer.
"""

import random
import re
import webbrowser
from datetime import date, datetime
from urllib.parse import quote_plus
import logging

from core import apps, tools, weather
from core.context_memory import memory
from core.intent import (
    INTENT_EXIT,
    INTENT_FORGET_FACT,
    INTENT_GET_WEATHER,
    INTENT_HELP,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_PLAY_MOOD_PLAYLIST,
    INTENT_PLAY_YOUTUBE,
    INTENT_RECALL_FACT,
    INTENT_REMEMBER_FACT,
    INTENT_SEARCH_WEB,
    INTENT_SEARCH_WIKIPEDIA,
    INTENT_SMALL_TALK,
    INTENT_SYSTEM_CONTROL,
    INTENT_TELL_DATE,
    INTENT_TELL_JOKE,
    INTENT_TELL_TIME,
)
import config


class Ask(str):
    """A reply that is a question; Nova's next input answers it."""


SITE_URLS = {
    "wikipedia": "https://www.wikipedia.org",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp": "https://web.whatsapp.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
    "reddit": "https://www.reddit.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
    "spotify": "https://open.spotify.com",
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
    "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "I'm reading a book about anti-gravity. It's impossible to put down.",
    "Why was the math book sad? It had too many problems.",
]

HELP_TEXT = (
    "Here's what I can do. Play music, like 'play lofi music' or 'play something relaxing'. "
    "Tell you the time, date or weather. Open apps and websites, like 'open chrome' or 'open youtube'. "
    "Search Google or Wikipedia. Tell jokes. Change the volume or lock the screen. "
    "Remember things, like 'my birthday is 5th March'. "
    "And you can just chat with me about anything. Say 'go to sleep' when you're done."
)

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _name_suffix() -> str:
    """", Shashi" if Nova knows the user's name, otherwise ""."""
    name = memory.get_fact("name")
    return f", {name.title()}" if name else ""


# ─────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────
def _handle_open_website(query: str, entities: dict):
    site = entities.get("site")
    url = SITE_URLS.get(site)
    if not url:
        return None
    webbrowser.open(url)
    return f"Opening {site}."


def _handle_search_wikipedia(query: str, entities: dict):
    topic = entities.get("topic")
    if not topic:
        return Ask("What should I look up on Wikipedia?")
    # None -> falls back to the conversation model, which may still know the answer.
    return tools.searchWikipedia(topic)


def _handle_search_web(query: str, entities: dict):
    term = entities.get("query")
    if not term:
        return Ask("What should I search for?")
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(term)}")
    return f"Here are the Google results for {term}."


def _handle_play_youtube(query: str, entities: dict):
    search_term = entities.get("query")
    if not search_term:
        return Ask("What would you like me to play?")
    tools.playOnYouTube(search_term)
    return f"Playing {search_term} on YouTube."


def _handle_play_mood_playlist(query: str, entities: dict):
    mood = entities.get("mood", "relaxing")
    choice = random.choice(MOOD_PLAYLISTS.get(mood, MOOD_PLAYLISTS["relaxing"]))
    tools.playOnYouTube(choice)
    return MOOD_INTROS.get(mood, "Playing something for you.")


def _handle_tell_time(query: str, entities: dict):
    return f"It's {datetime.now().strftime('%I:%M %p').lstrip('0')}."


def _handle_tell_date(query: str, entities: dict):
    now = datetime.now()
    return f"Today is {now.strftime('%A')}, {now.strftime('%B')} {now.day}, {now.year}."


def _handle_get_weather(query: str, entities: dict):
    city = entities.get("city") or config.DEFAULT_CITY
    return weather.get_weather(city)


def _handle_open_app(query: str, entities: dict):
    app_name = entities.get("app")
    if not app_name:
        return Ask("Which app should I open?")
    if apps.open_app(app_name):
        return f"Opening {app_name}."
    return f"I couldn't open {app_name}."


def _handle_system_control(query: str, entities: dict):
    action = entities.get("action")
    if action == "lock":
        return "Locking the screen." if apps.lock_screen() else "I couldn't lock the screen."
    if action == "mute":
        return "Done." if apps.mute() else "I couldn't change the volume."
    if action == "volume_up":
        return "Turning it up." if apps.volume_up() else "I couldn't change the volume."
    if action == "volume_down":
        return "Turning it down." if apps.volume_down() else "I couldn't change the volume."
    return "Should I turn the volume up, down, or mute it?"


# ── Personal memory ───────────────────────

def parse_day_month(text: str):
    """Find a (day, month) in text like '5th march', 'march 5', '05 mar 1999'."""
    text = (text or "").lower()
    month_pat = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?(?: of)?\s+" + month_pat, text)
    if m:
        day, month = int(m.group(1)), MONTHS[m.group(2)]
    else:
        m = re.search(r"\b" + month_pat + r"\s+(\d{1,2})(?:st|nd|rd|th)?\b", text)
        if not m:
            return None
        day, month = int(m.group(2)), MONTHS[m.group(1)]
    try:
        date(2000, month, day)  # validate (2000 is a leap year, so 29 Feb is allowed)
    except ValueError:
        return None
    return day, month


def _days_until(day: int, month: int, today: date = None) -> int:
    today = today or date.today()
    for year in (today.year, today.year + 1, today.year + 2):
        try:
            target = date(year, month, day)
        except ValueError:  # 29 Feb in a non-leap year
            continue
        if target >= today:
            return (target - today).days
    return -1


def describe_birthday(value: str, today: date = None) -> str:
    parsed = parse_day_month(value)
    if not parsed:
        return f"Your birthday is {value}."
    day, month = parsed
    pretty = date(2000, month, day).strftime("%B ") + str(day)
    days = _days_until(day, month, today)
    if days == 0:
        return f"It's today! Happy birthday{_name_suffix()}!"
    if days == 1:
        return f"Your birthday is tomorrow, {pretty}!"
    return f"Your birthday is on {pretty}. That's {days} days from now."


def _handle_remember_fact(query: str, entities: dict):
    key, value, note = entities.get("key"), entities.get("value"), entities.get("note")
    if key and value:
        memory.set_fact(key, value)
        if key == "name":
            return f"Nice to meet you, {value.title()}. I'll remember that."
        if key == "birthday":
            return "Got it, I'll remember that. " + describe_birthday(value)
        return f"Got it. Your {key} is {value}."
    if note:
        memory.add_note(note)
        return "Okay, I'll remember that."
    return Ask("What should I remember?")


def _handle_recall_fact(query: str, entities: dict):
    key = entities.get("key")
    facts = memory.get_facts()
    notes = memory.get_notes()

    if key == "*" or not key:
        if not facts and not notes:
            return "I don't know much about you yet. Tell me things like 'my name is ...' or 'my birthday is ...'."
        parts = [f"your {k} is {v}" for k, v in facts.items()]
        parts += [f"you told me {n}" for n in notes[-3:]]
        return "Here's what I know: " + ", ".join(parts) + "."

    value = facts.get(key)
    if value is None:
        # Try a looser match: "favorite color" vs "favorite colour".
        for k, v in facts.items():
            if key in k or k in key:
                key, value = k, v
                break
    if value is None:
        return f"I don't know your {key} yet. You can tell me by saying 'my {key} is ...'."
    if key == "birthday":
        return describe_birthday(value)
    if key == "name":
        return f"Your name is {value.title()}."
    return f"Your {key} is {value}."


def _handle_forget_fact(query: str, entities: dict):
    key = entities.get("key")
    if not key:
        return Ask("What should I forget?")
    if memory.delete_fact(key):
        return f"Okay, I've forgotten your {key}."
    return f"I didn't have your {key} saved anyway."


def _handle_small_talk(query: str, entities: dict):
    text = query.lower()
    if "thank" in text:
        return random.choice(["You're welcome!", "Anytime.", "Happy to help."])
    if "night" in text:
        return f"Good night{_name_suffix()}. Sleep well."
    if "welcome" in text:
        return "Ha, thanks."
    return random.choice([f"Hey{_name_suffix()}! What can I do for you?", "Hi! What do you need?"])


HANDLERS = {
    INTENT_OPEN_WEBSITE: _handle_open_website,
    INTENT_SEARCH_WIKIPEDIA: _handle_search_wikipedia,
    INTENT_SEARCH_WEB: _handle_search_web,
    INTENT_PLAY_YOUTUBE: _handle_play_youtube,
    INTENT_PLAY_MOOD_PLAYLIST: _handle_play_mood_playlist,
    INTENT_TELL_JOKE: lambda q, e: random.choice(JOKES),
    INTENT_TELL_TIME: _handle_tell_time,
    INTENT_TELL_DATE: _handle_tell_date,
    INTENT_GET_WEATHER: _handle_get_weather,
    INTENT_OPEN_APP: _handle_open_app,
    INTENT_SYSTEM_CONTROL: _handle_system_control,
    INTENT_REMEMBER_FACT: _handle_remember_fact,
    INTENT_RECALL_FACT: _handle_recall_fact,
    INTENT_FORGET_FACT: _handle_forget_fact,
    INTENT_HELP: lambda q, e: HELP_TEXT,
    INTENT_SMALL_TALK: _handle_small_talk,
    INTENT_EXIT: lambda q, e: f"Goodbye{_name_suffix()}!",
}


def handle_command(intent: str, query: str, entities: dict):
    """
    Execute the handler for a detected intent.

    Returns:
        str / Ask: the response Nova should speak, or None if the intent has
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
