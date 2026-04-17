from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.value_estimator import build_value_context, suggest_value_range

CENTS = Decimal("0.01")


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _format_brl(value: Decimal | None) -> str:
    if value is None:
        return "R$ 0,00"
    normalized = value.quantize(CENTS)
    integer, _, decimal = f"{normalized:.2f}".partition(".")
    groups: list[str] = []
    remaining = integer
    while remaining:
        groups.append(remaining[-3:])
        remaining = remaining[:-3]
    return f"R$ {'.'.join(reversed(groups))},{decimal}"


def score_robustez_subsidios(subsidios: dict[str, Any], policy: dict[str, Any]) -> float:
    weights = policy.get("robustez", {}).get("pesos", {})
    total_weight = sum(weights.values()) or 1
    score = 0.0

    for key, weight in weights.items():
        if subsidios.get(key):
            score += float(weight)

    return round(score / float(total_weight), 2)


def _policy_snapshot(case_data: dict[str, Any]) -> dict[str, Any]:
    subsidios = dict(case_data.get("subsidios") or {})
    return {
        **subsidios,
        "tem_comprovante_credito": subsidios.get("tem_comprovante"),
        "assinatura_validada_dossie": subsidios.get("assinatura_validada"),
        "autor_idoso": case_data.get("vulnerabilidade_autor") == "idoso",
        "vulnerabilidade_autor": case_data.get("vulnerabilidade_autor"),
        "indicio_fraude": float(case_data.get("indicio_fraude", 0.0) or 0.0),
        "red_flags": list(case_data.get("red_flags") or []),
    }


def _condition_matches(snapshot: dict[str, Any], condition: dict[str, Any]) -> bool:
    if "OR" in condition:
        return any(_condition_matches(snapshot, item) for item in condition["OR"])

    key, expected = next(iter(condition.items()))
    return snapshot.get(key) == expected


def _rule_matches(snapshot: dict[str, Any], rule: dict[str, Any]) -> bool:
    return all(_condition_matches(snapshot, condition) for condition in rule.get("condicoes", []))


