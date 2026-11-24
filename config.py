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
# Exact phrases that wake Nova. On top of these, any word that *sounds like*
# "nova" (e.g. "innova", "nava", "novah" -- common speech-to-text mishearings)
# near the start of a sentence also counts. See core/wakeword.py.
WAKE_WORDS = [
    "hey nova", "hi nova", "hello nova", "ok nova", "okay nova", "wake up nova",
    "innova", "inova", "hey noba", "hey nobu",
]
WAKE_NAME = "nova"
SLEEP_WORDS = ["go to sleep", "stop listening", "sleep nova", "go to sleep nova", "that's all"]

# After this many seconds without hearing a command, Nova quietly goes back
# to sleep, so it doesn't keep reacting to background noise.
ACTIVE_TIMEOUT_SECONDS = int(os.getenv("NOVA_ACTIVE_TIMEOUT", "90"))

# --- Intent routing ---
CONFIDENCE_THRESHOLD = 0.6

# --- Conversation model ---
# "auto"         -> use Ollama if it is running, otherwise a small local
#                   Hugging Face model.
# "ollama"       -> only Ollama.
# "transformers" -> only the Hugging Face model.
LLM_BACKEND = os.getenv("NOVA_LLM_BACKEND", "auto").lower()

# 127.0.0.1 rather than "localhost": on Windows, "localhost" tries IPv6 first
# and adds a ~2 second delay to every request.
OLLAMA_URL = os.getenv("NOVA_OLLAMA_URL", "http://127.0.0.1:11434")
# Leave empty to automatically use the first model you have installed in Ollama.
# Smaller models answer faster on CPU, e.g. "qwen2.5:1.5b" or "llama3.2:1b".
OLLAMA_MODEL = os.getenv("NOVA_OLLAMA_MODEL", "")

# Fallback when Ollama isn't available. Small instruction-tuned chat model
# (~1 GB, runs on CPU). Downloaded once on first use.
HF_MODEL_NAME = os.getenv("NOVA_HF_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

LLM_MAX_TOKENS = int(os.getenv("NOVA_LLM_MAX_TOKENS", "120"))
LLM_HISTORY_TURNS = 3  # previous back-and-forths the model sees (more = slower on CPU)

# --- Weather ---
DEFAULT_CITY = os.getenv("NOVA_DEFAULT_CITY", "Delhi")

# --- Persistent memory ---
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
MAX_SAVED_EXCHANGES = 200

# --- Speech recognition ---
SPEECH_LANGUAGE = os.getenv("NOVA_SPEECH_LANGUAGE", "en-IN")
LISTEN_TIMEOUT = 6          # seconds to wait for speech to start
PHRASE_TIME_LIMIT = 10      # max seconds for a single phrase
PAUSE_THRESHOLD = 0.8       # seconds of silence that ends a phrase

# --- Text to speech ---
SPEECH_RATE = int(os.getenv("NOVA_SPEECH_RATE", "185"))  # words per minute
