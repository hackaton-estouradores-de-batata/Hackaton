from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Hackathon UFMG 2026 API"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/app.db"
    case_storage_dir: str = str(BASE_DIR / "data" / "processos_exemplo")
    openai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
