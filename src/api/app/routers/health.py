from sqlalchemy.engine import make_url

from fastapi import APIRouter

from app.core.config import get_settings
from app.llm.client import has_active_openai_credentials

router = APIRouter(tags=["health"])


@router.get("/")
def read_root() -> dict[str, str]:
    settings = get_settings()
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "status": "ok",
    }


@router.get("/healthz")
def read_health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "database_backend": make_url(settings.database_url).get_backend_name(),
        "llm_mode": "openai" if has_active_openai_credentials() else "local_fallback",
    }
