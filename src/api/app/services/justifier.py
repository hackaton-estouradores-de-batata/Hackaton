from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.llm.client import chat_json_prompt


def _format_currency(value: Any) -> str | None:
    if value in (None, "", "None"):
        return None
    try:
        normalized = float(value)
    except Exception:
        return str(value)
    return f"R$ {normalized:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _format_percent(value: Any) -> str | None:
    if value in (None, "", "None"):
        return None
    try:
        numeric = float(value)
    except Exception:
        return None
    return f"{round(numeric * 100):.0f}%"


def _normalize_justification(payload: dict[str, Any]) -> str | None:
    text = payload.get("justificativa")
    if text is None:
        return None
    normalized = " ".join(str(text).split())
    return normalized or None


def _fallback_justification(
    case_data: dict[str, Any],
    recommendation_payload: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
    judge_result: dict[str, Any] | None = None,
) -> str:
    del case_data, history_summary

    trace = dict(recommendation_payload.get("policy_trace") or {})
    decisao = str(recommendation_payload.get("decisao") or "").upper()
    valor_min = _format_currency(recommendation_payload.get("valor_sugerido_min"))
    valor_max = _format_currency(recommendation_payload.get("valor_sugerido_max"))
    vej = _format_currency(trace.get("vej"))
    alvo = _format_currency(trace.get("alvo"))
    p_suc = _format_percent(trace.get("p_suc"))
    matriz = trace.get("matriz_escolhida")
    qtd_docs = trace.get("qtd_docs")
    documentos = list(trace.get("documentos_presentes") or [])

    parts: list[str] = []
    if decisao == "ACORDO" and valor_min and valor_max:
        parts.append(
            f"Recomenda-se ACORDO na faixa de {valor_min} a {valor_max}, com alvo tecnico em {alvo or valor_min} e VEJ estimado em {vej or 'R$ 0,00'}."
        )
    else:
        parts.append(
            f"Recomenda-se DEFESA pela politica V5, porque o teto racional calculado ficou abaixo do piso comercial do caso."
        )

    if matriz and qtd_docs is not None:
        parts.append(
            f"A matriz aplicada foi {matriz}, com {qtd_docs} documento(s) valido(s) e probabilidade estimada de exito defensivo em {p_suc or '0%'}."
        )

    if documentos:
        parts.append(f"Os documentos considerados foram: {', '.join(documentos[:6])}.")

    if judge_result and judge_result.get("concorda") is False and judge_result.get("observacao"):
        parts.append(f"Revisao humana sugerida pelo judge: {judge_result['observacao']}")

    return " ".join(parts)


def generate_recommendation_justification(
    case_data: dict[str, Any],
    recommendation_payload: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
    judge_result: dict[str, Any] | None = None,
    *,
    allow_llm: bool = True,
) -> str:
    del history_summary

    if allow_llm:
        settings = get_settings()
        llm_payload = chat_json_prompt(
            settings.justify_model,
            "justify.txt",
            json.dumps(
                {
                    "case_data": case_data,
                    "recommendation": recommendation_payload,
                    "judge_result": judge_result,
                },
                ensure_ascii=False,
                default=str,
            ),
        )
        if llm_payload:
            text = _normalize_justification(llm_payload)
            if text:
                return text

    return _fallback_justification(case_data, recommendation_payload, judge_result=judge_result)
