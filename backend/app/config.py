from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    model_name: str = Field(default="claude-haiku-4-5-20251001", alias="MODEL_NAME")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    uploads_dir: Path = Field(default=Path("data/uploads"), alias="UPLOADS_DIR")
    chroma_dir: Path = Field(default=Path("data/chroma"), alias="CHROMA_DIR")
    context_window_turns: int = Field(default=8, alias="CONTEXT_WINDOW_TURNS")
    top_k: int = Field(default=6, alias="TOP_K")
    similarity_threshold: float = Field(default=0.28, alias="SIMILARITY_THRESHOLD")

    class Config:
        populate_by_name = True
        env_file = ".env"
        extra = "ignore"


config = AppConfig()
