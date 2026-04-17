from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CaseRead(BaseModel):
    id: str
    numero_processo: str | None = None
    valor_causa: Decimal | None = None
    autor_nome: str | None = None
    autor_cpf: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)
