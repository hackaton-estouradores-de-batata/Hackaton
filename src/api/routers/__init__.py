from app.routers.cases import router as cases_router
from app.routers.health import router as health_router
from app.routers.outcomes import router as outcomes_router
from app.routers.recommendations import router as recommendations_router

__all__ = ["cases_router", "health_router", "outcomes_router", "recommendations_router"]
