# main.py
"""
Entrypoint for Nova.

Voice mode (default):  python main.py
    Say "Hey Nova" (optionally followed by a command), then keep talking.
    Say "go to sleep" -- or stay quiet for a while -- to put Nova back to sleep.

Text mode:  python main.py --text
    Type instead of talking. Add --mute to turn off the spoken replies.
"""

import argparse
import logging
import sys
import time

import config
from core.assistant import process_command, say
from core.gpt_module import warm_up_in_background
from core.speech import set_muted
from core.wakeword import split_wake_word

# Windows consoles/redirects may not be UTF-8; never crash on an emoji.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure:
        _reconfigure(errors="replace")

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

BANNER = """
──────────────────────────────────────────────
  Nova is ready.
  • Say "Hey Nova" to wake me (you can add a command: "Hey Nova, what's the time?")
  • Try: "play lofi music", "what's the weather", "my birthday is 5th March",
         "open chrome", "tell me a joke", "what can you do"
  • Say "go to sleep" when you're done. Ctrl+C quits.
──────────────────────────────────────────────"""


def listen(verbose: bool = True) -> str:
    from core.listener import takeCommand
    return takeCommand(verbose=verbose)


def active_listen():
    """Handle commands until the user says a sleep word or goes quiet."""
    last_heard = time.time()
    while True:
        query = listen()
        if not query:
            if time.time() - last_heard > config.ACTIVE_TIMEOUT_SECONDS:
                print("💤 No commands for a while, going back to sleep. Say 'Hey Nova' to wake me.")
                return True
            continue

        last_heard = time.time()
        if any(word in query.lower() for word in config.SLEEP_WORDS):
            say("Okay, going to sleep. Say 'Hey Nova' when you need me.")
            return True

        if not process_command(query):
            return False  # exit requested


def voice_mode():
    print(BANNER)
    print("😴 Waiting for 'Hey Nova'...")
    try:
        while True:
            query = listen(verbose=False)
            woke, command = split_wake_word(query)
            if not woke:
                continue

            if command.strip():
                # "Hey Nova, what's the time?" -- handle the command right away.
                if not process_command(command):
                    return
            else:
                say("Yes?")

            if not active_listen():
                return
            print("😴 Waiting for 'Hey Nova'...")
    except KeyboardInterrupt:
        print("\nGoodbye!")


def text_mode():
    print("Nova text mode. Type a message, or 'exit' to quit. Try 'what can you do'.\n")
    try:
        while True:
            query = input("You: ").strip()
            if query and not process_command(query):
                break
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nova voice assistant")
    parser.add_argument("--text", action="store_true", help="type instead of talking (no microphone needed)")
    parser.add_argument("--mute", action="store_true", help="don't speak replies out loud")
    parser.add_argument("--debug", action="store_true", help="show detailed logs")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    set_muted(args.mute)
    warm_up_in_background()  # load the conversation model while we wait for the user

    if args.text:
        text_mode()
    else:
        voice_mode()
    sys.exit(0)
