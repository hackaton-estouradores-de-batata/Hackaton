from decimal import Decimal

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

    model_config = ConfigDict(from_attributes=True)
