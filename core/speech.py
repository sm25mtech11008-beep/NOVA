# core/speech.py
import logging
import platform

import config

_muted = False


def _init_engine():
    try:
        import pyttsx3
        system = platform.system().lower()
        if system == "windows":
            engine = pyttsx3.init("sapi5")
        elif system == "darwin":
            engine = pyttsx3.init("nsss")
        else:
            engine = pyttsx3.init("espeak")
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)
        engine.setProperty("rate", config.SPEECH_RATE)
        return engine
    except Exception:
        logging.exception("Failed to initialize the text-to-speech engine; replies will be text only.")
        return None


engine = _init_engine()


def set_muted(muted: bool):
    """Turn spoken output off/on (text is still printed)."""
    global _muted
    _muted = muted


def speak(text: str):
    """Convert text to speech."""
    if not text or _muted or not engine:
        return
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        logging.exception("Speech synthesis failed.")
