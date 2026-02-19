from __future__ import annotations

from anthropic import Anthropic

from .config import config
from .settings_store import SessionStore

CRITICAL_KEYWORDS = {
    "breach",
    "security incident",
    "outage",
    "data loss",
    "production down",
    "critical",
    "urgent",
    "compliance violation",
    "safety issue",
}


class ChatService:
    def __init__(self, session_store: SessionStore) -> None:
        self.session_store = session_store

    def is_critical(self, message: str) -> bool:
        low = message.lower()
        return any(k in low for k in CRITICAL_KEYWORDS)

    def build_response(
        self,
        session_id: str,
        user_message: str,
        retrieved_docs: list[str],
        settings: dict,
        api_key: str,
    ) -> tuple[str, bool]:
        if not api_key:
            return (
                "Anthropic API key is not configured. Add it in environment or UI settings to start chatting.",
                False,
            )
        client = Anthropic(api_key=api_key)

        escalated = self.is_critical(user_message)
        history = self.session_store.get_history(session_id)
        context_window_turns = int(settings.get("context_window_turns", config.context_window_turns))
        max_messages = max(2, context_window_turns * 2)
        history = history[-max_messages:]

        if not retrieved_docs:
            fallback = (
                "I couldn't find a verified answer in the current knowledge base. "
                "Please connect with a company representative for accurate guidance."
            )
            if escalated:
                fallback = "HIGH PRIORITY: " + fallback
            self.session_store.append(session_id, "user", user_message, context_window_turns)
            self.session_store.append(session_id, "assistant", fallback, context_window_turns)
            return fallback, escalated

        context_block = "\n\n".join(
            f"[KB-{idx + 1}] {chunk}" for idx, chunk in enumerate(retrieved_docs)
        )

        system_prompt = settings["system_prompt"] + (
            "\n\nRules:\n"
            "1) Use only KB snippets; do not invent details.\n"
            "2) If missing, say not found and ask user to contact representative.\n"
            "3) Be empathetic and practical.\n"
            "4) For critical issues, start with 'HIGH PRIORITY'.\n"
            "5) End with 'Sources:' and list KB ids used."
        )

        messages = []
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})

        user_payload = (
            f"User question:\n{user_message}\n\n"
            f"Knowledge base context:\n{context_block}\n\n"
            "Answer using only the context above."
        )
        messages.append({"role": "user", "content": user_payload})

        msg = client.messages.create(
            model=settings.get("model_name", config.model_name),
            max_tokens=900,
            temperature=0.2,
            system=system_prompt,
            messages=messages,
        )
        text = "\n".join(block.text for block in msg.content if hasattr(block, "text")).strip()

        if escalated and not text.lower().startswith("high priority"):
            text = "HIGH PRIORITY: " + text

        self.session_store.append(session_id, "user", user_message, context_window_turns)
        self.session_store.append(session_id, "assistant", text, context_window_turns)
        return text, escalated
