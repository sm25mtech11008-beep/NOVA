# core/intent.py
"""
Fast, fully-offline intent detection for Nova.

Pure regex/keyword matching -- no model downloads, no network calls,
no first-call latency. Each rule also knows how to pull out the
entities (site name, search term, city, app name, ...) the matched
command needs. Anything that doesn't match a rule goes to the
conversation model.
"""

import re

# ─────────────────────────────────────────
# Canonical intent labels
# ─────────────────────────────────────────
INTENT_OPEN_WEBSITE = "open_website"
INTENT_SEARCH_WIKIPEDIA = "search_wikipedia"
INTENT_SEARCH_WEB = "search_web"
INTENT_PLAY_MOOD_PLAYLIST = "play_mood_playlist"
INTENT_PLAY_YOUTUBE = "play_youtube"
INTENT_TELL_JOKE = "tell_joke"
INTENT_TELL_TIME = "tell_time"
INTENT_TELL_DATE = "tell_date"
INTENT_GET_WEATHER = "get_weather"
INTENT_OPEN_APP = "open_app"
INTENT_SYSTEM_CONTROL = "system_control"
INTENT_REMEMBER_FACT = "remember_fact"
INTENT_RECALL_FACT = "recall_fact"
INTENT_FORGET_FACT = "forget_fact"
INTENT_HELP = "help"
INTENT_SMALL_TALK = "small_talk"
INTENT_EXIT = "exit"
INTENT_GENERAL_CONVERSATION = "general_conversation"

KNOWN_SITES = [
    "wikipedia", "google", "facebook", "instagram", "twitter", "x",
    "stackoverflow", "stack overflow", "linkedin", "whatsapp", "netflix",
    "amazon", "reddit", "youtube", "github", "gmail", "chatgpt", "spotify",
]

KNOWN_APPS = [
    "vs code", "vscode", "visual studio code", "code", "chrome", "notepad",
    "calculator", "file explorer", "explorer", "settings", "task manager",
    "command prompt", "terminal", "paint",
]

MOOD_KEYWORDS = {
    "relaxing": r"relax\w*|calm\w*|chill\w*|sleep music|meditat\w*|soothing|peaceful",
    "fun_fact": r"fun facts?|interesting facts?",
    "motivation": r"motivat\w*|inspir\w*|pump me up|energ\w*",
}

# Words people wrap around commands that carry no meaning for us.
_POLITE = r"(?:(?:hey |ok |okay )?nova[, ]*|can you |could you |would you |will you |please |just |now |and |so |also )*"

_FACT_KEY_STOP = r"(?:\s+(?:is|was|are|can|could|please|nova|again|do|did|you|tell|and|right)\b.*)?$"

FACT_ALIASES = {
    "bday": "birthday", "b day": "birthday", "date of birth": "birthday", "dob": "birthday",
    "birth date": "birthday", "birthdate": "birthday", "full name": "name",
}


def normalize_fact_key(key: str) -> str:
    key = re.sub(r"[^a-z0-9 ]", "", (key or "").lower()).strip()
    key = key.replace("favourite", "favorite")
    return FACT_ALIASES.get(key, key)


def _has_mood(text: str):
    for mood, pattern in MOOD_KEYWORDS.items():
        if re.search(r"\b(?:" + pattern + r")\b", text):
            return mood
    return None


def _is_mood_request(text: str) -> bool:
    if not _has_mood(text):
        return False
    # Require some sign the user wants something *played*, so "I'm feeling
    # calm today" goes to conversation instead of opening YouTube.
    return bool(re.search(
        r"\b(play|put on|music|songs?|video|something|some|motivate me|inspire me|pump me up|"
        r"help me (?:relax|calm down)|i (?:want|need) to relax|tell me a fun fact|fun fact)\b",
        text,
    ))


_RECALL_PATTERNS = [
    r"\bwhat (?:do|did) you (?:know|remember) about me\b",
    # "when is my birthday", "what's my name", "so what was my favourite colour"
    r"^" + _POLITE + r"(?:but |ok |okay )?(?:what|when|where|who|which)(?:'s|s| is| are| was| were)? my\b",
    # "do you know my name", "tell me my birthday", "remind me what my wifi password is"
    r"\b(?:do you (?:know|remember)|tell me|remind me)(?: what| when)?(?: is| was)? my\b",
]


