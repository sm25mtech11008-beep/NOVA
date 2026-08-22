# core/download_model.py
"""Pre-download and cache the offline conversation model so first launch is fast."""

from transformers import AutoModelForCausalLM, AutoTokenizer

import config

if __name__ == "__main__":
    print(f"Downloading {config.GPT_MODEL_NAME} (this only needs to run once)...")
    AutoTokenizer.from_pretrained(config.GPT_MODEL_NAME)
    AutoModelForCausalLM.from_pretrained(config.GPT_MODEL_NAME)
    print("Done. Model is cached locally.")
