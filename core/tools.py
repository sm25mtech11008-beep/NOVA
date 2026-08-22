# core/tools.py
import logging

import pywhatkit
import wikipedia


def playOnYouTube(query: str):
    """Play a YouTube video for the given search query."""
    try:
        pywhatkit.playonyt(query)
    except Exception:
        logging.exception("Failed to play video on YouTube.")


def searchWikipedia(query: str) -> str:
    """Search Wikipedia and return a short summary, or None on failure."""
    try:
        topic = query.replace("wikipedia", "").replace("wiki", "").strip()
        return wikipedia.summary(topic, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        option = e.options[0]
        return f"There are multiple results. The closest match is {option}."
    except Exception:
        logging.exception("Wikipedia search failed.")
        return None
