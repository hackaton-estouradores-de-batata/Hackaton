from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from app.models.case import Case
from app.models.recommendation import Recommendation
from app.services.case_normalization import normalize_case_snapshot
from app.services.decision_engine import build_recommendation_payload
from app.services.judge import review_recommendation_with_judge
from app.services.justifier import generate_recommendation_justification

TERMINAL_CASE_STATUSES = {"decided", "closed"}


def case_snapshot(case: Case) -> dict[str, object]:
    snapshot = {
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
    return normalize_case_snapshot(snapshot)


def _json_signature(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def snapshot_signature(snapshot: dict[str, object]) -> str:
    payload = _json_signature(snapshot).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _decimal_str(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _recommendation_payload_from_record(recommendation: Recommendation) -> dict[str, object]:
    return {
        "decisao": recommendation.decisao,
        "valor_sugerido_min": recommendation.valor_sugerido_min,
        "valor_sugerido_max": recommendation.valor_sugerido_max,
        "justificativa": recommendation.justificativa,
        "confianca": recommendation.confianca,
        "policy_version": recommendation.policy_version,
        "regras_aplicadas": list(recommendation.regras_aplicadas or []),
        "casos_similares_ids": list(recommendation.casos_similares_ids or []),
        "policy_trace": dict(recommendation.policy_trace or {}),
        "judge_concorda": recommendation.judge_concorda,
        "judge_observacao": recommendation.judge_observacao,
        "source_snapshot_signature": recommendation.source_snapshot_signature,
    }


def _needs_llm_refresh(recommendation: Recommendation | None, payload: dict[str, object]) -> bool:
    if recommendation is None:
        return True
    if recommendation.justificativa is None or recommendation.judge_concorda is None:
        return True
    if recommendation.decisao != payload.get("decisao"):
        return True
    if _decimal_str(recommendation.valor_sugerido_min) != _decimal_str(payload.get("valor_sugerido_min")):
        return True
    if _decimal_str(recommendation.valor_sugerido_max) != _decimal_str(payload.get("valor_sugerido_max")):
        return True
    if recommendation.policy_version != payload.get("policy_version"):
        return True
    if list(recommendation.regras_aplicadas or []) != list(payload.get("regras_aplicadas") or []):
        return True
    if list(recommendation.casos_similares_ids or []) != list(payload.get("casos_similares_ids") or []):
        return True
    if _json_signature(recommendation.policy_trace) != _json_signature(payload.get("policy_trace")):
        return True
    return False


def _apply_judge_and_justification(
    case_data: dict[str, object],
    payload: dict[str, object],
) -> dict[str, object]:
    updated = dict(payload)
    judge_result = review_recommendation_with_judge(case_data, updated)
    updated["judge_concorda"] = judge_result["concorda"]
    updated["judge_observacao"] = judge_result["observacao"]
    updated["confianca"] = judge_result["confianca_calibrada"]
    updated["regras_aplicadas"] = list(updated.get("regras_aplicadas") or [])

    if judge_result["concorda"] is False:
        judge_rule = "JUDGE-01: revisao humana sugerida"
        if judge_rule not in updated["regras_aplicadas"]:
            updated["regras_aplicadas"].append(judge_rule)

    updated["justificativa"] = generate_recommendation_justification(
        case_data,
        updated,
        judge_result=judge_result,
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
    del history_k, policy

    current_snapshot = case_snapshot(case)
    current_signature = snapshot_signature(current_snapshot)

    if (
        existing_recommendation is not None
        and existing_recommendation.source_snapshot_signature == current_signature
    ):
        existing_payload = _recommendation_payload_from_record(existing_recommendation)
        if not _needs_llm_refresh(existing_recommendation, existing_payload):
            return existing_payload, {"snapshot_signature": current_signature, "reused": True}

    payload = build_recommendation_payload(current_snapshot)
    payload["source_snapshot_signature"] = current_signature

    if _needs_llm_refresh(existing_recommendation, payload):
        payload = _apply_judge_and_justification(current_snapshot, payload)
    elif existing_recommendation is not None:
        payload = _reuse_existing_llm_fields(existing_recommendation, payload)

    payload["source_snapshot_signature"] = current_signature
    return payload, {"snapshot_signature": current_signature, "reused": False}


def derive_case_status(current_status: str, recommendation_payload: dict[str, object]) -> str:
    if current_status in TERMINAL_CASE_STATUSES:
        return current_status
    policy_trace = dict(recommendation_payload.get("policy_trace") or {})
    if recommendation_payload.get("judge_concorda") is False or bool(policy_trace.get("revisao_humana")):
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
