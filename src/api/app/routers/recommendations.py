from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationRead
from app.services.case_processing import case_processing_active, get_processing_state
from app.services.case_normalization import normalize_case_record
from app.services import apply_recommendation_payload, build_recommendation_for_case, sync_case_status

router = APIRouter(prefix="/api/cases", tags=["recommendations"])
HISTORY_TOP_K = 10


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso não encontrado.")
    return case


def _normalize_recommendation(recommendation: Recommendation) -> Recommendation:
    recommendation.regras_aplicadas = list(recommendation.regras_aplicadas or [])
    recommendation.casos_similares_ids = list(recommendation.casos_similares_ids or [])
    recommendation.policy_trace = dict(recommendation.policy_trace or {})
    return recommendation


@router.get("/{case_id}/recommendation", response_model=RecommendationRead)
def get_recommendation(case_id: str, db: Session = Depends(get_db)) -> RecommendationRead:
    case = normalize_case_record(_get_case_or_404(db, case_id))
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == case.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    processing_state = get_processing_state(case)
    if recommendation is None and case_processing_active(case):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Caso ainda em processamento pelo pipeline de analise.",
        )
    if recommendation is None and processing_state == "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O processamento do caso falhou e precisa de revisao humana.",
        )

    payload, _ = build_recommendation_for_case(
        case,
        existing_recommendation=recommendation,
        history_k=HISTORY_TOP_K,
    )
    sync_case_status(case, payload)

    if recommendation is None:
        recommendation = Recommendation(case_id=case.id, **payload)
        db.add(recommendation)
    else:
        apply_recommendation_payload(recommendation, payload)

    db.commit()
    db.refresh(recommendation)

    return RecommendationRead.model_validate(_normalize_recommendation(recommendation))
