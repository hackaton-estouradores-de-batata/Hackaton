from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.llm.client import chat_json_prompt


def _clamp_confidence(value: Any, default: float, *, max_value: float = 0.98) -> float:
    try:
        confidence = float(value)
    except Exception:
        confidence = default
    return round(max(0.20, min(max_value, confidence)), 2)


def _review_reasons(recommendation_payload: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    policy_trace = dict(recommendation_payload.get("policy_trace") or {})
    decisao = str(recommendation_payload.get("decisao") or "")
    valor_min = recommendation_payload.get("valor_sugerido_min")
    valor_max = recommendation_payload.get("valor_sugerido_max")
    regras = {str(rule) for rule in recommendation_payload.get("regras_aplicadas") or []}

    if "V5-MISSING-PED" in regras:
        reasons.append("pedido_base_ausente")
    if bool(policy_trace.get("revisao_humana")):
        reasons.append("contradicao_documental")
    if not policy_trace or policy_trace.get("mode") != "v5":
        reasons.append("trace_v5_ausente")

    if decisao == "acordo":
        if valor_min is None or valor_max is None:
            reasons.append("faixa_acordo_ausente")
        elif valor_min > valor_max:
            reasons.append("faixa_acordo_invalida")

    if decisao == "defesa" and (valor_min is not None or valor_max is not None):
        reasons.append("faixa_incompativel_com_defesa")

    return reasons


def _reason_message(reason: str) -> str:
    messages = {
        "pedido_base_ausente": "o pedido base do caso nao foi identificado",
        "contradicao_documental": "ha contradicao documental objetiva nos subsidios",
        "trace_v5_ausente": "o trace da politica V5 nao foi gerado corretamente",
        "faixa_acordo_ausente": "a faixa de acordo nao foi gerada",
        "faixa_acordo_invalida": "a faixa de acordo esta inconsistente",
        "faixa_incompativel_com_defesa": "ha faixa financeira associada a uma decisao de defesa",
    }
    return messages.get(reason, reason.replace("_", " "))


def _fallback_review(reasons: list[str], default_confidence: float) -> dict[str, Any]:
    observation = "Judge sugere revisao humana: " + "; ".join(_reason_message(reason) for reason in reasons) + "."
    return {
        "concorda": False,
        "observacao": observation,
        "confianca_calibrada": _clamp_confidence(default_confidence, default_confidence, max_value=0.55),
    }


def _normalize_judge_response(
    payload: dict[str, Any],
    default_confidence: float,
    fallback_observation: str,
) -> dict[str, Any]:
    observacao = payload.get("observacao")
    observacao_text = str(observacao).strip() if observacao else fallback_observation

    return {
        "concorda": False,
        "observacao": observacao_text,
        "confianca_calibrada": _clamp_confidence(
            payload.get("confianca_calibrada", payload.get("confianca")),
            default_confidence,
            max_value=0.55,
        ),
    }


def review_recommendation_with_judge(
    case_data: dict[str, Any],
    recommendation_payload: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
    *,
    allow_llm: bool = True,
) -> dict[str, Any]:
    del case_data, history_summary

    default_confidence = float(recommendation_payload.get("confianca", 0.5) or 0.5)
    reasons = _review_reasons(recommendation_payload)
    if not reasons:
        return {
            "concorda": True,
            "observacao": None,
            "confianca_calibrada": _clamp_confidence(default_confidence, default_confidence),
        }

    fallback = _fallback_review(reasons, default_confidence)
    if not allow_llm:
        return fallback

    settings = get_settings()
    llm_payload = chat_json_prompt(
        settings.judge_model,
        "judge.txt",
        json.dumps(
            {
                "recommendation": recommendation_payload,
                "review_reasons": reasons,
            },
            ensure_ascii=False,
            default=str,
        ),
    )
    if not llm_payload:
        return fallback
    return _normalize_judge_response(llm_payload, default_confidence, fallback["observacao"])
