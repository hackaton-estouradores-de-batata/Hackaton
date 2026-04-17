from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationRead
from app.services import build_recommendation_payload, load_policy

router = APIRouter(prefix="/api/cases", tags=["recommendations"])


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso não encontrado.")
    return case


def _normalize_recommendation(recommendation: Recommendation) -> Recommendation:
    recommendation.regras_aplicadas = list(recommendation.regras_aplicadas or [])
    recommendation.casos_similares_ids = list(recommendation.casos_similares_ids or [])
    return recommendation


@router.get("/{case_id}/recommendation", response_model=RecommendationRead)
def get_recommendation(case_id: str, db: Session = Depends(get_db)) -> RecommendationRead:
    case = _get_case_or_404(db, case_id)
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == case.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    if recommendation is None:
        payload = build_recommendation_payload(
            {
                "valor_causa": case.valor_causa,
                "valor_pedido_danos_morais": case.valor_pedido_danos_morais,
                "red_flags": case.red_flags,
                "vulnerabilidade_autor": case.vulnerabilidade_autor,
                "indicio_fraude": case.indicio_fraude,
                "forca_narrativa_autor": case.forca_narrativa_autor,
                "subsidios": case.subsidios,
            },
            load_policy(),
        )
        recommendation = Recommendation(case_id=case.id, **payload)
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)

    return RecommendationRead.model_validate(_normalize_recommendation(recommendation))
