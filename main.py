# main.py
"""
Entrypoint for Nova.

Voice mode (default): passive-listens for a wake word, then actively
processes commands through core.assistant.process_command until a sleep
word or exit is heard.

Text mode (`python main.py --text`): a plain CLI chat loop using the same
assistant pipeline, no microphone required -- handy for development,
testing, or headless use.
"""

import argparse
import sys
import time
import logging

import config
from core.speech import speak
from core.assistant import process_command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def safe_listen():
    """Wrapper around takeCommand() that always returns a normalized string."""
    from core.listener import takeCommand
    try:
        result = takeCommand()
        return str(result).strip().lower() if result else ""
    except Exception:
        logging.exception("Error while listening:")
        time.sleep(0.5)
        return ""


def active_listen():
    logging.info("Nova is active now.")
    try:
        while True:
            query = safe_listen()
            if not query:
                continue

            if any(sleep_word in query for sleep_word in config.SLEEP_WORDS):
                speak("Going to sleep. Say 'Hey Nova' to wake me again.")
                break

            keep_going = process_command(query)
            if not keep_going:
                sys.exit(0)

    except KeyboardInterrupt:
        logging.info("Interrupted by user while active. Returning to passive mode.")
    except Exception:
        logging.exception("Unhandled exception in active_listen(). Returning to passive.")


def passive_listen():
    logging.info("Nova is sleeping. Waiting for wake word...")
    try:
        while True:
            query = safe_listen()
            if not query:
                continue

            if any(wake_word in query for wake_word in config.WAKE_WORDS):
                logging.info("Wake word detected.")
                speak("Yes, I'm here!")
                active_listen()
                logging.info("Returned to passive listening.")
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting.")
        sys.exit(0)


def text_mode():
    print("Nova text mode. Type a command, or 'exit' to quit.\n")
    try:
        while True:
            query = input("You: ").strip()
            if not query:
                continue
            keep_going = process_command(query)
            if not keep_going:
                break
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye, sir!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nova voice assistant")
    parser.add_argument("--text", action="store_true", help="Run in text-only mode (no microphone required)")
    args = parser.parse_args()

    if args.text:
        text_mode()
    else:
        passive_listen()
