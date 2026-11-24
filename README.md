# 🎙️ Nova Voice Assistant

Nova is an intelligent, fully offline-capable local-first voice assistant built in Python with a **production-grade system prompt** inspired by Jarvis.

It recognizes voice commands, speaks back, opens websites, plays YouTube videos, fetches Wikipedia summaries, checks the weather, launches apps, controls basic system functions, and falls back to an offline conversational AI model for anything else — all with persistent memory across sessions.

## ✨ Features

- 🎧 Voice recognition with Google Speech API (plus a `--text` mode that needs no microphone)
- 🗣️ Natural speech replies using pyttsx3
- 🌐 Opens common websites & performs web searches
- 📚 Fetches Wikipedia summaries
- 🎵 Plays YouTube music, mood playlists, and fun facts
- ⛅ Live weather lookups (no API key required)
- 🖥️ Launches apps (VS Code, Chrome, Notepad, Calculator, File Explorer, Settings, Task Manager, Terminal, Paint) and controls the system (lock screen, volume, mute)
- 🤖 Offline conversation through a real chat model (Ollama, or a small built-in Hugging Face model), streamed so Nova starts talking sooner
- 🎂 Remembers facts about you ("my birthday is 5th March", "what's my name", "what do you know about me")
- 🔁 Follow-up questions ("play something" → "What would you like me to play?" → "arijit singh")
- 👂 Forgiving wake word ("Hey Nova", or mishearings like "Innova"), and you can say the command in the same breath
- 🎯 Fast, fully offline keyword/regex intent detection — no model download on the critical path
- 🧠 Context-aware conversation with a memory system
- 💾 Conversation history, preferences, and active projects persisted to disk across restarts
- ⚡ Short, voice-friendly replies (one or two sentences, no markdown)
- 🎭 Personality-driven responses (intelligent, calm, witty)

## 🆕 What's New

- **Real conversation model.** DialoGPT echoed its own prompt ("Context : System Context…") and gave one-word answers. It has been replaced by Ollama, or a small instruction-tuned Hugging Face model as a fallback.
- **Personal memory.** Nova remembers your name, birthday and notes, and answers "when is my birthday" with the days remaining.
- **Follow-ups.** When Nova asks "What would you like me to play?", your next sentence is treated as the answer.
- **Better listening.** The wake word tolerates mishearings, the microphone is calibrated once instead of before every phrase, background noise is ignored quietly, and Nova goes back to sleep after 90 seconds of silence.
- **Smarter commands.** "what time is it", "play something motivational", "search for …", "what can you do" and more phrasings are understood. Tests live in `tests/`.

## 🚀 Quick Start

### Setup
```bash
git clone https://github.com/sm25mtech11008-beep/NOVA.git
cd NOVA
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Set up the conversation model (recommended)
Install [Ollama](https://ollama.com), then pull a model. Smaller models answer faster on a CPU:
```bash
ollama pull qwen2.5:1.5b      # fast, good for voice
```
Nova uses the first installed Ollama model automatically (set `NOVA_OLLAMA_MODEL` in `.env` to choose one).
Without Ollama, Nova falls back to `Qwen/Qwen2.5-0.5B-Instruct` via transformers (downloaded once, ~1 GB).

### Run (voice mode)
```bash
python main.py
```
Say "Hey Nova" (or "Hey Nova, what's the time?"), then keep talking. Say "go to sleep", or stay quiet for 90 seconds, to put it back to sleep.

### Things to say
| Say | What happens |
|---|---|
| "play arijit singh songs" / "play something relaxing" | Plays on YouTube |
| "what's the weather in Mumbai" | Live weather |
| "what time is it" / "what's the date" | Time / date |
| "open chrome" / "open youtube" | Opens apps and websites |
| "search for best biryani" / "who is Ada Lovelace" | Google / Wikipedia |
| "my name is …" / "my birthday is 5th March" / "remember that …" | Nova remembers it |
| "when is my birthday" / "what do you know about me" / "forget my birthday" | Recall / forget |
| "turn up the volume" / "mute" / "lock the screen" | System control |
| "tell me a joke" / "what can you do" | Fun / help |
| anything else | Answered by the conversation model |

### Run (text mode, no microphone needed)
```bash
python main.py --text           # add --mute to turn off spoken replies, --debug for logs
```

### Run the tests
```bash
python -m pytest tests
```

### One-time model setup (optional, speeds up first run)
```bash
python -m core.download_model
```

### Verify System Prompt Implementation
```bash
python verify_implementation.py
```

## 📖 System Prompt Architecture

Nova is built on a **Jarvis-level system prompt** with:

### Core Identity
- Proactive voice operating system
- Understands intent accurately
- Completes tasks with minimum friction
- Speaks naturally and concisely
- Remembers context across conversations

### Personality
- **Intelligent** - Understands complex requests
- **Calm** - Maintains steady demeanor
- **Slightly witty** - Uses light humor appropriately
- **Confident** - Acts decisively
- **Helpful** - Always aims to assist

Never robotic, overly formal, or overly emotional.

### Key Behaviors
- **Observe → Think → Act** reasoning pipeline
- Context-aware responses from conversation history
- Voice-optimized output (5-20 seconds)
- Proactive assistance and suggestions
- Safety confirmations for dangerous operations
- Emotional intelligence and tone adaptation

### Memory System
- Tracks conversation history across sessions
- Manages user preferences
- Monitors active projects
- Tracks running tasks
- Provides session summaries

## 📁 Core Components

### System Prompt Configuration
- **`core/system_prompt.py`** - Complete system prompt with personality traits, tool priorities, and safety rules

### Memory & Context System
- **`core/context_memory.py`** - Conversation history, preferences, projects, and task tracking, persisted to `data/memory.json`

### Core Modules
- **`core/intent.py`** - Fast, fully offline keyword/regex intent detection
- **`core/commands.py`** - Command handlers (websites, Wikipedia, YouTube, weather, apps, system control)
- **`core/gpt_module.py`** - Conversation model (Ollama or local Hugging Face), streamed sentence by sentence
- **`core/wakeword.py`** - Forgiving wake-word matching
- **`core/assistant.py`** - The pipeline that ties intent detection, commands, AI fallback, and memory together
- **`core/weather.py`** - Keyless weather lookups (Open-Meteo)
- **`core/apps.py`** - App launching and system control (lock screen, volume)
- **`config.py`** - Central configuration (wake/sleep words, model name, default city, confidence threshold)

## 💡 Usage Examples

### Basic Conversation
```python
from core.assistant import process_command

