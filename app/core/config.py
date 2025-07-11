from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    UPLOAD_DIR: str = str(Path(__file__).parent.parent.parent / "uploads")
    PORT: int = 8090
    MONGO_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()