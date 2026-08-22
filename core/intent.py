# core/intent.py
"""
Fast, fully-offline intent detection for Nova.

Pure regex/keyword matching -- no model downloads, no network calls,
no first-call latency. Each rule also knows how to pull out the
entities (site name, search term, city, app name, ...) the matched
command needs.
"""

import re

# ─────────────────────────────────────────
# Canonical intent labels
# ─────────────────────────────────────────
INTENT_OPEN_WEBSITE = "open_website"
INTENT_SEARCH_WIKIPEDIA = "search_wikipedia"
INTENT_PLAY_MOOD_PLAYLIST = "play_mood_playlist"
INTENT_PLAY_YOUTUBE = "play_youtube"
INTENT_TELL_JOKE = "tell_joke"
INTENT_TELL_TIME = "tell_time"
INTENT_TELL_DATE = "tell_date"
INTENT_GET_WEATHER = "get_weather"
INTENT_OPEN_APP = "open_app"
INTENT_SYSTEM_CONTROL = "system_control"
INTENT_EXIT = "exit"
INTENT_GENERAL_CONVERSATION = "general_conversation"

KNOWN_SITES = [
    "wikipedia", "google", "facebook", "instagram", "twitter", "x",
    "stackoverflow", "linkedin", "whatsapp", "netflix", "amazon",
    "reddit", "youtube", "github",
]

KNOWN_APPS = ["vs code", "vscode", "code", "chrome", "notepad", "calculator", "explorer", "file explorer"]

MOOD_KEYWORDS = {
    "relaxing": ["relax", "calm", "chill", "sleep music", "meditation"],
    "fun_fact": ["fun fact", "interesting fact", "did you know"],
    "motivation": ["motivate", "motivation", "inspire", "pump me up"],
}

# Ordered rules: (regex, intent). First match wins.
KEYWORD_RULES = [
    (r"\b(exit|quit|goodbye|shut down)\b", INTENT_EXIT),
    (r"\b(weather|temperature|forecast)\b", INTENT_GET_WEATHER),
    (r"\bwhat('?s| is) the time\b|\btell me the time\b|\bcurrent time\b", INTENT_TELL_TIME),
    (r"\bwhat('?s| is) the date\b|\btell me the date\b|\btoday'?s date\b", INTENT_TELL_DATE),
    (r"\b(joke|make me laugh|something funny)\b", INTENT_TELL_JOKE),
    (r"\b(relax|calm|chill|meditation music)\b", INTENT_PLAY_MOOD_PLAYLIST),
    (r"\b(fun fact|interesting fact|did you know)\b", INTENT_PLAY_MOOD_PLAYLIST),
    (r"\b(motivate|motivation|inspire me|pump me up)\b", INTENT_PLAY_MOOD_PLAYLIST),
    (r"\b(lock( the)? (screen|pc|computer)|mute|volume up|volume down|increase volume|decrease volume)\b", INTENT_SYSTEM_CONTROL),
    (r"\bopen\b.*\b(" + "|".join(re.escape(a) for a in KNOWN_APPS) + r")\b", INTENT_OPEN_APP),
    (r"\b(play|put on)\b.*\b(youtube|music|song|video)\b", INTENT_PLAY_YOUTUBE),
    (r"\b(wikipedia|wiki)\b", INTENT_SEARCH_WIKIPEDIA),
    (r"\bopen\b.*\b(" + "|".join(re.escape(s) for s in KNOWN_SITES) + r")\b", INTENT_OPEN_WEBSITE),
]


def _extract_entities(intent: str, text: str) -> dict:
    """Pull the piece of the sentence each intent actually needs."""
    entities = {}

    if intent == INTENT_OPEN_WEBSITE:
        for site in KNOWN_SITES:
            if site in text:
                entities["site"] = site
                break

    elif intent == INTENT_OPEN_APP:
        for app in KNOWN_APPS:
            if app in text:
                entities["app"] = app
                break

    elif intent == INTENT_SEARCH_WIKIPEDIA:
        topic = re.sub(r"\b(search|wikipedia|wiki|tell me about|who is|what is)\b", "", text).strip()
        if topic:
            entities["topic"] = topic

    elif intent == INTENT_PLAY_YOUTUBE:
        query = re.sub(r"\b(play|put on|on)\b.*\b(youtube)\b", "", text)
        query = re.sub(r"\b(play|put on|youtube|music|song|video)\b", "", query).strip()
        if query:
            entities["query"] = query

    elif intent == INTENT_PLAY_MOOD_PLAYLIST:
        for mood, keywords in MOOD_KEYWORDS.items():
            if any(k in text for k in keywords):
                entities["mood"] = mood
                break

    elif intent == INTENT_GET_WEATHER:
        match = re.search(r"\b(?:in|for|at)\s+([a-zA-Z\s]+)$", text)
        if match:
            entities["city"] = match.group(1).strip()

    elif intent == INTENT_SYSTEM_CONTROL:
        if "lock" in text:
            entities["action"] = "lock"
        elif "mute" in text:
            entities["action"] = "mute"
        elif "up" in text or "increase" in text:
            entities["action"] = "volume_up"
        elif "down" in text or "decrease" in text:
            entities["action"] = "volume_down"

    return entities


def detect_intent(user_input: str) -> dict:
    """
    Detect the intent of a user's voice command using fast keyword rules.

    Returns:
        dict with keys:
            - 'intent': str (matched intent label)
            - 'confidence': float (0.0 to 1.0)
            - 'method': str (always 'keyword' -- kept for API compatibility)
            - 'entities': dict (extracted slot values)
    """
    text = (user_input or "").lower().strip()

    for pattern, intent in KEYWORD_RULES:
        if re.search(pattern, text):
            return {
                "intent": intent,
                "confidence": 1.0,
                "method": "keyword",
                "entities": _extract_entities(intent, text),
            }

    return {
        "intent": INTENT_GENERAL_CONVERSATION,
        "confidence": 0.5,
        "method": "fallback",
        "entities": {},
    }


if __name__ == "__main__":
    test_inputs = [
        "Hey Nova, play some relaxing music on YouTube",
        "What's the weather like in Mumbai?",
        "Tell me about Albert Einstein on wikipedia",
        "Open VS Code please",
        "Lock the screen",
        "I'm feeling a bit sad today",
    ]
    for inp in test_inputs:
        result = detect_intent(inp)
        print(f"\nInput : {inp}")
        print(f"Intent: {result['intent']} ({result['confidence']*100:.1f}% via {result['method']})")
        if result["entities"]:
            print(f"Entities: {result['entities']}")
