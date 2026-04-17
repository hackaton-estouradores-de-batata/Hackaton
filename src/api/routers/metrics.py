from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

__all__ = ["router"]
