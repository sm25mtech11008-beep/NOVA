# core/listener.py
"""
Microphone input -> text, via Google's free speech recognition.

The recognizer is created and calibrated to the room's background noise
once, instead of spending a second re-calibrating before every phrase
(which also cut off the first words people said).
"""

import logging
import time

import speech_recognition as sr

import config

_recognizer = None
_last_network_warning = 0.0


def _get_recognizer() -> sr.Recognizer:
    global _recognizer
    if _recognizer is None:
        r = sr.Recognizer()
        r.dynamic_energy_threshold = True     # keeps adapting to background noise
        r.pause_threshold = config.PAUSE_THRESHOLD
        r.non_speaking_duration = min(0.5, config.PAUSE_THRESHOLD)
        try:
            with sr.Microphone() as source:
                print("🎙️  Calibrating microphone, please stay quiet for a moment...")
                r.adjust_for_ambient_noise(source, duration=1.5)
            # Don't let a silent room make it trigger on every tiny sound.
            r.energy_threshold = max(r.energy_threshold, 300)
        except Exception:
            logging.exception("Microphone calibration failed:")
        _recognizer = r
    return _recognizer


def takeCommand(timeout=config.LISTEN_TIMEOUT, phrase_time_limit=config.PHRASE_TIME_LIMIT,
                verbose: bool = True) -> str:
    """
    Listen on the microphone and return the recognized text ("" if nothing).

    verbose=False keeps the console quiet (used while Nova waits for its
    wake word), so it doesn't print a line every few seconds.
    """
    global _last_network_warning
    r = _get_recognizer()

    try:
        with sr.Microphone() as source:
            if verbose:
                print("🎤 Listening...")
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        return ""
    except Exception:
        logging.exception("Microphone error:")
        time.sleep(1)
        return ""

    try:
        query = r.recognize_google(audio, language=config.SPEECH_LANGUAGE)
        print(f"🗣️  You: {query}")
        return query.strip()
    except sr.UnknownValueError:
        # Background noise or mumbling -- ignore quietly.
        if verbose:
            print("   (didn't catch that)")
    except sr.RequestError:
        now = time.time()
        if now - _last_network_warning > 30:
            print("⚠️  Speech recognition needs internet. Check your connection.")
            _last_network_warning = now
        time.sleep(2)
    except Exception:
        logging.exception("Recognition error:")
    return ""
