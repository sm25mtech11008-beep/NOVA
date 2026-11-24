# core/wakeword.py
"""
Forgiving wake-word matching.

Speech-to-text often mishears "hey Nova" as "Innova", "a Nova", "hey Nava"
and so on. Instead of requiring an exact phrase, we accept any of the
configured phrases *or* any word near the start of the sentence that sounds
close enough to "nova". Whatever the user said after the wake word is
returned so "hey nova what's the time" works in one breath.
"""

import difflib
import re

import config

# How close a word must be to "nova" (0..1). "innova" ~0.8, "nava" 0.75,
# "noah" 0.5 (rejected), "over" 0.25 (rejected).
_SIMILARITY = 0.75
# Only look at the first few words, so "I drive an Innova" mid-sentence
# during normal conversation doesn't count as a wake word.
_MAX_POSITION = 3
_FILLERS = {"hey", "hi", "hello", "ok", "okay", "a", "the", "yo", "wake", "up"}


def _words(text: str):
    return re.findall(r"[a-z']+", (text or "").lower())


def _sounds_like_name(word: str) -> bool:
    name = config.WAKE_NAME
    return word == name or difflib.SequenceMatcher(None, word, name).ratio() >= _SIMILARITY


def split_wake_word(text: str):
    """
    Return (woke, remainder).

    woke      -- True if the text contains the wake word.
    remainder -- the command spoken after the wake word ("" if none).
    """
    lowered = (text or "").lower().strip()
    if not lowered:
        return False, ""

    for phrase in sorted(config.WAKE_WORDS, key=len, reverse=True):
        idx = lowered.find(phrase)
        if idx != -1:
            return True, lowered[idx + len(phrase):].strip(" ,.!?")

    words = _words(lowered)
    for i, word in enumerate(words[:_MAX_POSITION]):
        if _sounds_like_name(word):
            return True, " ".join(words[i + 1:])
    return False, ""


def strip_wake_word(text: str) -> str:
    """Remove a leading wake word from a command ("hey nova, open chrome" -> "open chrome")."""
    words = _words(text)
    for i, word in enumerate(words[:_MAX_POSITION]):
        if word in _FILLERS:
            continue
        if _sounds_like_name(word):
            return " ".join(words[i + 1:])
        break
    return text
