# core/listener.py
import speech_recognition as sr
from core.speech import speak
import webbrowser
import logging

import config

def takeCommand(timeout=config.LISTEN_TIMEOUT, phrase_time_limit=config.PHRASE_TIME_LIMIT):
    """
    Listen from microphone and return recognized speech as text.
    Returns None if nothing recognized or error occurs.
    """
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🎤 Listening...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        print("⏰ Timeout: No speech detected.")
        return None
    except Exception as e:
        logging.exception("Microphone error:")
        return None

    try:
        print("🧠 Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"🗣️ User said: {query}\n")

        # Inline Google search trigger
        if "search on google" in query.lower():
            search_term = query.lower().replace("search on google", "").strip()
            speak(f"Searching {search_term} on Google...")
            webbrowser.open(f"https://www.google.com/search?q={search_term}")
            return None

        return query

    except sr.UnknownValueError:
        print("🤖 Sorry, I couldn't understand that.")
    except sr.RequestError:
        print("⚠️ Speech service unavailable. Check your internet connection.")
    except Exception:
        logging.exception("Recognition error:")

    return None
