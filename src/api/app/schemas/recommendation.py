from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class RecommendationRead(BaseModel):
    id: str
    case_id: str
    decisao: str
    valor_sugerido_min: Decimal | None = None
    valor_sugerido_max: Decimal | None = None
    justificativa: str | None = None
    confianca: float
    policy_version: str
    regras_aplicadas: list[str] = []
    casos_similares_ids: list[str] = []
    policy_trace: dict[str, Any] | None = None
    judge_concorda: bool | None = None
    judge_observacao: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