def _is_recall(text: str) -> bool:
    return any(re.search(p, text) for p in _RECALL_PATTERNS)


# Ordered rules: (matcher, intent). First match wins. A matcher is a regex
# string or a function taking the lowercased text.
KEYWORD_RULES = [
    (r"^" + _POLITE + r"(exit|quit|goodbye|good bye|bye|shut ?down nova|turn off)( nova)?$", INTENT_EXIT),
    (r"\b(what can you do|what do you do|help me use you|list (?:your )?commands)\b|^" + _POLITE + r"help$", INTENT_HELP),
    (r"^" + _POLITE + r"(hi|hello|hey|thanks|thank you|thank you so much|thanks a lot|good morning|good afternoon|good evening|good night|you're welcome)( nova)?$", INTENT_SMALL_TALK),

    # Personal memory: "my birthday is 5th march", "remember that I parked on level 2",
    # "when is my birthday", "what do you know about me", "forget my birthday".
    (r"\bforget (?:about )?my\b", INTENT_FORGET_FACT),
    (lambda t: _is_recall(t), INTENT_RECALL_FACT),
    (r"^" + _POLITE + r"(remember|note down|note that|make a note|don't forget)\b", INTENT_REMEMBER_FACT),
    (r"\bmy name is\b|\bcall me\b|\bi was born on\b|\bmy (birthday|bday|date of birth|favou?rite [a-z ]+?) is\b", INTENT_REMEMBER_FACT),

    (r"\b(weather|temperature|forecast|is it (?:going to )?rain\w*)\b", INTENT_GET_WEATHER),
    (r"\bwhat('?s| is)? the time\b|\bwhat time is it\b|\btell me the time\b|\b(current|the) time\b|\btime now\b|\btime is it\b", INTENT_TELL_TIME),
    (r"\bwhat('?s| is)? (the |today'?s )?date\b|\btell me the date\b|\btoday'?s date\b|\bwhat day is (it|today)\b|\bwhich day is (it|today)\b|\bdate today\b", INTENT_TELL_DATE),
    (r"\b(joke|make me laugh|something funny)\b", INTENT_TELL_JOKE),
    (lambda t: _is_mood_request(t), INTENT_PLAY_MOOD_PLAYLIST),
    (r"\b(lock (the |my )?(screen|pc|computer|laptop|system)|un ?mute|mute|volume|louder|quieter|softer)\b", INTENT_SYSTEM_CONTROL),
    (r"\b(open|launch|start|run)\b.*\b(" + "|".join(re.escape(a) for a in KNOWN_APPS) + r")\b", INTENT_OPEN_APP),
    (r"\b(open|go to|launch)\b.*\b(" + "|".join(re.escape(s) for s in KNOWN_SITES) + r")\b", INTENT_OPEN_WEBSITE),
    (r"^" + _POLITE + r"(play|put on)\b|\b(play|put on)\b.*\b(youtube|music|songs?|video)\b", INTENT_PLAY_YOUTUBE),
    (r"\b(wikipedia|wiki)\b|^" + _POLITE + r"(who is|who was|who were|tell me about)\b(?!.*\b(you|your|yourself|me|my)\b)", INTENT_SEARCH_WIKIPEDIA),
    (r"\b(google|search|look up|lookup)\b", INTENT_SEARCH_WEB),
]


def _strip_polite(text: str) -> str:
    return re.sub(r"^" + _POLITE, "", text).strip()


def _extract_fact_key(text: str) -> str:
    match = re.search(r"\bmy ([a-z' ]+)", text)
    if not match:
        return ""
    key = re.sub(_FACT_KEY_STOP, "", match.group(1)).strip()
    return normalize_fact_key(key)


def _extract_remember(text: str) -> dict:
    text = re.sub(r"^" + _POLITE + r"(?:remember|note down|note that|make a note(?: that)?|don't forget)(?: that)?\s*", "", text)
    text = text.strip(" .!?")

    m = re.search(r"\b(?:my name is|call me)\s+(.+)$", text)
    if m:
        return {"key": "name", "value": m.group(1).strip()}
    m = re.search(r"\bi was born on\s+(.+)$", text)
    if m:
        return {"key": "birthday", "value": m.group(1).strip()}
    m = re.search(r"\bmy ([a-z' ]+?) (?:is|are|was) (?:on )?(.+)$", text)
    if m:
        return {"key": normalize_fact_key(m.group(1)), "value": m.group(2).strip()}
    return {"note": text} if text else {}


