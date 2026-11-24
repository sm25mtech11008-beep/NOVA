# core/tools.py
import logging
import re
import webbrowser
from urllib.parse import quote_plus


def playOnYouTube(query: str):
    """Play the top YouTube result for the query (falls back to the search page)."""
    try:
        # Imported lazily: pywhatkit is slow to import and checks the internet on import.
        import pywhatkit
        pywhatkit.playonyt(query)
    except Exception:
        logging.warning("pywhatkit failed; opening YouTube search instead.", exc_info=True)
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")


def searchWikipedia(query: str):
    """Search Wikipedia and return a short spoken summary, or None on failure."""
    summary = _wikipedia_summary(query)
    if summary:
        # Drop bracketed pronunciations/dates that sound awful when read aloud.
        summary = re.sub(r"\s*[(\[][^)\]]*[)\]]", "", summary)
    return summary


def _wikipedia_summary(query: str):
    try:
        import wikipedia
        topic = query.replace("wikipedia", "").replace("wiki", "").strip()
        return wikipedia.summary(topic, sentences=2, auto_suggest=False)
    except Exception as e:
        # Disambiguation: retry with the first suggested page.
        options = getattr(e, "options", None)
        if options:
            try:
                import wikipedia
                return wikipedia.summary(options[0], sentences=2, auto_suggest=False)
            except Exception:
                pass
        try:
            import wikipedia
            return wikipedia.summary(query, sentences=2)  # let the library guess
        except Exception:
            logging.info("Wikipedia search failed for %r", query, exc_info=True)
            return None