def _evaluate_policy_rules(
    case_data: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[str | None, list[str], float | None]:
    snapshot = _policy_snapshot(case_data)

    for section_name, default_action in (("defesa_forte", "defesa"), ("acordo_prioritario", "acordo")):
        for rule in policy.get(section_name, []):
            if not _rule_matches(snapshot, rule):
                continue

            confidence = rule.get("confianca")
            return (
                str(rule.get("acao", default_action)),
                [str(rule.get("id", default_action.upper()))],
                float(confidence) if confidence is not None else None,
            )

    return None, [], None


def adjust_score(base_score: float, case_data: dict[str, Any], policy: dict[str, Any]) -> float:
    adjusted = base_score
    features_policy = policy.get("features", {})

    if case_data.get("vulnerabilidade_autor") and case_data.get("vulnerabilidade_autor") != "nenhuma":
        adjusted -= float(features_policy.get("penalidade_vulnerabilidade", 0.10))

    indicio_fraude = float(case_data.get("indicio_fraude", 0.0) or 0.0)
    fraud_threshold = float(features_policy.get("limiar_indicio_fraude_alto", 0.70))
    if indicio_fraude >= fraud_threshold:
        adjusted += float(features_policy.get("bonus_indicio_fraude_alto", 0.15))
    else:
        adjusted -= indicio_fraude * float(features_policy.get("penalidade_indicio_fraude", 0.0))

    adjusted -= len(case_data.get("red_flags", [])) * float(
        features_policy.get("penalidade_por_red_flag", 0.04)
    )
    adjusted -= float(case_data.get("forca_narrativa_autor", 0.0) or 0.0) * float(
        features_policy.get("penalidade_narrativa", 0.12)
    )

    return round(max(0.0, min(1.0, adjusted)), 2)


def calcular_ev(
    case_data: dict[str, Any],
    policy: dict[str, Any],
    history_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stats = dict((history_summary or {}).get("stats") or {})
    prob_vitoria = float(stats.get("prob_vitoria", 0.0) or 0.0)
    prob_vitoria = max(0.0, min(1.0, prob_vitoria))

    ev_policy = policy.get("ev", {})
    custo_default = Decimal(str(ev_policy.get("custo_esperado_defesa_default", "2500")))
    custo_medio_defesa = _to_decimal(stats.get("custo_medio_defesa"), str(custo_default))
    custo_esperado_defesa = max(custo_default, custo_medio_defesa)

    conservative_value = build_value_context(
        case_data,
        policy,
        history_summary=history_summary,
        strategy="conservador",
    )
    ev_acordo = conservative_value["ev_acordo"]
    ev_defesa = (Decimal(str(prob_vitoria)) * custo_esperado_defesa).quantize(CENTS)

    return {
        "prob_vitoria": prob_vitoria,
        "custo_esperado_defesa": custo_esperado_defesa,
        "ev_defesa": ev_defesa,
        "ev_acordo": ev_acordo,
    }


def _derive_decision(
    adjusted_score: float,
    case_data: dict[str, Any],
    policy: dict[str, Any],
    ev_summary: dict[str, Any],
) -> tuple[str, list[str], str | None, float | None]:
    explicit_decision, explicit_rules, explicit_confidence = _evaluate_policy_rules(case_data, policy)
    thresholds = policy.get("robustez", {}).get("thresholds", {})
    defesa_threshold = float(thresholds.get("defesa", 0.80))
    acordo_threshold = float(thresholds.get("acordo", 0.40))

    if explicit_decision == "defesa":
        return "defesa", explicit_rules, None, explicit_confidence
    if explicit_decision == "acordo":
        strategy = "agressivo" if adjusted_score <= acordo_threshold else "conservador"
        return "acordo", explicit_rules, strategy, explicit_confidence

    rules: list[str] = []
    if adjusted_score >= defesa_threshold and ev_summary["ev_defesa"] < ev_summary["ev_acordo"]:
        rules.append("EV-DF-01: robustez alta e EV_defesa inferior ao acordo conservador")
        return "defesa", rules, None, None

    if adjusted_score <= acordo_threshold:
        rules.append("EV-AC-01: robustez baixa, acordo agressivo")
        return "acordo", rules, "agressivo", None

    if ev_summary["ev_acordo"] <= ev_summary["ev_defesa"]:
        rules.append("EV-AC-02: acordo conservador mais barato que litigar")
    else:
        rules.append("EV-AC-03: robustez insuficiente para sustentar defesa")
    return "acordo", rules, "conservador", None


def _approval_rule(valor_max: Decimal | None, policy: dict[str, Any]) -> str | None:
    if valor_max is None:
        return None

    approval = policy.get("alcada", {})
    auto_limit = Decimal(str(approval.get("aprovacao_automatica_ate", "5000")))
    manager_limit = Decimal(str(approval.get("requer_aprovacao_gestor_ate", "20000")))

    if valor_max <= auto_limit:
        return "ALC-01: faixa dentro da aprovacao automatica"
    if valor_max <= manager_limit:
        return "ALC-02: faixa requer aprovacao do gestor"
    return "ALC-03: faixa requer aprovacao da diretoria"


def _build_justification(
    case_data: dict[str, Any],
    adjusted_score: float,
    decisao: str,
    regras: list[str],
    ev_summary: dict[str, Any],
    value_context: dict[str, Any],
    history_summary: dict[str, Any] | None,
) -> str:
    total = int((history_summary or {}).get("total_casos_similares", 0) or 0)
    risk_text = f"robustez ajustada {adjusted_score:.2f}"

    if decisao == "acordo":
        return (
            f"Recomendação de acordo {value_context['strategy']} baseada em {risk_text}, "
            f"EV da defesa em {_format_brl(ev_summary['ev_defesa'])} e referência histórica "
            f"{value_context['anchor_label']} em {_format_brl(value_context['ev_acordo'])}. "
            f"Faixa sugerida entre {_format_brl(value_context['valor_sugerido_min'])} e "
            f"{_format_brl(value_context['valor_sugerido_max'])}, com {total} caso(s) similar(es) "
            f"e vulnerabilidade {case_data.get('vulnerabilidade_autor') or 'não identificada'}."
        )

    return (
        f"Recomendação de defesa baseada em {risk_text}, EV da defesa em "
        f"{_format_brl(ev_summary['ev_defesa'])} contra um acordo conservador de "
        f"{_format_brl(ev_summary['ev_acordo'])}. Regras aplicadas: {', '.join(regras)}. "
        f"Base histórica com {total} caso(s) similar(es)."
    )


def _calibrate_confidence(
    adjusted_score: float,
    decisao: str,
    ev_summary: dict[str, Any],
    history_summary: dict[str, Any] | None,
    explicit_confidence: float | None,
    value_context: dict[str, Any],
) -> float:
    if explicit_confidence is not None:
        return round(max(0.35, min(0.95, explicit_confidence)), 2)

    total = int((history_summary or {}).get("total_casos_similares", 0) or 0)
    history_factor = min(total / 10.0, 1.0)
    base = adjusted_score if decisao == "defesa" else 1 - adjusted_score

    major = max(ev_summary["ev_acordo"], ev_summary["ev_defesa"], Decimal("1"))
    ev_margin = float(abs(ev_summary["ev_acordo"] - ev_summary["ev_defesa"]) / major)

    confidence = 0.45 + (0.20 * base) + (0.20 * ev_margin) + (0.10 * history_factor)
    if decisao == "acordo" and value_context["strategy"] == "agressivo":
        confidence -= 0.05
    return round(max(0.35, min(0.95, confidence)), 2)


def build_recommendation_payload(
    case_data: dict[str, Any],
    policy: dict[str, Any],
    *,
    history_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    robustez = score_robustez_subsidios(case_data.get("subsidios") or {}, policy)
    ajustado = adjust_score(robustez, case_data, policy)
    ev_summary = calcular_ev(case_data, policy, history_summary=history_summary)
    decisao, regras, acordo_strategy, explicit_confidence = _derive_decision(
        ajustado,
        case_data,
        policy,
        ev_summary,
    )

    recommendation_context = dict(case_data)
    recommendation_context["decisao"] = decisao
    if acordo_strategy is not None:
        recommendation_context["acordo_strategy"] = acordo_strategy

    value_context = build_value_context(
        recommendation_context,
        policy,
        history_summary=history_summary,
        strategy=acordo_strategy,
    )
    valor_min, valor_max = suggest_value_range(
        recommendation_context,
        policy,
        history_summary=history_summary,
    )

    applied_rules = list(regras)
    if decisao == "acordo":
        for rule_id in value_context["applied_adjustments"]:
            if rule_id not in applied_rules:
                applied_rules.append(rule_id)

        approval_rule = _approval_rule(valor_max, policy)
        if approval_rule and approval_rule not in applied_rules:
            applied_rules.append(approval_rule)

    return {
        "decisao": decisao,
        "valor_sugerido_min": valor_min,
        "valor_sugerido_max": valor_max,
        "justificativa": _build_justification(
            case_data,
            ajustado,
            decisao,
            applied_rules,
            ev_summary,
            value_context,
            history_summary,
        ),
        "confianca": _calibrate_confidence(
            ajustado,
            decisao,
            ev_summary,
            history_summary,
            explicit_confidence,
            value_context,
        ),
        "policy_version": str(policy.get("version", "v1")),
        "regras_aplicadas": applied_rules,
        "casos_similares_ids": list((history_summary or {}).get("casos_similares_ids") or []),
        "judge_concorda": True,
        "judge_observacao": None,
    }
