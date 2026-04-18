from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


API_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = API_DIR.parent.parent if API_DIR.parent.name == "src" else API_DIR


class Settings(BaseSettings):
    app_name: str = "Hackathon UFMG 2026 API"
    app_env: str = "development"
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'app.db').as_posix()}"
    case_storage_dir: str = str(PROJECT_ROOT / "data" / "processos_exemplo")
    historical_csv_path: str = ""
    policy_path: str = str(PROJECT_ROOT / "policy" / "acordos_v1.yaml")
    openai_api_key: str = ""
    extract_model: str = "gpt-5.4-mini"
    analysis_model: str = "gpt-5.4"
    judge_model: str = "gpt-5.4"
    justify_model: str = "gpt-5.4"
    embedding_model: str = "text-embedding-3-large"
    enable_ingest_embeddings: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
