from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.llm.client import chat_json_prompt


def _history_excerpt(history_summary: dict[str, Any] | None, limit: int = 5) -> list[dict[str, Any]]:
    history_cases = list((history_summary or {}).get("casos_similares") or [])
    excerpt: list[dict[str, Any]] = []

    for item in history_cases[:limit]:
        excerpt.append(
            {
                "case_id": item.get("case_id"),
                "similarity_score": item.get("similarity_score"),
                "resultado_macro": item.get("resultado_macro"),
                "resultado_micro": item.get("resultado_micro"),
                "valor_causa": item.get("valor_causa"),
                "valor_condenacao": item.get("valor_condenacao"),
            }
        )

    return excerpt


def _clamp_confidence(value: Any, default: float) -> float:
    try:
        confidence = float(value)
    except Exception:
        confidence = default
    return round(max(0.20, min(0.98, confidence)), 2)


def _normalize_judge_response(payload: dict[str, Any], default_confidence: float) -> dict[str, Any]:
    observacao = payload.get("observacao")
    observacao_text = str(observacao).strip() if observacao else None
    concorda = bool(payload.get("concorda", True))

    if not concorda and not observacao_text:
        observacao_text = "Judge sugeriu revisão humana por inconsistência material na recomendação."

    return {
        "concorda": concorda,
        "observacao": observacao_text,
        "confianca_calibrada": _clamp_confidence(
            payload.get("confianca_calibrada", payload.get("confianca")),
            default_confidence,
        ),
    }


def _fallback_judge(
    case_data: dict[str, Any],
    recommendation_payload: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    red_flags = list(case_data.get("red_flags") or [])
    vulnerabilidade = str(case_data.get("vulnerabilidade_autor") or "").strip()
    vulnerable = bool(vulnerabilidade and vulnerabilidade != "nenhuma")
    indicio_fraude = float(case_data.get("indicio_fraude", 0.0) or 0.0)
    decisao = str(recommendation_payload.get("decisao") or "")
    default_confidence = float(recommendation_payload.get("confianca", 0.5) or 0.5)

    stats = dict((history_summary or {}).get("stats") or {})
    prob_vitoria = float(stats.get("prob_vitoria", 0.0) or 0.0)
    total = int((history_summary or {}).get("total_casos_similares", 0) or 0)

    reasons: list[str] = []
    if decisao == "defesa":
        if vulnerable:
            reasons.append("há vulnerabilidade relevante do autor")
        if len(red_flags) >= 2:
            reasons.append("existem múltiplos red flags")
        if prob_vitoria >= 0.55:
            reasons.append("o histórico semelhante é desfavorável à defesa")
    elif decisao == "acordo":
        if recommendation_payload.get("valor_sugerido_max") is None:
            reasons.append("a faixa de acordo não foi definida")
        if indicio_fraude >= 0.70 and prob_vitoria <= 0.15 and not vulnerable:
            reasons.append("os sinais favorecem defesa mais robusta")

    calibrated_confidence = default_confidence
    if total == 0:
        calibrated_confidence -= 0.10
    elif total >= 5:
        calibrated_confidence += 0.05

    concorda = not reasons
    if not concorda:
        calibrated_confidence = min(calibrated_confidence, 0.55)

    return {
        "concorda": concorda,
        "observacao": (
            "Judge heurístico sugere revisão humana: " + "; ".join(reasons) + "."
            if reasons
            else None
        ),
        "confianca_calibrada": _clamp_confidence(calibrated_confidence, default_confidence),
    }


def review_recommendation_with_judge(
    case_data: dict[str, Any],
    recommendation_payload: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
    *,
    allow_llm: bool = True,
) -> dict[str, Any]:
    default_confidence = float(recommendation_payload.get("confianca", 0.5) or 0.5)

    if allow_llm:
        settings = get_settings()
        llm_payload = chat_json_prompt(
            settings.judge_model,
            "judge.txt",
            json.dumps(
                {
                    "case_data": case_data,
                    "recommendation": recommendation_payload,
                    "history_summary": {
                        "stats": dict((history_summary or {}).get("stats") or {}),
                        "total_casos_similares": int(
                            (history_summary or {}).get("total_casos_similares", 0) or 0
                        ),
                        "casos_similares": _history_excerpt(history_summary, limit=5),
                    },
                },
                ensure_ascii=False,
                default=str,
            ),
        )
        if llm_payload:
            return _normalize_judge_response(llm_payload, default_confidence)

    return _fallback_judge(case_data, recommendation_payload, history_summary)
