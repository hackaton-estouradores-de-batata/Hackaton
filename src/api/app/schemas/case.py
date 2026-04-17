from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CaseIngestResponse(BaseModel):
    id: str
    status: str
    source_folder: str | None = None
    autos_count: int
    subsidios_count: int
    uf: str | None = None
    assunto: str | None = None
    sub_assunto: str | None = None


class CaseRead(BaseModel):
    id: str
    numero_processo: str | None = None
    valor_causa: Decimal | None = None
    autor_nome: str | None = None
    autor_cpf: str | None = None
    uf: str | None = None
    assunto: str | None = None
    sub_assunto: str | None = None
    case_text: str | None = None
    status: str
    source_folder: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
