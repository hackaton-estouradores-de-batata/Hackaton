from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.analytics.historical import summarize_case_history
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.services.decision_engine import build_recommendation_payload
from app.services.judge import review_recommendation_with_judge
from app.services.justifier import generate_recommendation_justification
from app.services.policy import load_policy

TERMINAL_CASE_STATUSES = {"decided", "closed"}


def case_snapshot(case: Case) -> dict[str, object]:
    return {
        "numero_processo": case.numero_processo,
        "valor_causa": case.valor_causa,
        "valor_pedido_danos_morais": case.valor_pedido_danos_morais,
        "uf": case.uf,
        "assunto": case.assunto,
        "sub_assunto": case.sub_assunto,
        "alegacoes": case.alegacoes,
        "pedidos": case.pedidos,
        "case_text": case.case_text,
        "red_flags": case.red_flags,
        "vulnerabilidade_autor": case.vulnerabilidade_autor,
        "indicio_fraude": case.indicio_fraude,
        "forca_narrativa_autor": case.forca_narrativa_autor,
        "subsidios": case.subsidios,
    }


def _decorate_policy_version(base_version: str, history_summary: dict[str, object]) -> str:
    if history_summary.get("casos_similares_ids") and not base_version.endswith("-hist"):
        return f"{base_version}-hist"
    return base_version


def _apply_history_traceability(
    payload: dict[str, object],
    history_summary: dict[str, object],
) -> dict[str, object]:
    updated = dict(payload)
    updated["casos_similares_ids"] = list(history_summary.get("casos_similares_ids") or [])
    updated["regras_aplicadas"] = list(updated.get("regras_aplicadas") or [])
    if updated["casos_similares_ids"] and "HIST-01: resumo histórico inicial" not in updated["regras_aplicadas"]:
        updated["regras_aplicadas"].append("HIST-01: resumo histórico inicial")
    updated["policy_version"] = _decorate_policy_version(str(updated.get("policy_version", "v1")), history_summary)
    return updated


def _decimal_str(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _needs_llm_refresh(recommendation: Recommendation | None, payload: dict[str, object]) -> bool:
    if recommendation is None:
        return True
    if recommendation.justificativa is None or recommendation.judge_concorda is None:
        return True
    if "Contexto historico:" in recommendation.justificativa:
        return True

    current_ids = list(recommendation.casos_similares_ids or [])
    expected_ids = list(payload.get("casos_similares_ids") or [])
    if recommendation.decisao != payload.get("decisao"):
        return True
    if _decimal_str(recommendation.valor_sugerido_min) != _decimal_str(payload.get("valor_sugerido_min")):
        return True
    if _decimal_str(recommendation.valor_sugerido_max) != _decimal_str(payload.get("valor_sugerido_max")):
        return True
    if current_ids != expected_ids:
        return True
    if recommendation.policy_version != payload.get("policy_version"):
        return True
    return False


def _apply_judge_and_justification(
    case_data: dict[str, object],
    payload: dict[str, object],
    history_summary: dict[str, object],
) -> dict[str, object]:
    updated = dict(payload)
    judge_result = review_recommendation_with_judge(case_data, updated, history_summary)
    updated["judge_concorda"] = judge_result["concorda"]
    updated["judge_observacao"] = judge_result["observacao"]
    updated["confianca"] = judge_result["confianca_calibrada"]
    updated["regras_aplicadas"] = list(updated.get("regras_aplicadas") or [])

    if judge_result["concorda"] is False:
        judge_rule = "JUDGE-01: revisão humana sugerida"
        if judge_rule not in updated["regras_aplicadas"]:
            updated["regras_aplicadas"].append(judge_rule)

    updated["justificativa"] = generate_recommendation_justification(
        case_data,
        updated,
        history_summary,
        judge_result,
    )
    return updated


def _reuse_existing_llm_fields(
    recommendation: Recommendation,
    payload: dict[str, object],
) -> dict[str, object]:
    updated = dict(payload)
    updated["justificativa"] = recommendation.justificativa
    updated["judge_concorda"] = recommendation.judge_concorda
    updated["judge_observacao"] = recommendation.judge_observacao
    updated["confianca"] = recommendation.confianca
    return updated


def build_recommendation_for_case(
    case: Case,
    *,
    existing_recommendation: Recommendation | None = None,
    history_k: int = 10,
    policy: dict[str, Any] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    current_policy = policy or load_policy()
    current_snapshot = case_snapshot(case)
    history_summary = summarize_case_history(case, k=history_k)
    payload = build_recommendation_payload(
        current_snapshot,
        current_policy,
        history_summary=history_summary,
    )
    payload = _apply_history_traceability(payload, history_summary)

    if _needs_llm_refresh(existing_recommendation, payload):
        payload = _apply_judge_and_justification(current_snapshot, payload, history_summary)
    elif existing_recommendation is not None:
        payload = _reuse_existing_llm_fields(existing_recommendation, payload)

    return payload, history_summary


def derive_case_status(current_status: str, recommendation_payload: dict[str, object]) -> str:
    if current_status in TERMINAL_CASE_STATUSES:
        return current_status
    if recommendation_payload.get("judge_concorda") is False:
        return "needs_review"
    return "analyzed"


def sync_case_status(case: Case, recommendation_payload: dict[str, object]) -> str:
    case.status = derive_case_status(case.status, recommendation_payload)
    return case.status


def apply_recommendation_payload(
    recommendation: Recommendation,
    payload: dict[str, object],
) -> Recommendation:
    for key, value in payload.items():
        setattr(recommendation, key, value)
    return recommendation
