from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.agreement_policy_v5 import (
    PolicyCaseInputV5,
    PolicyResultV5,
    build_policy_case_input,
    build_policy_trace,
    calculate_policy_v5,
    documentos_presentes,
)

CENTS = Decimal("0.01")


def _clamp_confidence(value: Decimal) -> float:
    return round(max(0.35, min(0.95, float(value))), 2)


def _serialize_trace_decimal(value: Decimal) -> float:
    return float(value.quantize(CENTS))


def _applied_rules(result: PolicyResultV5) -> list[str]:
    return [
        f"V5-MATRIZ:{result.matriz_escolhida}",
        f"V5-SUB:{result.sub}",
        f"V5-QTD_DOCS:{result.qtd_docs}",
        f"V5-DECISAO:{result.decisao}",
    ]


def _missing_ped_trace(case: PolicyCaseInputV5) -> dict[str, Any]:
    return {
        "mode": "v5",
        "matriz_escolhida": "MATRIZ_GERAL_6D",
        "sub_estatistico": case.sub,
        "qtd_docs": len(documentos_presentes(case)),
        "documentos_presentes": documentos_presentes(case),
        "p_suc": 0.0,
        "p_per": 0.0,
        "vej": 0.0,
        "abertura": 0.0,
        "alvo": 0.0,
        "teto": 0.0,
        "teto_pct": 0.0,
        "revisao_humana": True,
        "uf_sem_historico_proprio": case.uf != "TOTAL"
        and case.uf not in {"AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RS", "SC", "SE", "SP", "TO"},
    }


def build_recommendation_payload(
    case_data: dict[str, Any],
    policy: dict[str, Any] | None = None,
    *,
    history_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del policy, history_summary

    case = build_policy_case_input(case_data)
    if case.ped <= 0:
        return {
            "decisao": "defesa",
            "valor_sugerido_min": None,
            "valor_sugerido_max": None,
            "justificativa": "Revisao manual necessaria: o pedido base do caso nao foi identificado.",
            "confianca": 0.35,
            "policy_version": "v5",
            "regras_aplicadas": ["V5-MISSING-PED"],
            "casos_similares_ids": [],
            "judge_concorda": True,
            "judge_observacao": None,
            "policy_trace": _missing_ped_trace(case),
        }

    result = calculate_policy_v5(case)
    decisao = result.decisao.lower()
    confidence = _clamp_confidence(result.p_suc if decisao == "defesa" else result.p_per)
    policy_trace = build_policy_trace(result, case)

    return {
        "decisao": decisao,
        "valor_sugerido_min": result.abertura if decisao == "acordo" else None,
        "valor_sugerido_max": result.teto if decisao == "acordo" else None,
        "justificativa": result.justificativa_curta,
        "confianca": confidence,
        "policy_version": "v5",
        "regras_aplicadas": _applied_rules(result),
        "casos_similares_ids": [],
        "judge_concorda": True,
        "judge_observacao": None,
        "policy_trace": {
            **policy_trace,
            "vej": _serialize_trace_decimal(result.vej),
            "abertura": _serialize_trace_decimal(result.abertura),
            "alvo": _serialize_trace_decimal(result.alvo),
            "teto": _serialize_trace_decimal(result.teto),
        },
    }
