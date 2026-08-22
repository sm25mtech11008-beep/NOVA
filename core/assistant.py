# core/assistant.py
"""
assistant.py - Nova's Core Brain
Connects: listener -> intent detection -> command execution -> AI response -> speech

Pipeline: Observe (detect intent) -> Think (route) -> Act (execute + speak)
"""

import logging

from core.intent import detect_intent, INTENT_GENERAL_CONVERSATION, INTENT_EXIT
from core.gpt_module import get_ai_response, reset_conversation
from core.commands import handle_command
from core.speech import speak
from core.context_memory import memory
import config

logger = logging.getLogger(__name__)

RESET_PHRASES = ["forget", "clear chat", "reset chat", "new conversation"]


def process_command(user_input: str) -> bool:
    """
    Main processing pipeline for a single voice/text command.

    Returns:
        bool: False if the exit intent was triggered (caller should stop
        listening), True otherwise.
    """
    if not user_input or not user_input.strip():
        return True

    print(f"\n[Nova] You said: {user_input}")

    if any(phrase in user_input.lower() for phrase in RESET_PHRASES):
        reset_conversation()
        speak("Okay, I've cleared our conversation history. Fresh start!")
        return True

    intent_result = detect_intent(user_input)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]
    entities = intent_result["entities"]

    print(f"[Nova] Intent: {intent} ({confidence * 100:.1f}%) | Method: {intent_result['method']}")
    if entities:
        print(f"[Nova] Entities: {entities}")

    if intent != INTENT_GENERAL_CONVERSATION and confidence >= config.CONFIDENCE_THRESHOLD:
        response = handle_command(intent, user_input, entities)
        if response:
            print(f"[Nova] Nova: {response}")
            speak(response)
            memory.add_exchange(user_input, response, intent=intent)
            return intent != INTENT_EXIT

    # Fall back to open-ended conversation
    print("[Nova] Routing to AI conversation model...")
    response = get_ai_response(user_input)
    print(f"[Nova] Nova: {response}")
    speak(response)
    return True
