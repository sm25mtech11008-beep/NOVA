# core/assistant.py
"""
assistant.py - Nova's Core Brain
Connects: listener -> intent detection -> command execution / AI reply -> speech

Pipeline: Observe (detect intent) -> Think (route) -> Act (execute + speak)
"""

import logging
import re

import config
from core.commands import Ask, handle_command
from core.context_memory import memory
from core.gpt_module import note_exchange, reset_conversation, stream_ai_response
from core.intent import (
    INTENT_EXIT,
    INTENT_GENERAL_CONVERSATION,
    INTENT_OPEN_APP,
    detect_intent,
    extract_entities,
)
from core.speech import speak
from core.wakeword import strip_wake_word

logger = logging.getLogger(__name__)

RESET_PHRASES = ["forget our conversation", "forget this conversation", "clear chat",
                 "reset chat", "new conversation", "start over", "clear history"]
CANCEL_WORDS = r"^(never ?mind|cancel|nothing|forget it|no|nope|leave it|stop)$"

# When Nova asked a follow-up question ("What would you like me to play?"),
# this holds the intent waiting for an answer.
_pending_intent = None

# How the answer to a follow-up question is turned back into a command.
_FOLLOW_UP_PREFIX = {
    "play_youtube": "play ",
    "search_web": "search ",
    "search_wikipedia": "who is ",
    "open_app": "open ",
    "remember_fact": "remember ",
    "forget_fact": "forget my ",
}


def say(text: str):
    """Print and speak one piece of Nova's reply."""
    print(f"🤖 Nova: {text}")
    speak(text)


def _resolve_follow_up(user_input: str):
    """
    Interpret user_input as the answer to Nova's last question.
    Returns (intent, entities) or None if it should be treated normally.
    """
    global _pending_intent
    intent, _pending_intent = _pending_intent, None
    if intent is None:
        return None

    text = user_input.lower().strip(" .!?")
    if re.match(CANCEL_WORDS, text):
        return "cancel", {}

    # A clear new command wins ("play something motivational", "what's the time").
    fresh = detect_intent(user_input)
    if fresh["intent"] != INTENT_GENERAL_CONVERSATION and fresh["intent"] != intent:
        return None
    if fresh["intent"] == intent and fresh["entities"]:
        return intent, fresh["entities"]

    prefix = _FOLLOW_UP_PREFIX.get(intent, "")
    if intent == INTENT_OPEN_APP:
        return intent, {"app": text}
    return intent, extract_entities(intent, prefix + text)


def process_command(user_input: str) -> bool:
    """
    Main processing pipeline for a single voice/text command.

    Returns:
        bool: False if the exit intent was triggered (caller should stop
        listening), True otherwise.
    """
    global _pending_intent

    user_input = strip_wake_word((user_input or "").strip())
    if not user_input:
        return True

    if any(phrase in user_input.lower() for phrase in RESET_PHRASES):
        _pending_intent = None
        reset_conversation()
        say("Okay, fresh start.")
        return True

    follow_up = _resolve_follow_up(user_input)
    if follow_up and follow_up[0] == "cancel":
        say("Okay, never mind.")
        return True

    if follow_up:
        intent, entities = follow_up
        confidence, method = 1.0, "follow-up"
    else:
        result = detect_intent(user_input)
        intent, entities = result["intent"], result["entities"]
        confidence, method = result["confidence"], result["method"]

    logger.debug("Intent: %s (%.0f%%, %s) entities=%s", intent, confidence * 100, method, entities)

    if intent != INTENT_GENERAL_CONVERSATION and confidence >= config.CONFIDENCE_THRESHOLD:
        response = handle_command(intent, user_input, entities)
        if response:
            say(response)
            if isinstance(response, Ask):
                _pending_intent = intent
            memory.add_exchange(user_input, str(response), intent=intent)
            note_exchange(user_input, str(response))
            return intent != INTENT_EXIT

    # Anything else: open-ended conversation, spoken sentence by sentence.
    print("💭 Thinking...")
    for sentence in stream_ai_response(user_input):
        say(sentence)
    return True
