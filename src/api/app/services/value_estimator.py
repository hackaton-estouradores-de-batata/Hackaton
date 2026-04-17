from decimal import Decimal
from typing import Any


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


def suggest_value_range(case_data: dict[str, Any], policy: dict[str, Any]) -> tuple[Decimal | None, Decimal | None]:
    if case_data["decisao"] != "acordo":
        return None, None

    value_policy = policy.get("valor", {})
    percentual_min = Decimal(str(value_policy.get("percentual_min_valor_base", "0.15")))
    percentual_max = Decimal(str(value_policy.get("percentual_max_valor_base", "0.25")))
    piso = Decimal(str(value_policy.get("piso_minimo", "1500")))

    valor_base = _to_decimal(case_data.get("valor_pedido_danos_morais"))
    if valor_base <= 0:
        valor_base = _to_decimal(case_data.get("valor_causa")) * Decimal("0.25")
    if valor_base <= 0:
        valor_base = Decimal("5000")

    multiplicador = Decimal("1")
    if case_data.get("vulnerabilidade_autor") == "idoso":
        multiplicador += Decimal("0.10")
    if case_data.get("indicio_fraude", 0) > 0.5:
        multiplicador -= Decimal("0.05")

    valor_min = max(piso, (valor_base * percentual_min * multiplicador).quantize(Decimal("0.01")))
    valor_max = max(
        valor_min,
        (valor_base * percentual_max * multiplicador).quantize(Decimal("0.01")),
    )
    return valor_min, valor_max
