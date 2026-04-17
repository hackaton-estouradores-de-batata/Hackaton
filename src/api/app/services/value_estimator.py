from __future__ import annotations

from decimal import Decimal
from typing import Any

CENTS = Decimal("0.01")


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _resolve_case_value(case_data: dict[str, Any], key: str) -> Any:
    if key in case_data:
        return case_data.get(key)

    subsidios = case_data.get("subsidios") or {}
    if key in subsidios:
        return subsidios.get(key)
    return None


def _matches_expression(expression: str, case_data: dict[str, Any]) -> bool:
    normalized = expression.strip()
    if normalized == "autor_idoso":
        return case_data.get("vulnerabilidade_autor") == "idoso"

    for operator in ("==", ">=", "<=", ">", "<"):
        if operator not in normalized:
            continue

        left, right = [part.strip() for part in normalized.split(operator, maxsplit=1)]
        actual = _resolve_case_value(case_data, left)
        if actual is None:
            return False

        if operator == "==":
            expected = right.strip("'\"")
            return str(actual) == expected

        actual_decimal = _to_decimal(actual)
        expected_decimal = _to_decimal(right.strip("'\""))
        if operator == ">=":
            return actual_decimal >= expected_decimal
        if operator == "<=":
            return actual_decimal <= expected_decimal
        if operator == ">":
            return actual_decimal > expected_decimal
        if operator == "<":
            return actual_decimal < expected_decimal

    return False


def _policy_multiplier(case_data: dict[str, Any], value_policy: dict[str, Any]) -> Decimal:
    multiplier = Decimal("1")

    for factor in value_policy.get("fatores_ajuste", []):
        expression = str(factor.get("se", "")).strip()
        if expression and _matches_expression(expression, case_data):
            multiplier *= Decimal(str(factor.get("multiplicador", "1")))

    return multiplier


def _policy_adjustment_ids(case_data: dict[str, Any], value_policy: dict[str, Any]) -> list[str]:
    applied: list[str] = []

    for factor in value_policy.get("fatores_ajuste", []):
        expression = str(factor.get("se", "")).strip()
        if expression and _matches_expression(expression, case_data):
            applied.append(str(factor.get("id", "VAL")))

    return applied


def _history_percentile(history_summary: dict[str, Any] | None, field_name: str) -> Decimal:
    stats = dict((history_summary or {}).get("stats") or {})
    return _to_decimal(stats.get(field_name), "0")


def _interpolate(lower: Decimal, upper: Decimal, ratio: str) -> Decimal:
    if lower <= 0:
        return upper
    if upper <= lower:
        return lower
    return lower + (upper - lower) * Decimal(ratio)


def _upper_cap(case_data: dict[str, Any]) -> Decimal | None:
    candidates = [
        _to_decimal(case_data.get("valor_pedido_danos_morais")),
        _to_decimal(case_data.get("valor_causa")),
    ]
    positives = [value for value in candidates if value > 0]
    if not positives:
        return None
    return min(positives)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENTS)


def build_value_context(
    case_data: dict[str, Any],
    policy: dict[str, Any],
    *,
    history_summary: dict[str, Any] | None = None,
    strategy: str | None = None,
) -> dict[str, Any]:
    value_policy = policy.get("valor", {})
    selected_strategy = str(strategy or case_data.get("acordo_strategy") or "conservador")
    percentile_25 = _history_percentile(history_summary, "percentil_25")
    percentile_50 = _history_percentile(history_summary, "percentil_50")
    percentile_35 = _interpolate(percentile_25, percentile_50, "0.40")
    floor_value = Decimal(str(value_policy.get("piso_minimo", "1500")))
    multiplier = _policy_multiplier(case_data, value_policy)
    applied_adjustments = _policy_adjustment_ids(case_data, value_policy)
    cap = _upper_cap(case_data)

    if cap is not None:
        floor_value = min(floor_value, cap)

    if multiplier == Decimal("1"):
        if case_data.get("vulnerabilidade_autor") == "idoso":
            multiplier += Decimal("0.10")
        if float(case_data.get("indicio_fraude", 0.0) or 0.0) > 0.5:
            multiplier -= Decimal("0.05")

    history_based = percentile_25 > 0 or percentile_50 > 0
    if history_based:
        if selected_strategy == "agressivo":
            anchor_label = "p35"
            base_min = percentile_35 if percentile_35 > 0 else percentile_25
            base_max = percentile_50 if percentile_50 > 0 else base_min
            ev_anchor = base_min
        else:
            anchor_label = "p25"
            base_min = percentile_25 if percentile_25 > 0 else percentile_35
            base_max = percentile_35 if percentile_35 > 0 else max(percentile_25, percentile_50)
            ev_anchor = base_min
    else:
        percentual_min = Decimal(str(value_policy.get("percentual_min_valor_base", "0.15")))
        percentual_max = Decimal(str(value_policy.get("percentual_max_valor_base", "0.25")))
        anchor_label = "fallback"
        valor_base = _to_decimal(case_data.get("valor_pedido_danos_morais"))
        if valor_base <= 0:
            valor_base = _to_decimal(case_data.get("valor_causa")) * Decimal("0.25")
        if valor_base <= 0:
            valor_base = Decimal("5000")

        base_min = valor_base * percentual_min
        base_max = valor_base * percentual_max
        if selected_strategy == "agressivo":
            base_min = _interpolate(base_min, base_max, "0.50")
            anchor_label = "fallback_agressivo"
        ev_anchor = base_min

    value_min = _quantize(base_min * multiplier)
    value_max = _quantize(base_max * multiplier)
    ev_acordo = _quantize(ev_anchor * multiplier)

    if cap is not None:
        value_min = min(value_min, cap)
        value_max = min(value_max, cap)
        ev_acordo = min(ev_acordo, cap)

    value_min = max(floor_value, value_min)
    value_max = max(value_min, value_max)
    ev_acordo = max(floor_value, ev_acordo)

    if cap is not None:
        value_min = min(value_min, cap)
        value_max = min(value_max, cap)
        ev_acordo = min(ev_acordo, cap)
        value_min = min(value_min, value_max)

    return {
        "strategy": selected_strategy,
        "history_based": history_based,
        "anchor_label": anchor_label,
        "percentil_25": percentile_25,
        "percentil_35": percentile_35,
        "percentil_50": percentile_50,
        "multiplier": multiplier,
        "applied_adjustments": applied_adjustments,
        "ev_acordo": ev_acordo,
        "valor_sugerido_min": _quantize(value_min),
        "valor_sugerido_max": _quantize(value_max),
    }


def suggest_value_range(
    case_data: dict[str, Any],
    policy: dict[str, Any],
    *,
    history_summary: dict[str, Any] | None = None,
) -> tuple[Decimal | None, Decimal | None]:
    if case_data.get("decisao") != "acordo":
        return None, None

    value_context = build_value_context(case_data, policy, history_summary=history_summary)
    return value_context["valor_sugerido_min"], value_context["valor_sugerido_max"]
