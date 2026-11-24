# tests/test_intent.py
"""
Offline tests for intent detection and wake-word matching.
Run with:  python -m pytest tests     (or simply: python tests/test_intent.py)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent import detect_intent  # noqa: E402
from core.wakeword import split_wake_word, strip_wake_word  # noqa: E402

# (utterance, expected intent, expected entities subset)
CASES = [
    # From real session logs
    ("play me something on YouTube", "play_youtube", {}),
    ("play something motivational", "play_mood_playlist", {"mood": "motivation"}),
    ("so what is the date today", "tell_date", {}),
    ("and when is my birthday can you tell", "recall_fact", {"key": "birthday"}),
    ("play snehithane on youtube", "play_youtube", {"query": "snehithane"}),
    ("play snehithane snehithane", "play_youtube", {"query": "snehithane snehithane"}),
    # Time / date
    ("what time is it", "tell_time", {}),
    ("what's the time", "tell_time", {}),
    ("what day is it today", "tell_date", {}),
    # Personal memory
    ("my birthday is 5th march", "remember_fact", {"key": "birthday", "value": "5th march"}),
    ("my name is shashi", "remember_fact", {"key": "name", "value": "shashi"}),
    ("call me boss", "remember_fact", {"key": "name", "value": "boss"}),
    ("remember that my favourite colour is blue", "remember_fact", {"key": "favorite colour", "value": "blue"}),
    ("remember I parked on level 2", "remember_fact", {"note": "i parked on level 2"}),
    ("what's my name", "recall_fact", {"key": "name"}),
    ("do you remember my birthday", "recall_fact", {"key": "birthday"}),
    ("what do you know about me", "recall_fact", {"key": "*"}),
    ("forget my birthday", "forget_fact", {"key": "birthday"}),
    # Media
    ("play arijit singh songs", "play_youtube", {"query": "arijit singh songs"}),
    ("can you play lofi on youtube", "play_youtube", {"query": "lofi"}),
    ("play some relaxing music", "play_mood_playlist", {"mood": "relaxing"}),
    ("motivate me", "play_mood_playlist", {"mood": "motivation"}),
    # Other commands
    ("what's the weather in mumbai today", "get_weather", {"city": "mumbai"}),
    ("open vs code please", "open_app", {"app": "vs code"}),
    ("open youtube", "open_website", {"site": "youtube"}),
    ("search for python tutorials on google", "search_web", {"query": "python tutorials"}),
    ("who is albert einstein", "search_wikipedia", {"topic": "albert einstein"}),
    ("turn up the volume", "system_control", {"action": "volume_up"}),
    ("lock the screen", "system_control", {"action": "lock"}),
    ("tell me a joke", "tell_joke", {}),
    ("what can you do", "help", {}),
    ("thank you", "small_talk", {}),
    ("goodbye", "exit", {}),
    # Should go to the conversation model
    ("i'm feeling a bit sad today", "general_conversation", {}),
    ("how do i fix my laptop", "general_conversation", {}),
    ("tell me about yourself", "general_conversation", {}),
    ("i'm feeling calm today", "general_conversation", {}),
]


def test_intents():
    failures = []
    for text, intent, entities in CASES:
        result = detect_intent(text)
        got_entities = result["entities"]
        if result["intent"] != intent or any(got_entities.get(k) != v for k, v in entities.items()):
            failures.append(f"{text!r}: expected {intent} {entities}, got {result['intent']} {got_entities}")
    assert not failures, "\n" + "\n".join(failures)


def test_wake_word():
    assert split_wake_word("hey nova") == (True, "")
    assert split_wake_word("Innova") == (True, "")          # common mishearing
    assert split_wake_word("hey nova what's the time") == (True, "what's the time")
    assert split_wake_word("a nava open chrome")[0]
    assert not split_wake_word("i went over there")[0]
    assert not split_wake_word("what is the time")[0]
    assert strip_wake_word("hey nova open chrome") == "open chrome"
    assert strip_wake_word("open chrome") == "open chrome"


if __name__ == "__main__":
    test_intents()
    test_wake_word()
    print("All intent and wake-word tests passed.")
