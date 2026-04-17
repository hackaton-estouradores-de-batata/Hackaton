from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db import engine
from app.models import case, outcome, recommendation  # noqa: F401
from app.models.base import Base
from app.routers.cases import router as cases_router
from app.routers.health import router as health_router
from app.routers.outcomes import router as outcomes_router
from app.routers.recommendations import router as recommendations_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(cases_router)
    app.include_router(recommendations_router)
    app.include_router(outcomes_router)

    return app


app = create_app()
