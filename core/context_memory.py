"""
core/context_memory.py - Context awareness and memory system for NOVA
Maintains conversation history, user preferences, and active tasks
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
import logging
import os

import config

logger = logging.getLogger(__name__)


class ContextMemory:
    """Manages NOVA's context awareness and memory.

    Conversation history, preferences, and active projects are persisted
    to disk (config.MEMORY_FILE) so they survive restarts; running tasks
    and the session clock are intentionally session-only.
    """

    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.user_preferences: Dict = {}
        self.active_projects: List[str] = []
        self.running_tasks: Dict = {}
        self.last_intent: Optional[str] = None
        self.last_topic: Optional[str] = None
        self.session_start_time = datetime.now()
        self._load_from_disk()

    def _load_from_disk(self):
        """Restore persisted state from config.MEMORY_FILE, if present."""
        try:
            if os.path.exists(config.MEMORY_FILE):
                with open(config.MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.conversation_history = data.get("conversation_history", [])
                self.user_preferences = data.get("user_preferences", {})
                self.active_projects = data.get("active_projects", [])
                logger.info(f"Loaded memory from {config.MEMORY_FILE}")
        except Exception:
            logger.exception("Failed to load persisted memory; starting fresh.")

    def _save_to_disk(self):
        """Persist conversation history, preferences, and projects to disk."""
        try:
            os.makedirs(config.DATA_DIR, exist_ok=True)
            with open(config.MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "conversation_history": self.conversation_history,
                    "user_preferences": self.user_preferences,
                    "active_projects": self.active_projects,
                }, f, indent=2)
        except Exception:
            logger.exception("Failed to persist memory to disk.")

    def add_exchange(self, user_input: str, assistant_response: str, intent: str = None):
        """Log a conversation exchange"""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response,
            "intent": intent,
        }
        self.conversation_history.append(exchange)
        self.last_intent = intent
        self._save_to_disk()
        logger.debug(f"Added exchange: {intent}")

    def get_recent_context(self, num_exchanges: int = 3) -> str:
        """Retrieve recent conversation context for the LLM"""
        if not self.conversation_history:
            return ""

        recent = self.conversation_history[-num_exchanges:]
        context_text = "Recent conversation:\n"
        for exchange in recent:
            context_text += f"User: {exchange['user']}\n"
            context_text += f"Nova: {exchange['assistant']}\n"
        return context_text

    def set_preference(self, key: str, value):
        """Store user preference"""
        self.user_preferences[key] = value
        self._save_to_disk()
        logger.debug(f"Set preference: {key} = {value}")

    def get_preference(self, key: str, default=None):
        """Retrieve user preference"""
        return self.user_preferences.get(key, default)

    def add_active_project(self, project_name: str):
        """Track active projects"""
        if project_name not in self.active_projects:
            self.active_projects.append(project_name)
            self._save_to_disk()
            logger.debug(f"Added active project: {project_name}")

    def get_active_projects(self) -> List[str]:
        """Get list of active projects"""
        return self.active_projects

    def start_task(self, task_id: str, task_name: str):
        """Mark a task as currently running"""
        self.running_tasks[task_id] = {
            "name": task_name,
            "started_at": datetime.now().isoformat(),
        }
        logger.debug(f"Started task: {task_name}")

    def complete_task(self, task_id: str):
        """Mark task as completed"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
            logger.debug(f"Completed task: {task_id}")

    def get_session_summary(self) -> str:
        """Generate current session summary for context"""
        elapsed = datetime.now() - self.session_start_time
        summary = f"""Session Summary:
- Duration: {elapsed.seconds // 60} minutes
- Exchanges: {len(self.conversation_history)}
- Active projects: {', '.join(self.active_projects) if self.active_projects else 'None'}
- Running tasks: {len(self.running_tasks)}
- Last intent: {self.last_intent}"""
        return summary

    def clear_history(self):
        """Clear conversation history (for 'forget' command)"""
        self.conversation_history = []
        self.last_intent = None
        self.last_topic = None
        self._save_to_disk()
        logger.info("Conversation history cleared")

    def export_context(self) -> Dict:
        """Export full context state"""
        return {
            "conversation_history": self.conversation_history,
            "user_preferences": self.user_preferences,
            "active_projects": self.active_projects,
            "running_tasks": self.running_tasks,
            "session_start": self.session_start_time.isoformat(),
        }


# Global instance
memory = ContextMemory()
