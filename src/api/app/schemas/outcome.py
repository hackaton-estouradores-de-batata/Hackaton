from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OutcomeCreate(BaseModel):
    decisao_advogado: str
    valor_proposto: Decimal | None = None
    valor_acordado: Decimal | None = None
    resultado_negociacao: str | None = None
    sentenca: str | None = None
    valor_condenacao: Decimal | None = None
    custos_processuais: Decimal | None = None


class OutcomeRead(BaseModel):
    id: str
    case_id: str
    recommendation_id: str | None = None
    decisao_advogado: str
    seguiu_recomendacao: bool
    valor_proposto: Decimal | None = None
    valor_acordado: Decimal | None = None
    resultado_negociacao: str | None = None
    sentenca: str | None = None
    valor_condenacao: Decimal | None = None
    custos_processuais: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
