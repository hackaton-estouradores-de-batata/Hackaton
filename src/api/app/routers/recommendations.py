from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.historical import summarize_case_history
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


def _enrich_recommendation_with_history(case: Case, recommendation: Recommendation) -> Recommendation:
    history_summary = summarize_case_history(case)
    stats = history_summary["stats"]

    recommendation.casos_similares_ids = history_summary["casos_similares_ids"]
    recommendation.regras_aplicadas = list(recommendation.regras_aplicadas or [])
    if "HIST-01: resumo histórico inicial" not in recommendation.regras_aplicadas:
        recommendation.regras_aplicadas.append("HIST-01: resumo histórico inicial")

    base_justificativa = recommendation.justificativa or "Recomendação gerada a partir da política atual."
    recommendation.justificativa = (
        f"{base_justificativa} Resumo histórico: prob_vitoria={stats['prob_vitoria']:.2f}, "
        f"p25={stats['percentil_25']}, p50={stats['percentil_50']}."
    )
    if recommendation.policy_version == "v1":
        recommendation.policy_version = "v1-hist"
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
        recommendation = _enrich_recommendation_with_history(case, recommendation)
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)

    return RecommendationRead.model_validate(_normalize_recommendation(recommendation))
