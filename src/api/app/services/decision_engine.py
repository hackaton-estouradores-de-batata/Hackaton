from decimal import Decimal
from typing import Any

from app.services.value_estimator import suggest_value_range


def score_robustez_subsidios(subsidios: dict[str, Any], policy: dict[str, Any]) -> float:
    weights = policy.get("robustez", {}).get("pesos", {})
    total_weight = sum(weights.values()) or 1
    score = 0.0

    for key, weight in weights.items():
        if subsidios.get(key):
            score += float(weight)

    return round(score / float(total_weight), 2)


def adjust_score(base_score: float, case_data: dict[str, Any], policy: dict[str, Any]) -> float:
    adjusted = base_score
    features_policy = policy.get("features", {})

    if case_data.get("vulnerabilidade_autor") and case_data.get("vulnerabilidade_autor") != "nenhuma":
        adjusted -= float(features_policy.get("penalidade_vulnerabilidade", 0.08))

    adjusted -= float(case_data.get("indicio_fraude", 0)) * float(
        features_policy.get("penalidade_indicio_fraude", 0.2)
    )
    adjusted -= len(case_data.get("red_flags", [])) * float(
        features_policy.get("penalidade_por_red_flag", 0.04)
    )
    adjusted -= float(case_data.get("forca_narrativa_autor", 0)) * float(
        features_policy.get("penalidade_narrativa", 0.12)
    )

    return round(max(0.0, min(1.0, adjusted)), 2)


def _derive_decision(adjusted_score: float, case_data: dict[str, Any], policy: dict[str, Any]) -> tuple[str, list[str]]:
    thresholds = policy.get("robustez", {}).get("thresholds", {})
    defesa_threshold = float(thresholds.get("defesa", 0.72))
    acordo_threshold = float(thresholds.get("acordo", 0.45))

    rules: list[str] = []
    if adjusted_score >= defesa_threshold:
        rules.append("DF-BASE: robustez documental alta")
        return "defesa", rules

    if adjusted_score <= acordo_threshold:
        rules.append("AP-BASE: robustez documental baixa")
        return "acordo", rules

    if case_data.get("vulnerabilidade_autor") and case_data.get("vulnerabilidade_autor") != "nenhuma":
        rules.append("AP-VULN: vulnerabilidade do autor")
        return "acordo", rules

    if len(case_data.get("red_flags", [])) >= 2:
        rules.append("AP-FLAGS: múltiplos red flags")
        return "acordo", rules

    rules.append("DF-INTERMEDIARIA: risco controlado")
    return "defesa", rules


def _build_justification(case_data: dict[str, Any], adjusted_score: float, decisao: str, regras: list[str]) -> str:
    if decisao == "acordo":
        return (
            f"Recomendação de acordo baseada em robustez ajustada {adjusted_score:.2f}, "
            f"red flags {len(case_data.get('red_flags', []))} e vulnerabilidade "
            f"{case_data.get('vulnerabilidade_autor') or 'não identificada'}."
        )

    return (
        f"Recomendação de defesa baseada em robustez ajustada {adjusted_score:.2f}, "
        f"subsídios suficientes e regras aplicadas: {', '.join(regras)}."
    )


def build_recommendation_payload(case_data: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    robustez = score_robustez_subsidios(case_data.get("subsidios") or {}, policy)
    ajustado = adjust_score(robustez, case_data, policy)
    decisao, regras = _derive_decision(ajustado, case_data, policy)
    recommendation_context = dict(case_data)
    recommendation_context["decisao"] = decisao
    valor_min, valor_max = suggest_value_range(recommendation_context, policy)

    return {
        "decisao": decisao,
        "valor_sugerido_min": valor_min,
        "valor_sugerido_max": valor_max,
        "justificativa": _build_justification(case_data, ajustado, decisao, regras),
        "confianca": round(max(0.35, min(0.95, ajustado if decisao == "defesa" else 1 - ajustado)), 2),
        "policy_version": str(policy.get("version", "v1")),
        "regras_aplicadas": regras,
        "casos_similares_ids": [],
        "judge_concorda": True,
        "judge_observacao": None,
    }
