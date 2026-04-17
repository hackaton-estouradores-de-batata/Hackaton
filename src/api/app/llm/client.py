from functools import lru_cache

from openai import OpenAI

from app.core.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI | None:
    api_key = get_settings().openai_api_key
    if not api_key:
        return None
    return OpenAI(api_key=api_key)
