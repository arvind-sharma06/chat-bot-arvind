from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    used_context: list[str] = Field(default_factory=list)
    escalated: bool = False


class SettingsPayload(BaseModel):
    system_prompt: str
    model_name: str = "claude-haiku-4-5-20251001"
    context_window_turns: int = 8
    top_k: int = 6
    similarity_threshold: float = 0.28
    enable_image_understanding: bool = False
    anthropic_api_key: Optional[str] = None


class ReindexPayload(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