def _extract_entities(intent: str, text: str) -> dict:
    """Pull the piece of the sentence each intent actually needs."""
    entities = {}

    if intent == INTENT_OPEN_WEBSITE:
        for site in sorted(KNOWN_SITES, key=len, reverse=True):
            if re.search(r"\b" + re.escape(site) + r"\b", text):
                entities["site"] = site
                break

    elif intent == INTENT_OPEN_APP:
        for app in sorted(KNOWN_APPS, key=len, reverse=True):
            if re.search(r"\b" + re.escape(app) + r"\b", text):
                entities["app"] = app
                break

    elif intent == INTENT_SEARCH_WIKIPEDIA:
        topic = re.sub(r"\b(search|on|in|from|wikipedia|wiki|tell me about|who is|who was|who were|what is|for)\b", " ", _strip_polite(text))
        topic = re.sub(r"\s+", " ", topic).strip(" ?.!")
        if topic:
            entities["topic"] = topic

    elif intent == INTENT_SEARCH_WEB:
        query = _strip_polite(text)
        query = re.sub(r"\b(on|in|using|with) (google|the web|the internet|internet)\b", " ", query)
        query = re.sub(r"\b(search|google|look up|lookup)( for| about)?\b", " ", query)
        query = re.sub(r"\s+", " ", query).strip(" ?.!")
        if query:
            entities["query"] = query

    elif intent == INTENT_PLAY_YOUTUBE:
        query = _strip_polite(text)
        query = re.sub(r"\b(on|in|from|using) youtube\b|\byoutube\b", " ", query)
        query = re.sub(r"^(play|put on)\s+(me\s+)?(a |an |some |the )?", "", query.strip())
        query = re.sub(r"\s+(for me|please|now|nova)$", "", query.strip())
        query = re.sub(r"\s+", " ", query).strip(" ?.!")
        if query and query not in {"something", "anything", "music", "a song", "song", "songs",
                                   "some music", "video", "a video", "something good", "something nice"}:
            entities["query"] = query

    elif intent == INTENT_PLAY_MOOD_PLAYLIST:
        entities["mood"] = _has_mood(text) or "relaxing"

    elif intent == INTENT_GET_WEATHER:
        match = re.search(r"\b(?:in|for|at)\s+([a-z\s]+?)(?:\s+(?:today|tomorrow|now|right now|please|nova))*\s*\??$", text)
        if match:
            entities["city"] = match.group(1).strip()

    elif intent == INTENT_SYSTEM_CONTROL:
        if "lock" in text:
            entities["action"] = "lock"
        elif "mute" in text:
            entities["action"] = "mute"
        elif re.search(r"\b(up|increase|raise|louder|higher)\b", text):
            entities["action"] = "volume_up"
        elif re.search(r"\b(down|decrease|lower|reduce|quieter|softer)\b", text):
            entities["action"] = "volume_down"

    elif intent == INTENT_REMEMBER_FACT:
        entities.update(_extract_remember(text))

    elif intent in (INTENT_RECALL_FACT, INTENT_FORGET_FACT):
        if re.search(r"\babout me\b", text):
            entities["key"] = "*"
        else:
            key = _extract_fact_key(text)
            if key:
                entities["key"] = key

    return entities


def extract_entities(intent: str, text: str) -> dict:
    """Public wrapper, used when Nova fills in a follow-up answer."""
    return _extract_entities(intent, (text or "").lower().strip())


def detect_intent(user_input: str) -> dict:
    """
    Detect the intent of a user's voice command using fast keyword rules.

    Returns:
        dict with keys:
            - 'intent': str (matched intent label)
            - 'confidence': float (0.0 to 1.0)
            - 'method': str ('keyword' or 'fallback')
            - 'entities': dict (extracted slot values)
    """
    text = (user_input or "").lower().strip().rstrip("?.!")

    for matcher, intent in KEYWORD_RULES:
        matched = matcher(text) if callable(matcher) else re.search(matcher, text)
        if matched:
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
        "play me something on YouTube",
        "play something motivational",
        "when is my birthday can you tell",
        "my birthday is 5th march",
        "what time is it",
        "Open VS Code please",
        "I'm feeling a bit sad today",
    ]
    for inp in test_inputs:
        result = detect_intent(inp)
        print(f"{inp!r:45} -> {result['intent']} {result['entities'] or ''}")
