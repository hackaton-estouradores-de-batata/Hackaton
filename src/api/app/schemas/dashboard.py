from pydantic import BaseModel


class DashboardMetricsRead(BaseModel):
    total_cases: int
    total_recommendations: int
    total_outcomes: int
    adherence_pct: float
    agreement_acceptance_pct: float
    judge_disagreement_pct: float
    has_enough_data: bool


class ParetoItem(BaseModel):
    sub_assunto: str
    total_valor_pedido: float
    count: int


class ResultadoMicroItem(BaseModel):
    resultado_micro: str
    count: int
    pct: float


class MatrixCell(BaseModel):
    uf: str
    qtd_docs: int
    taxa_sucesso: float
    count: int


class ValorPedidoVsPagoRead(BaseModel):
    total_pedido: float
    total_pago: float
    percentual_pago: float
    count: int


class DashboardAnalyticsRead(BaseModel):
    pareto: list[ParetoItem]
    valor_pedido_vs_pago: ValorPedidoVsPagoRead
    kpi_economia_nao_exito_defesa: float
    resultado_macro: dict[str, float]
    resultado_micro: list[ResultadoMicroItem]
    matrix: list[MatrixCell]
    ufs_disponiveis: list[str]
    sub_assuntos_disponiveis: list[str]
