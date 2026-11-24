# core/download_model.py
"""
One-time setup for Nova's conversation model.

    python -m core.download_model

If Ollama is running, makes sure the configured model is pulled.
Otherwise downloads the small Hugging Face fallback model so the
first conversation doesn't have to wait for it.
"""

import subprocess

import requests

import config

DEFAULT_OLLAMA_MODEL = "qwen2.5:1.5b"


def _ollama_models():
    try:
        resp = requests.get(config.OLLAMA_URL.rstrip("/") + "/api/tags", timeout=5)
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return None


if __name__ == "__main__":
    models = _ollama_models()
    if models is not None and config.LLM_BACKEND != "transformers":
        wanted = config.OLLAMA_MODEL or (models[0] if models else DEFAULT_OLLAMA_MODEL)
        if any(m == wanted or m.split(":")[0] == wanted for m in models):
            print(f"Ollama is running and '{wanted}' is installed. You're all set.")
        else:
            print(f"Pulling '{wanted}' with Ollama (only needed once)...")
            subprocess.run(["ollama", "pull", wanted], check=False)
    else:
        print("Ollama isn't running, so setting up the built-in fallback model instead.")
        print(f"Downloading {config.HF_MODEL_NAME} (only needed once)...")
        from transformers import AutoModelForCausalLM, AutoTokenizer
        AutoTokenizer.from_pretrained(config.HF_MODEL_NAME)
        AutoModelForCausalLM.from_pretrained(config.HF_MODEL_NAME)
        print("Done. The model is cached locally.")
