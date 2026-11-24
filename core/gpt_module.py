# core/gpt_module.py
"""
Nova's conversation brain -- used for anything that isn't a built-in command.

Backends (picked automatically, see config.LLM_BACKEND):
  1. Ollama  -- a local model server (https://ollama.com). Best quality; uses
                whatever model you've pulled, e.g. `ollama pull qwen2.5:1.5b`.
  2. Transformers -- a small instruction-tuned Hugging Face model
                (default Qwen2.5-0.5B-Instruct) that runs inside Python.

Both run fully offline. Replies are streamed sentence by sentence so Nova
can start speaking before the whole answer has been generated.
"""

import json
import logging
import re
import threading
from typing import Iterator, List, Optional

import requests

import config
from core.context_memory import memory
from core.system_prompt import build_voice_prompt

logger = logging.getLogger(__name__)

_history: List[dict] = []          # recent {"role", "content"} messages
_backend = None
_backend_checked = False
_backend_lock = threading.Lock()

NO_BACKEND_MESSAGE = (
    "My conversation model isn't available right now. "
    "Start Ollama, or run 'python -m core.download_model' once to set up the offline model."
)


# ─────────────────────────────────────────
# Backends
# ─────────────────────────────────────────
class OllamaBackend:
    name = "ollama"

    def __init__(self, model: str):
        self.model = model
        self.url = config.OLLAMA_URL.rstrip("/")
        self._send_think = True  # disable "thinking" so replies come back fast

    @classmethod
    def detect(cls) -> Optional["OllamaBackend"]:
        try:
            resp = requests.get(config.OLLAMA_URL.rstrip("/") + "/api/tags", timeout=5)
            resp.raise_for_status()
            names = [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return None
        if not names:
            print("[Nova] Ollama is running but has no models. Try: ollama pull qwen2.5:1.5b")
            return None

        wanted = config.OLLAMA_MODEL
        if not wanted:
            return cls(names[0])
        for name in names:
            if name == wanted or name.split(":")[0] == wanted:
                return cls(name)
        print(f"[Nova] Ollama model '{wanted}' isn't installed (have: {', '.join(names)}). "
              f"Run: ollama pull {wanted}")
        return None

    def _post(self, payload: dict, stream: bool):
        return requests.post(self.url + "/api/chat", json=payload, stream=stream, timeout=(5, 300))

    def stream(self, messages: List[dict]) -> Iterator[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": "30m",
            "options": {"num_predict": config.LLM_MAX_TOKENS, "temperature": 0.7},
        }
        if self._send_think:
            payload["think"] = False

        resp = self._post(payload, stream=True)
        if resp.status_code == 400 and "think" in resp.text.lower():
            # Older Ollama versions / models that don't know the option.
            self._send_think = False
            payload.pop("think", None)
            resp = self._post(payload, stream=True)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("error"):
                raise RuntimeError(data["error"])
            yield data.get("message", {}).get("content", "")
            if data.get("done"):
                break

    def warm_up(self):
        """Load the model into memory so the first real question is fast."""
        try:
            self._post({"model": self.model, "messages": [], "keep_alive": "30m"}, stream=False)
        except Exception:
            logger.debug("Ollama warm-up failed", exc_info=True)

    def __str__(self):
        return f"Ollama ({self.model})"


class TransformersBackend:
    name = "transformers"

    def __init__(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"[Nova] Loading {config.HF_MODEL_NAME} (first run downloads ~1 GB)...")
        self.tokenizer = AutoTokenizer.from_pretrained(config.HF_MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(config.HF_MODEL_NAME)
        self.model.eval()

    def stream(self, messages: List[dict]) -> Iterator[str]:
        import torch
        from transformers import TextIteratorStreamer

        input_ids = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        )
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        kwargs = dict(
            input_ids=input_ids,
            attention_mask=torch.ones_like(input_ids),
            max_new_tokens=config.LLM_MAX_TOKENS,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=self.tokenizer.eos_token_id,
            streamer=streamer,
        )
        worker = threading.Thread(target=self._generate, kwargs=kwargs, daemon=True)
        worker.start()
        yield from streamer
        worker.join()

    def _generate(self, **kwargs):
        import torch
        with torch.no_grad():
            self.model.generate(**kwargs)

    def warm_up(self):
        pass

    def __str__(self):
        return f"{config.HF_MODEL_NAME} (local)"


def get_backend():
    """Pick (once) and return the conversation backend, or None if none works."""
    global _backend, _backend_checked
    with _backend_lock:
        if _backend is not None:
            return _backend

        choice = config.LLM_BACKEND
        backend = None
        if choice in ("auto", "ollama"):
            backend = OllamaBackend.detect()
        # Only attempt the (slow) Hugging Face load once; after that, just keep
        # re-checking Ollama in case the user starts it later.
        if backend is None and not _backend_checked and choice in ("auto", "transformers"):
            try:
                backend = TransformersBackend()
            except Exception:
                logger.exception("Could not load the local Hugging Face model.")

        if backend is not None:
            print(f"[Nova] Conversation model: {backend}")
        _backend, _backend_checked = backend, True
        return backend


def warm_up_in_background():
    """Pick the backend and preload the model without blocking startup."""
    def _run():
        backend = get_backend()
        if backend:
            backend.warm_up()
    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────
# Text clean-up for speech
# ─────────────────────────────────────────
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")


def clean_for_speech(text: str) -> str:
    text = _EMOJI.sub("", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", text, flags=re.M)   # list bullets
    text = re.sub(r"[*_#`>|]+", "", text)                               # markdown symbols
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)                # [text](link)
    text = re.sub(r"^\s*nova\s*:\s*", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


# A sentence ends at . ! or ? followed by whitespace -- but not inside "..." .
_SENTENCE_END = re.compile(r"^(.+?(?<!\.)[.!?])(?!\.)[\"')\]]*\s+|^(.+?)\n+", re.S)


def _split_sentences(chunks: Iterator[str]) -> Iterator[str]:
    buffer = ""
    for chunk in chunks:
        buffer += chunk
        while True:
            match = _SENTENCE_END.match(buffer)
            if not match:
                break
            sentence = clean_for_speech(match.group(0))
            buffer = buffer[match.end():]
            if sentence:
                yield sentence
    rest = clean_for_speech(buffer)
    if rest:
        yield rest


# ─────────────────────────────────────────
# Public API
# ─────────────────────────────────────────
def _build_messages(user_input: str) -> List[dict]:
    system = build_voice_prompt(memory.get_facts(), memory.get_notes())
    return [{"role": "system", "content": system}, *_history, {"role": "user", "content": user_input}]


def _remember_turn(user_input: str, reply: str):
    _history.extend([
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": reply},
    ])
    del _history[:-config.LLM_HISTORY_TURNS * 2]


def note_exchange(user_input: str, reply: str):
    """Let the model know about commands Nova handled itself (for follow-up questions)."""
    _remember_turn(user_input, reply)


def stream_ai_response(user_input: str) -> Iterator[str]:
    """Yield the reply one sentence at a time, ready to be spoken."""
    backend = get_backend()
    if backend is None:
        yield NO_BACKEND_MESSAGE
        return

    spoken = []
    try:
        for sentence in _split_sentences(backend.stream(_build_messages(user_input))):
            spoken.append(sentence)
            yield sentence
    except requests.RequestException:
        logger.exception("Conversation model request failed.")
        if not spoken:
            yield "I couldn't reach my conversation model. Is Ollama still running?"
            return
    except Exception:
        logger.exception("Conversation model error.")
        if not spoken:
            yield "Sorry, I had trouble thinking about that. Could you try again?"
            return

    if not spoken:
        spoken = ["Hmm, I'm not sure what to say to that."]
        yield spoken[0]

    reply = " ".join(spoken)
    _remember_turn(user_input, reply)
    memory.add_exchange(user_input, reply, intent="conversation")


def get_ai_response(user_input: str) -> str:
    """Return the full reply as one string (non-streaming convenience wrapper)."""
    return " ".join(stream_ai_response(user_input))


def reset_conversation():
    """Clear conversation history (start fresh)."""
    _history.clear()
    memory.clear_history()
    logger.info("Conversation history reset")
