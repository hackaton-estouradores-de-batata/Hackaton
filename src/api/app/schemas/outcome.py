from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OutcomeRead(BaseModel):
    id: str
    case_id: str
    recommendation_id: str | None = None
    decisao_advogado: str
    seguiu_recomendacao: bool
    valor_proposto: Decimal | None = None
    valor_acordado: Decimal | None = None
    resultado_negociacao: str | None = None
    valor_condenacao: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
