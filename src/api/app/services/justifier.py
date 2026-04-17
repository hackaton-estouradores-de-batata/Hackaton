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


def _history_reference(history_summary: dict[str, Any] | None, limit: int = 3) -> str | None:
    case_ids = list((history_summary or {}).get("casos_similares_ids") or [])[:limit]
    if not case_ids:
        return None
    return ", ".join(case_ids)


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
    decisao = str(recommendation_payload.get("decisao") or "").upper()
    valor_min = _format_currency(recommendation_payload.get("valor_sugerido_min"))
    valor_max = _format_currency(recommendation_payload.get("valor_sugerido_max"))
    red_flags = list(case_data.get("red_flags") or [])
    vulnerabilidade = str(case_data.get("vulnerabilidade_autor") or "").strip() or "não identificada"
    stats = dict((history_summary or {}).get("stats") or {})
    prob_vitoria = float(stats.get("prob_vitoria", 0.0) or 0.0)
    similar_cases = _history_reference(history_summary)

    parts: list[str] = []
    if decisao == "ACORDO" and valor_min and valor_max:
        parts.append(f"Recomenda-se ACORDO na faixa de {valor_min} a {valor_max}.")
    else:
        parts.append("Recomenda-se DEFESA com base no motor estatístico e na política vigente.")

    if similar_cases:
        p25 = _format_currency(stats.get("percentil_25")) or "R$ 0,00"
        p50 = _format_currency(stats.get("percentil_50")) or "R$ 0,00"
        parts.append(
            f"Foram usados como referência os casos similares {similar_cases}, com probabilidade histórica "
            f"de êxito do autor em {prob_vitoria:.0%}, p25 em {p25} e p50 em {p50}."
        )

    if red_flags:
        parts.append(f"Os principais fatores de risco foram: {', '.join(red_flags[:3])}.")
    parts.append(f"A vulnerabilidade do autor foi classificada como {vulnerabilidade}.")

    if judge_result and judge_result.get("concorda") is False and judge_result.get("observacao"):
        parts.append(f"Revisão humana sugerida pelo judge: {judge_result['observacao']}")

    return " ".join(parts)


def generate_recommendation_justification(
    case_data: dict[str, Any],
    recommendation_payload: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
    judge_result: dict[str, Any] | None = None,
    *,
    allow_llm: bool = True,
) -> str:
    if allow_llm:
        settings = get_settings()
        llm_payload = chat_json_prompt(
            settings.justify_model,
            "justify.txt",
            json.dumps(
                {
                    "case_data": case_data,
                    "recommendation": recommendation_payload,
                    "history_summary": {
                        "stats": dict((history_summary or {}).get("stats") or {}),
                        "casos_similares_ids": list(
                            (history_summary or {}).get("casos_similares_ids") or []
                        )[:5],
                        "total_casos_similares": int(
                            (history_summary or {}).get("total_casos_similares", 0) or 0
                        ),
                    },
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

    return _fallback_justification(case_data, recommendation_payload, history_summary, judge_result)
