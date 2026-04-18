from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.case import Case
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.schemas.outcome import OutcomeCreate, OutcomeRead

router = APIRouter(prefix="/api/cases", tags=["outcomes"])


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso não encontrado.")
    return case


@router.post("/{case_id}/outcome", response_model=OutcomeRead, status_code=status.HTTP_201_CREATED)
def create_outcome(case_id: str, payload: OutcomeCreate, db: Session = Depends(get_db)) -> Outcome:
    case = _get_case_or_404(db, case_id)
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == case.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    sentenca = payload.sentenca
    if payload.decisao_advogado == "acordo" and payload.resultado_negociacao == "aceito":
        sentenca = "acordo"

    outcome = Outcome(
        case_id=case.id,
        recommendation_id=recommendation.id if recommendation else None,
        decisao_advogado=payload.decisao_advogado,
        seguiu_recomendacao=bool(recommendation and recommendation.decisao == payload.decisao_advogado),
        valor_proposto=payload.valor_proposto,
        valor_acordado=payload.valor_acordado,
        resultado_negociacao=payload.resultado_negociacao,
        sentenca=sentenca,
        valor_condenacao=payload.valor_condenacao,
        custos_processuais=payload.custos_processuais,
    )
    db.add(outcome)

    case.status = "closed" if payload.resultado_negociacao == "aceito" else "decided"

    db.commit()
    db.refresh(outcome)
    return outcome
