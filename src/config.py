from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/lenny_assistant"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GEMINI_API_KEY: str = ""
    RETRIEVAL_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.5
    LOG_LEVEL: str = "INFO"

settings = Settings()
