import json
from pathlib import Path
from .config import config


DEFAULT_SYSTEM_PROMPT = (
    "You are Arvind's Bot, a B2B onboarding and integration assistant. "
    "Be conversational, clear, and empathetic. Use only the provided knowledge-base context as truth. "
    "If answer is not present or ambiguous in context, say you cannot confirm from the knowledge base and "
    "ask the user to connect with a company representative. "
    "For critical issues (security incidents, production outages, safety risks, data loss, compliance breaches), "
    "mark as HIGH PRIORITY and advise immediate representative escalation."
)


class SettingsStore:
    def __init__(self) -> None:
        self.path = config.data_dir / "settings.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(
                {
                    "system_prompt": DEFAULT_SYSTEM_PROMPT,
                    "model_name": config.model_name,
                    "context_window_turns": config.context_window_turns,
                    "top_k": config.top_k,
                    "similarity_threshold": config.similarity_threshold,
                    "enable_image_understanding": False,
                    "anthropic_api_key": config.anthropic_api_key,
                }
            )

    def load(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, payload: dict) -> dict:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return payload


class SessionStore:
    def __init__(self) -> None:
        self.path = config.data_dir / "sessions.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save({})

    def _load(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_history(self, session_id: str) -> list[dict]:
        return self._load().get(session_id, [])

    def append(self, session_id: str, role: str, content: str, max_turns: int) -> None:
        data = self._load()
        history = data.get(session_id, [])
        history.append({"role": role, "content": content})
        max_messages = max(2, max_turns * 2)
        data[session_id] = history[-max_messages:]
        self._save(data)
