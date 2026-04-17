from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.historical import summarize_case_history
from app.db import get_db
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationRead

router = APIRouter(prefix="/api/cases", tags=["recommendations"])


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso não encontrado.")
    return case


def _build_stub_recommendation(case: Case) -> RecommendationRead:
    valor_base = Decimal(case.valor_causa or 3000)
    valor_min = (valor_base * Decimal("0.15")).quantize(Decimal("0.01"))
    valor_max = (valor_base * Decimal("0.25")).quantize(Decimal("0.01"))
    decisao = "defesa" if (case.valor_causa or 0) <= 5000 else "acordo"
    history_summary = summarize_case_history(case)
    stats = history_summary["stats"]

    return RecommendationRead(
        id=f"stub-{case.id}",
        case_id=case.id,
        decisao=decisao,
        valor_sugerido_min=valor_min if decisao == "acordo" else None,
        valor_sugerido_max=valor_max if decisao == "acordo" else None,
        justificativa=(
            "Recomendação inicial gerada com apoio da camada histórica da Sprint 2 "
            f"(prob_vitoria={stats['prob_vitoria']:.2f}, p25={stats['percentil_25']}, p50={stats['percentil_50']})."
        ),
        confianca=0.61,
        policy_version="v0-mvp-sprint2",
        regras_aplicadas=["MVP-01: fallback operacional", "HIST-01: resumo histórico inicial"],
        casos_similares_ids=history_summary["casos_similares_ids"],
        judge_concorda=True,
        judge_observacao=None,
    )


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
        return _build_stub_recommendation(case)

    return RecommendationRead.model_validate(recommendation)