process_command("Tell me about machine learning")
# Response uses system prompt + context awareness
```

### Memory & Preferences
```python
from core.context_memory import memory

# Store preferences
memory.set_preference("user_name", "Shash")

# Track projects
memory.add_active_project("M.Tech Placements")

# Conversation logged automatically
```

### AI Response with Context
```python
from core.gpt_module import get_ai_response

response = get_ai_response("Continue where we left off")
# Includes recent conversation history in response
```

## 🔧 Configuration

### Customize Personality
Edit `core/system_prompt.py`:
```python
PERSONALITY_TRAITS = {
    "tone": "professional yet conversational",
    "energy_level": "calm and focused",
    "humor": "light and contextual",
}
```

### Set User Preferences
```python
memory.set_preference("preferred_response_length", "short")
memory.set_preference("speaking_style", "casual")
```

### Add Projects
```python
memory.add_active_project("Machine Learning Research")
```

## 📋 Tech Stack

- **Speech Recognition**: Google Speech API (SpeechRecognition)
- **Text-to-Speech**: pyttsx3
- **Intent Detection**: Regex/keyword rules (fast, offline, no model download)
- **AI Model**: any Ollama model (recommended), or Qwen2.5-0.5B-Instruct via transformers
- **Framework**: Transformers (Hugging Face)
- **Weather**: Open-Meteo (free, no API key)
- **Backend**: Python 3.8+
- **Execution**: Local — the AI model runs fully offline; websites, Wikipedia, YouTube, and weather commands need internet like any browser action would

## 🩺 Troubleshooting

- **Replies are slow** – a 4B model on CPU takes ~10 s per answer. Pull a smaller one (`ollama pull qwen2.5:1.5b`) and set `NOVA_OLLAMA_MODEL=qwen2.5:1.5b` in `.env`.
- **"My conversation model isn't available"** – start Ollama, or run `python -m core.download_model`.
- **Nova doesn't wake up** – watch what it heard (printed as `You: …`) and add that mishearing to `WAKE_WORDS` in `config.py`.
- **Reacts to background noise** – it ignores unclear audio and goes back to sleep after `NOVA_ACTIVE_TIMEOUT` seconds (default 90).

## 🛡️ Safety Features

### Automatic Confirmations Required For:
- ⚠️ Delete file/directory
- ⚠️ Run scripts
- ⚠️ Install packages
- ⚠️ Modify system settings
- ⚠️ Send emails
- ⚠️ Financial transactions

### Safe to Execute Immediately:
- ✓ Read files
- ✓ List directories
- ✓ Check time/calendar
- ✓ Get weather
- ✓ Search files

## 📊 Project Structure

```
nova/
├── core/
│   ├── system_prompt.py       # System prompt config
│   ├── context_memory.py      # Memory system (persisted to data/memory.json)
│   ├── gpt_module.py          # Conversation model (Ollama / Hugging Face)
│   ├── wakeword.py            # Forgiving wake-word matching
│   ├── assistant.py           # Pipeline: intent -> command/AI -> speech -> memory
│   ├── intent.py              # Fast offline keyword/regex intent detection
│   ├── commands.py            # Command handlers
│   ├── weather.py             # Keyless weather lookups
│   ├── apps.py                # App launching + system control
│   ├── listener.py
│   ├── speech.py
│   └── download_model.py
├── main.py                    # Voice mode (default) or --text mode
├── config.py                  # Central configuration
├── tests/                     # Intent + wake-word tests
├── verify_implementation.py   # Verification script
├── requirements.txt
└── README.md
```

## 🧪 Testing

Run the verification script:
```bash
python verify_implementation.py
```

Expected output:
```
✅ system_prompt.py loaded
✅ context_memory.py loaded
✅ Memory system working
✅ Configuration verified
🚀 NOVA is ready!
```

## 🚀 Next Steps

1. **Test with voice**: Run `python main.py` and speak commands
2. **Customize**: Edit personality traits and preferences
3. **Extend**: Add calendar, email, and screen awareness
4. **Enhance**: Add autonomous agent mode for high-level goals

## 📝 License

MIT License — feel free to modify and extend.

## 🎯 Vision

Nova aims to be a **local-first, privacy-respecting voice assistant** with:
- Jarvis-level personality and proactive behavior
- Complete offline operation
- Context-aware multi-turn conversations
- Safety-first approach to system operations
- Extensible framework for custom integrations

---

**Status**: ✅ Working end-to-end (voice + text mode), offline conversational fallback, persistent memory

**Last Updated**: 2026-11-24
