from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.case import Case
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.schemas.dashboard import DashboardMetricsRead

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetricsRead)
def get_dashboard_metrics(db: Session = Depends(get_db)) -> DashboardMetricsRead:
    try:
        total_cases = db.query(Case).count()
        total_recommendations = db.query(Recommendation).count()
        total_outcomes = db.query(Outcome).count()

        followed_count = db.query(Outcome).filter(Outcome.seguiu_recomendacao.is_(True)).count()
        accepted_count = db.query(Outcome).filter(Outcome.resultado_negociacao == "aceito").count()

        judged_recommendations = db.query(Recommendation).filter(Recommendation.judge_concorda.is_not(None)).count()
        judge_disagreements = db.query(Recommendation).filter(Recommendation.judge_concorda.is_(False)).count()
    except OperationalError:
        total_cases = 0
        total_recommendations = 0
        total_outcomes = 0
        followed_count = 0
        accepted_count = 0
        judged_recommendations = 0
        judge_disagreements = 0

    adherence_pct = (followed_count / total_outcomes * 100) if total_outcomes else 0.0
    agreement_acceptance_pct = (accepted_count / total_outcomes * 100) if total_outcomes else 0.0
    judge_disagreement_pct = (
        judge_disagreements / judged_recommendations * 100 if judged_recommendations else 0.0
    )

    return DashboardMetricsRead(
        total_cases=total_cases,
        total_recommendations=total_recommendations,
        total_outcomes=total_outcomes,
        adherence_pct=adherence_pct,
        agreement_acceptance_pct=agreement_acceptance_pct,
        judge_disagreement_pct=judge_disagreement_pct,
        has_enough_data=total_outcomes > 0 or total_recommendations > 0,
    )
