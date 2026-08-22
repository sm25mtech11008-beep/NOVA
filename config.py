# config.py
"""
Central configuration for Nova. Keeps constants out of individual modules
so behavior can be tuned in one place. Optional overrides can be supplied
via environment variables (loaded from .env if python-dotenv is installed).
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Wake / sleep control ---
WAKE_WORDS = ["hey nova", "wake up nova"]
SLEEP_WORDS = ["go to sleep", "stop listening", "sleep nova", "go to sleep nova"]

# --- Intent routing ---
CONFIDENCE_THRESHOLD = 0.6

# --- Offline conversation model (DialoGPT) ---
GPT_MODEL_NAME = os.getenv("NOVA_GPT_MODEL", "microsoft/DialoGPT-medium")

# --- Weather ---
DEFAULT_CITY = os.getenv("NOVA_DEFAULT_CITY", "Delhi")

# --- Persistent memory ---
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

# --- Speech recognition ---
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 8
