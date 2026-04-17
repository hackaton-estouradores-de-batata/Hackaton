from pydantic import BaseModel


class DashboardMetricsRead(BaseModel):
    total_cases: int
    total_recommendations: int
    total_outcomes: int
    adherence_pct: float
    agreement_acceptance_pct: float
    judge_disagreement_pct: float
    has_enough_data: bool
