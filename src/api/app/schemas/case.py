from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class CaseIngestResponse(BaseModel):
    id: str
    status: str
    source_folder: str | None = None
    autos_count: int
    subsidios_count: int


class CaseRead(BaseModel):
    id: str
    numero_processo: str | None = None
    valor_causa: Decimal | None = None
    autor_nome: str | None = None
    autor_cpf: str | None = None
    data_distribuicao: date | None = None
    alegacoes: list[str] = []
    pedidos: list[str] = []
    valor_pedido_danos_morais: Decimal | None = None
    red_flags: list[str] = []
    vulnerabilidade_autor: str | None = None
    indicio_fraude: float = 0.0
    forca_narrativa_autor: float = 0.0
    inconsistencias_temporais: list[str] = []
    subsidios: dict[str, Any] | None = None
    status: str
    source_folder: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
