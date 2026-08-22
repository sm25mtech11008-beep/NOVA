"""
gpt_module.py - Upgraded AI Response Module for Nova with System Prompt Integration
Replaces broken OpenAI API with:
  - Hugging Face DialoGPT-medium (offline, free, conversational)
  - NOVA system prompt to guide personality and behavior
  - Conversation history for context-aware replies
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import logging
from core.system_prompt import NOVA_SYSTEM_PROMPT, VOICE_RESPONSE_RULES, PERSONALITY_TRAITS
from core.context_memory import memory
import config

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Model Configuration
# ─────────────────────────────────────────
MODEL_NAME = config.GPT_MODEL_NAME

tokenizer = None
model = None
chat_history_ids = None  # Keeps conversation context


def load_model():
    """Load DialoGPT model (downloads once, cached after)."""
    global tokenizer, model
    print("[Nova] Loading AI model (first run may take a moment)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()
    print("[Nova] AI model loaded successfully.")
    logger.info("DialoGPT model loaded")


def build_system_context() -> str:
    """Build system context from NOVA prompt and current state"""
    context = f"""System Context:
{NOVA_SYSTEM_PROMPT}

{VOICE_RESPONSE_RULES}

Personality: {', '.join(f"{k.replace('_', ' ')}: {v}" for k, v in PERSONALITY_TRAITS.items())}

Current State:
- {memory.get_session_summary()}
"""
    return context


def get_ai_response(user_input: str, max_new_tokens: int = 100) -> str:
    """
    Generate a conversational AI response using DialoGPT with NOVA system guidance.
    Maintains conversation history for multi-turn context.
    
    Args:
        user_input: The user's spoken/typed query
        max_new_tokens: Max tokens to generate

    Returns:
        str: AI-generated response optimized for voice output
    """
    global tokenizer, model, chat_history_ids

    if tokenizer is None or model is None:
        load_model()

    try:
        # Build prompt with system guidance
        system_context = build_system_context()
        
        # Prepare input with system guidance
        structured_input = f"Context: {system_context[:200]}...\n\nUser: {user_input}"
        
        # Encode user input + append EOS token
        new_input_ids = tokenizer.encode(
            structured_input + tokenizer.eos_token,
            return_tensors="pt"
        )

        # Concatenate with chat history for context
        bot_input_ids = (
            torch.cat([chat_history_ids, new_input_ids], dim=-1)
            if chat_history_ids is not None
            else new_input_ids
        )

        # Limit context to last 1000 tokens to avoid overflow
        if bot_input_ids.shape[-1] > 1000:
            bot_input_ids = bot_input_ids[:, -1000:]

        attention_mask = torch.ones_like(bot_input_ids)

        # Generate response
        with torch.no_grad():
            chat_history_ids = model.generate(
                bot_input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.75,
                no_repeat_ngram_size=3,
            )

        # Decode only the new response tokens
        response = tokenizer.decode(
            chat_history_ids[:, bot_input_ids.shape[-1]:][0],
            skip_special_tokens=True
        )

        response = response.strip() if response.strip() else "I'm not sure how to respond to that."
        
        # Log to memory for context
        memory.add_exchange(user_input, response, intent="conversation")
        
        logger.debug(f"AI response generated: {response[:50]}...")
        return response

    except Exception as e:
        logger.exception(f"AI response error: {e}")
        return "Sorry, I had trouble processing that. Could you try again?"


def reset_conversation():
    """Clear conversation history (start fresh)."""
    global chat_history_ids
    chat_history_ids = None
    memory.clear_history()
    print("[Nova] Conversation history cleared.")
    logger.info("Conversation history reset")
