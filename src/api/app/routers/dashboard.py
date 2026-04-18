from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.case import Case
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.schemas.dashboard import (
    DashboardAnalyticsRead,
    DashboardMetricsRead,
    MatrixCell,
    ParetoItem,
    ResultadoMicroItem,
    ValorPedidoVsPagoRead,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# sentenca values that represent "Não Êxito" for the bank
_NAO_EXITO = {"procedente", "parcial"}
_EXITO = {"improcedente"}


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


@router.get("/analytics", response_model=DashboardAnalyticsRead)
def get_dashboard_analytics(
    uf: Optional[str] = None,
    sub_assunto: Optional[str] = None,
    db: Session = Depends(get_db),
) -> DashboardAnalyticsRead:
    _empty_vp = ValorPedidoVsPagoRead(total_pedido=0, total_pago=0, percentual_pago=0, count=0)
    _empty_macro = {"exito_pct": 0.0, "nao_exito_pct": 0.0, "total": 0.0}

    try:
        case_q = db.query(Case)
        if uf:
            case_q = case_q.filter(Case.uf == uf)
        if sub_assunto:
            case_q = case_q.filter(Case.sub_assunto == sub_assunto)
        cases = case_q.all()
        case_ids = [c.id for c in cases]

        if case_ids:
            outcomes = db.query(Outcome).filter(Outcome.case_id.in_(case_ids)).all()
            recommendations = db.query(Recommendation).filter(Recommendation.case_id.in_(case_ids)).all()
        else:
            outcomes = []
            recommendations = []

        case_by_id = {c.id: c for c in cases}
        outcome_by_case: dict[str, Outcome] = {}
        for o in outcomes:
            outcome_by_case.setdefault(o.case_id, o)

        # ── Pareto ──────────────────────────────────────────────────────────
        pareto_map: dict[str, dict] = {}
        for c in cases:
            sa = c.sub_assunto or "Não informado"
            val = float(c.valor_pedido_danos_morais or c.valor_causa or 0)
            bucket = pareto_map.setdefault(sa, {"total": 0.0, "count": 0})
            bucket["total"] += val
            bucket["count"] += 1
        pareto = sorted(
            [
                ParetoItem(sub_assunto=k, total_valor_pedido=v["total"], count=v["count"])
                for k, v in pareto_map.items()
            ],
            key=lambda x: x.total_valor_pedido,
            reverse=True,
        )[:10]

        # ── Valor Pedido vs Pago ─────────────────────────────────────────────
        total_pedido = total_pago = 0.0
        vp_count = 0
        for o in outcomes:
            c = case_by_id.get(o.case_id)
            if not c:
                continue
            pedido = float(c.valor_pedido_danos_morais or c.valor_causa or 0)
            pago = float(o.valor_acordado or o.valor_condenacao or 0)
            if pedido > 0:
                total_pedido += pedido
                total_pago += pago
                vp_count += 1
        valor_vp = ValorPedidoVsPagoRead(
            total_pedido=total_pedido,
            total_pago=total_pago,
            percentual_pago=(total_pago / total_pedido * 100) if total_pedido else 0.0,
            count=vp_count,
        )

        # ── KPI Economia (não êxito + defesa) ───────────────────────────────
        eco_sum = eco_n = 0
        for o in outcomes:
            if o.decisao_advogado != "defesa" or o.sentenca not in _NAO_EXITO:
                continue
            c = case_by_id.get(o.case_id)
            if not c:
                continue
            pedido = float(c.valor_pedido_danos_morais or c.valor_causa or 0)
            if pedido <= 0:
                continue
            condenacao = float(o.valor_condenacao or 0)
            eco_sum += (pedido - condenacao) / pedido * 100
            eco_n += 1
        kpi_economia = eco_sum / eco_n if eco_n else 0.0

        # ── Resultado Macro ──────────────────────────────────────────────────
        com_sentenca = [o for o in outcomes if o.sentenca]
        exito_n = sum(1 for o in com_sentenca if o.sentenca in _EXITO)
        nao_exito_n = sum(1 for o in com_sentenca if o.sentenca in _NAO_EXITO)
        total_macro = len(com_sentenca)
        resultado_macro = {
            "exito_pct": exito_n / total_macro * 100 if total_macro else 0.0,
            "nao_exito_pct": nao_exito_n / total_macro * 100 if total_macro else 0.0,
            "total": float(total_macro),
        }

        # ── Resultado Micro ──────────────────────────────────────────────────
        micro_counts: dict[str, int] = {}
        for o in outcomes:
            if o.sentenca:
                micro_counts[o.sentenca] = micro_counts.get(o.sentenca, 0) + 1
        total_micro = sum(micro_counts.values())
        resultado_micro = [
            ResultadoMicroItem(
                resultado_micro=k,
                count=v,
                pct=v / total_micro * 100 if total_micro else 0.0,
            )
            for k, v in sorted(micro_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # ── Matrix qtd_docs × UF ────────────────────────────────────────────
        matrix_map: dict[tuple[int, str], dict] = {}
        for r in recommendations:
            c = case_by_id.get(r.case_id)
            if not c or not c.uf:
                continue
            qtd_docs = int((r.policy_trace or {}).get("qtd_docs", 0))
            key = (qtd_docs, c.uf)
            cell = matrix_map.setdefault(key, {"success": 0, "total": 0})
            o = outcome_by_case.get(r.case_id)
            if o:
                cell["total"] += 1
                if o.sentenca in _EXITO:
                    cell["success"] += 1
        matrix = [
            MatrixCell(
                uf=uf_val,
                qtd_docs=qtd,
                taxa_sucesso=v["success"] / v["total"] * 100 if v["total"] else 0.0,
                count=v["total"],
            )
            for (qtd, uf_val), v in sorted(matrix_map.items())
        ]

        # ── Filter options (unfiltered) ──────────────────────────────────────
        all_cases = db.query(Case).all()
        ufs_disponiveis = sorted({c.uf for c in all_cases if c.uf})
        sub_assuntos_disponiveis = sorted({c.sub_assunto for c in all_cases if c.sub_assunto})

        return DashboardAnalyticsRead(
            pareto=pareto,
            valor_pedido_vs_pago=valor_vp,
            kpi_economia_nao_exito_defesa=kpi_economia,
            resultado_macro=resultado_macro,
            resultado_micro=resultado_micro,
            matrix=matrix,
            ufs_disponiveis=ufs_disponiveis,
            sub_assuntos_disponiveis=sub_assuntos_disponiveis,
        )

    except OperationalError:
        return DashboardAnalyticsRead(
            pareto=[],
            valor_pedido_vs_pago=_empty_vp,
            kpi_economia_nao_exito_defesa=0.0,
            resultado_macro=_empty_macro,
            resultado_micro=[],
            matrix=[],
            ufs_disponiveis=[],
            sub_assuntos_disponiveis=[],
        )
