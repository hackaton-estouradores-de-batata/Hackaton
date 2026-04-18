from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, getcontext
from typing import Any
import unicodedata

getcontext().prec = 28

MatrixRow = dict[str, Any]
Matrix = dict[str, MatrixRow]

SUB_GENERICO = "generico"
SUB_GOLPE = "golpe"
SUB_INDEFINIDO = "indefinido"

MIN_SUCCESS = Decimal("0.01")
MAX_SUCCESS = Decimal("0.98")
CENTS = Decimal("0.01")

W_DOC = {
    0: Decimal("0.05"),
    1: Decimal("0.15"),
    2: Decimal("0.30"),
    3: Decimal("0.45"),
    4: Decimal("0.60"),
    5: Decimal("0.75"),
    6: Decimal("0.90"),
}

DISCOUNT_BY_UF: dict[str, Decimal] = {
    "AC": Decimal("0.32"),
    "AL": Decimal("0.31"),
    "AM": Decimal("0.16"),
    "AP": Decimal("0.16"),
    "BA": Decimal("0.20"),
    "CE": Decimal("0.32"),
    "DF": Decimal("0.31"),
    "ES": Decimal("0.32"),
    "GO": Decimal("0.28"),
    "MA": Decimal("0.40"),
    "MT": Decimal("0.39"),
    "MS": Decimal("0.39"),
    "MG": Decimal("0.32"),
    "PA": Decimal("0.32"),
    "PB": Decimal("0.32"),
    "PR": Decimal("0.31"),
    "PE": Decimal("0.32"),
    "PI": Decimal("0.31"),
    "RJ": Decimal("0.32"),
    "RN": Decimal("0.31"),
    "RS": Decimal("0.27"),
    "RO": Decimal("0.31"),
    "SC": Decimal("0.31"),
    "SP": Decimal("0.31"),
    "SE": Decimal("0.33"),
    "TO": Decimal("0.31"),
}

MICRO_RESULT_PROCEDENTE = "procedente"
MICRO_RESULT_PARCIAL_PROCEDENCIA = "parcial_procedencia"
MICRO_RESULT_IMPROCEDENTE = "improcedente"
MICRO_RESULT_EXTINTO = "extinto"
MICRO_RESULT_ACORDO = "acordo"
MICRO_RESULT_OUTRO = "outro"

MICRO_RESULT_RULES: dict[str, dict[str, Any]] = {
    MICRO_RESULT_PROCEDENTE: {
        "decisao_referencia": "defesa",
        "exito_financeiro": False,
        "desconto_ped": Decimal("0.10"),
        "leitura": "nao_exito",
    },
    MICRO_RESULT_PARCIAL_PROCEDENCIA: {
        "decisao_referencia": "defesa",
        "exito_financeiro": False,
        "desconto_ped": Decimal("0.38"),
        "leitura": "nao_exito_parcial",
    },
    MICRO_RESULT_IMPROCEDENTE: {
        "decisao_referencia": "defesa",
        "exito_financeiro": True,
        "desconto_ped": Decimal("1.00"),
        "leitura": "exito",
    },
    MICRO_RESULT_EXTINTO: {
        "decisao_referencia": "nula",
        "exito_financeiro": True,
        "desconto_ped": Decimal("1.00"),
        "leitura": "exito_sem_merito",
    },
    MICRO_RESULT_ACORDO: {
        "decisao_referencia": "acordo",
        "exito_financeiro": False,
        "desconto_ped": Decimal("0.70"),
        "leitura": "ganho_parcial_por_acordo",
    },
}


def _row(d0: str, d1: str, d2: str, d3: str, d4: str, d5: str, d6: str, total: str) -> MatrixRow:
    return {
        "D": [Decimal(d0), Decimal(d1), Decimal(d2), Decimal(d3), Decimal(d4), Decimal(d5), Decimal(d6)],
        "T": Decimal(total),
    }


MATRIZ_GERAL_6D: Matrix = {
    "AC": _row("0.00", "0.07", "0.12", "0.38", "0.70", "0.87", "0.98", "0.72"),
    "AL": _row("0.00", "0.00", "0.10", "0.34", "0.63", "0.87", "0.98", "0.69"),
    "AM": _row("0.00", "0.02", "0.05", "0.17", "0.47", "0.77", "0.93", "0.52"),
    "AP": _row("0.00", "0.00", "0.05", "0.18", "0.45", "0.77", "0.92", "0.52"),
    "BA": _row("0.00", "0.00", "0.10", "0.30", "0.58", "0.87", "0.96", "0.65"),
    "CE": _row("0.00", "0.00", "0.12", "0.40", "0.65", "0.89", "0.95", "0.72"),
    "DF": _row("0.00", "0.00", "0.16", "0.32", "0.63", "0.85", "0.96", "0.67"),
    "ES": _row("0.00", "0.00", "0.08", "0.30", "0.62", "0.86", "0.95", "0.67"),
    "GO": _row("0.00", "0.03", "0.11", "0.27", "0.57", "0.84", "0.97", "0.62"),
    "MA": _row("0.00", "0.00", "0.16", "0.43", "0.75", "0.92", "0.98", "0.79"),
    "MG": _row("0.00", "0.00", "0.18", "0.37", "0.66", "0.85", "0.96", "0.70"),
    "MS": _row("0.00", "0.00", "0.18", "0.36", "0.70", "0.91", "0.98", "0.75"),
    "MT": _row("0.00", "0.14", "0.20", "0.42", "0.69", "0.90", "0.97", "0.76"),
    "PA": _row("0.00", "0.10", "0.15", "0.34", "0.66", "0.87", "0.98", "0.72"),
    "PB": _row("0.00", "0.00", "0.17", "0.36", "0.66", "0.89", "0.96", "0.71"),
    "PE": _row("0.00", "0.03", "0.11", "0.33", "0.64", "0.87", "0.97", "0.69"),
    "PI": _row("0.00", "0.00", "0.20", "0.45", "0.76", "0.92", "0.97", "0.77"),
    "PR": _row("0.00", "0.07", "0.17", "0.40", "0.70", "0.89", "0.98", "0.74"),
    "RJ": _row("0.00", "0.03", "0.09", "0.32", "0.58", "0.86", "0.92", "0.65"),
    "RN": _row("0.00", "0.05", "0.17", "0.45", "0.69", "0.89", "0.96", "0.76"),
    "RO": _row("0.00", "0.00", "0.19", "0.40", "0.70", "0.89", "0.99", "0.74"),
    "RS": _row("0.00", "0.04", "0.14", "0.28", "0.57", "0.80", "0.93", "0.62"),
    "SC": _row("0.00", "0.05", "0.17", "0.36", "0.67", "0.89", "0.97", "0.73"),
    "SE": _row("0.00", "0.09", "0.10", "0.34", "0.63", "0.88", "0.96", "0.71"),
    "SP": _row("0.00", "0.08", "0.08", "0.34", "0.64", "0.88", "0.95", "0.69"),
    "TO": _row("0.00", "0.00", "0.13", "0.41", "0.71", "0.88", "0.97", "0.75"),
    "TOTAL": _row("0.00", "0.03", "0.13", "0.34", "0.64", "0.87", "0.96", "0.70"),
}


MATRIZ_GENERICO_6D: Matrix = {
    "AC": _row("0.00", "0.22", "0.20", "0.49", "0.83", "0.95", "0.99", "0.85"),
    "AL": _row("0.00", "0.00", "0.21", "0.55", "0.77", "0.94", "0.98", "0.83"),
    "AM": _row("0.00", "0.06", "0.06", "0.25", "0.60", "0.89", "0.95", "0.66"),
    "AP": _row("0.00", "0.00", "0.15", "0.28", "0.61", "0.86", "0.96", "0.68"),
    "BA": _row("0.00", "0.00", "0.15", "0.39", "0.71", "0.94", "0.98", "0.77"),
    "CE": _row("0.00", "0.00", "0.22", "0.51", "0.80", "0.95", "0.98", "0.84"),
    "DF": _row("0.00", "0.00", "0.24", "0.50", "0.77", "0.91", "0.99", "0.80"),
    "ES": _row("0.00", "0.00", "0.17", "0.35", "0.79", "0.92", "0.92", "0.79"),
    "GO": _row("0.00", "0.00", "0.15", "0.45", "0.70", "0.90", "0.99", "0.75"),
    "MA": _row("0.00", "0.00", "0.50", "0.56", "0.90", "0.97", "0.99", "0.92"),
    "MG": _row("0.00", "0.00", "0.27", "0.59", "0.78", "0.95", "0.98", "0.83"),
    "MS": _row("0.00", "0.00", "0.47", "0.55", "0.85", "0.95", "0.98", "0.89"),
    "MT": _row("0.00", "0.25", "0.43", "0.79", "0.85", "0.97", "1.00", "0.91"),
    "PA": _row("0.00", "0.00", "0.29", "0.53", "0.83", "0.94", "0.99", "0.85"),
    "PB": _row("0.00", "0.00", "0.35", "0.55", "0.82", "0.94", "0.96", "0.84"),
    "PE": _row("0.00", "0.00", "0.27", "0.49", "0.80", "0.93", "0.99", "0.83"),
    "PI": _row("0.00", "0.00", "0.48", "0.68", "0.90", "0.96", "0.99", "0.90"),
    "PR": _row("0.00", "0.14", "0.48", "0.63", "0.88", "0.97", "1.00", "0.90"),
    "RJ": _row("0.00", "0.00", "0.20", "0.43", "0.71", "0.93", "0.95", "0.77"),
    "RN": _row("0.00", "0.20", "0.41", "0.75", "0.86", "0.94", "0.97", "0.89"),
    "RO": _row("0.00", "0.00", "0.42", "0.60", "0.86", "0.94", "1.00", "0.87"),
    "RS": _row("0.00", "0.14", "0.23", "0.40", "0.72", "0.91", "0.95", "0.77"),
    "SC": _row("0.00", "0.00", "0.39", "0.53", "0.82", "0.94", "0.99", "0.86"),
    "SE": _row("0.00", "0.25", "0.33", "0.56", "0.79", "0.94", "0.98", "0.85"),
    "SP": _row("0.00", "0.11", "0.13", "0.47", "0.80", "0.95", "0.98", "0.83"),
    "TO": _row("0.00", "0.00", "0.26", "0.65", "0.87", "0.94", "0.99", "0.88"),
    "TOTAL": _row("0.00", "0.06", "0.26", "0.50", "0.80", "0.94", "0.98", "0.83"),
}


MATRIZ_GOLPE_6D: Matrix = {
    "AC": _row("0.00", "0.00", "0.10", "0.35", "0.64", "0.84", "0.98", "0.67"),
    "AL": _row("0.00", "0.00", "0.07", "0.29", "0.56", "0.83", "0.98", "0.63"),
    "AM": _row("0.00", "0.00", "0.05", "0.15", "0.41", "0.71", "0.91", "0.46"),
    "AP": _row("0.00", "0.00", "0.03", "0.14", "0.39", "0.72", "0.89", "0.44"),
    "BA": _row("0.00", "0.00", "0.09", "0.28", "0.53", "0.83", "0.94", "0.59"),
    "CE": _row("0.00", "0.00", "0.09", "0.36", "0.59", "0.86", "0.94", "0.66"),
    "DF": _row("0.00", "0.00", "0.12", "0.26", "0.56", "0.82", "0.94", "0.62"),
    "ES": _row("0.00", "0.00", "0.06", "0.28", "0.53", "0.82", "0.97", "0.61"),
    "GO": _row("0.00", "0.03", "0.09", "0.21", "0.51", "0.81", "0.96", "0.56"),
    "MA": _row("0.00", "0.00", "0.12", "0.39", "0.68", "0.89", "0.97", "0.74"),
    "MG": _row("0.00", "0.00", "0.15", "0.30", "0.59", "0.80", "0.95", "0.64"),
    "MS": _row("0.00", "0.00", "0.14", "0.31", "0.63", "0.88", "0.98", "0.69"),
    "MT": _row("0.00", "0.11", "0.16", "0.33", "0.62", "0.87", "0.95", "0.70"),
    "PA": _row("0.00", "0.12", "0.13", "0.28", "0.59", "0.84", "0.97", "0.66"),
    "PB": _row("0.00", "0.00", "0.13", "0.29", "0.59", "0.87", "0.96", "0.66"),
    "PE": _row("0.00", "0.04", "0.08", "0.28", "0.57", "0.85", "0.95", "0.64"),
    "PI": _row("0.00", "0.00", "0.15", "0.36", "0.69", "0.90", "0.96", "0.72"),
    "PR": _row("0.00", "0.05", "0.10", "0.34", "0.63", "0.85", "0.97", "0.68"),
    "RJ": _row("0.00", "0.03", "0.07", "0.27", "0.52", "0.83", "0.91", "0.60"),
    "RN": _row("0.00", "0.00", "0.12", "0.34", "0.60", "0.87", "0.96", "0.70"),
    "RO": _row("0.00", "0.00", "0.14", "0.34", "0.63", "0.86", "0.98", "0.69"),
    "RS": _row("0.00", "0.00", "0.11", "0.24", "0.51", "0.75", "0.92", "0.56"),
    "SC": _row("0.00", "0.06", "0.13", "0.31", "0.61", "0.87", "0.95", "0.67"),
    "SE": _row("0.00", "0.05", "0.05", "0.28", "0.56", "0.86", "0.95", "0.65"),
    "SP": _row("0.00", "0.06", "0.07", "0.30", "0.57", "0.84", "0.94", "0.63"),
    "TO": _row("0.00", "0.00", "0.10", "0.34", "0.65", "0.86", "0.96", "0.70"),
    "TOTAL": _row("0.00", "0.02", "0.10", "0.29", "0.57", "0.84", "0.95", "0.64"),
}


@dataclass
class PolicyCaseInputV5:
    ped: Decimal
    uf: str
    sub: str = SUB_INDEFINIDO
    contrato: bool = False
    comprovante_credito: bool = False
    extrato: bool = False
    demonstrativo_evolucao_divida: bool = False
    dossie: bool = False
    laudo_referenciado: bool = False
    documento_contraditorio: bool = False
    qtd_docs_override: int | None = None


@dataclass
class PolicyResultV5:
    decisao: str
    justificativa_curta: str
    ped: Decimal
    uf: str
    sub: str
    matriz_escolhida: str
    uf_sem_historico_proprio: bool
    revisao_humana: bool
    qtd_docs: int
    p_suc: Decimal
    p_per: Decimal
    vej: Decimal
    abertura: Decimal
    alvo: Decimal
    teto: Decimal
    teto_pct: Decimal


@dataclass(frozen=True)
class MicroResultEconomicOutcome:
    resultado_micro_normalizado: str
    decisao_referencia: str
    exito_financeiro: bool
    desconto_ped: Decimal
    percentual_pago: Decimal
    valor_preservado: Decimal
    valor_pago: Decimal
    leitura: str


def _clamp(value: Decimal, min_value: Decimal, max_value: Decimal) -> Decimal:
    return max(min_value, min(value, max_value))


def _round_to_nearest_100(value: Decimal) -> Decimal:
    return (value / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("100")


def _max_hundred_below(value: Decimal) -> Decimal:
    if value <= 0:
        return Decimal("0")
    base = ((value - Decimal("0.01")) / Decimal("100")).to_integral_value(rounding=ROUND_FLOOR)
    return max(Decimal("0"), base * Decimal("100"))


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value in (None, ""):
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _normalize_free_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(ascii_only.strip().lower().split())


def _normalize_uf(value: Any) -> str:
    cleaned = str(value or "").strip().upper()
    return cleaned if cleaned else "TOTAL"


def normalize_sub_assunto_v5(value: Any) -> str:
    lowered = _normalize_free_text(value)
    if "golpe" in lowered or "fraude" in lowered:
        return SUB_GOLPE
    if "generico" in lowered or "genérico" in lowered:
        return SUB_GENERICO
    return SUB_INDEFINIDO


def normalize_micro_result_v5(value: Any) -> str:
    lowered = _normalize_free_text(value)
    if not lowered:
        return MICRO_RESULT_OUTRO
    if "parcial" in lowered and "proced" in lowered:
        return MICRO_RESULT_PARCIAL_PROCEDENCIA
    if "improced" in lowered:
        return MICRO_RESULT_IMPROCEDENTE
    if "extint" in lowered:
        return MICRO_RESULT_EXTINTO
    if "acordo" in lowered:
        return MICRO_RESULT_ACORDO
    if "proced" in lowered:
        return MICRO_RESULT_PROCEDENTE
    return MICRO_RESULT_OUTRO


def classify_micro_result_economic(
    resultado_micro: Any,
    ped: Decimal | None = None,
) -> MicroResultEconomicOutcome | None:
    normalized = normalize_micro_result_v5(resultado_micro)
    rule = MICRO_RESULT_RULES.get(normalized)
    if rule is None:
        return None

    ped_decimal = _to_decimal(ped).quantize(CENTS) if ped is not None else Decimal("0.00")
    desconto_ped = Decimal(rule["desconto_ped"]).quantize(CENTS)
    percentual_pago = (Decimal("1") - desconto_ped).quantize(CENTS)
    valor_preservado = (ped_decimal * desconto_ped).quantize(CENTS)
    valor_pago = (ped_decimal * percentual_pago).quantize(CENTS)

    return MicroResultEconomicOutcome(
        resultado_micro_normalizado=normalized,
        decisao_referencia=str(rule["decisao_referencia"]),
        exito_financeiro=bool(rule["exito_financeiro"]),
        desconto_ped=desconto_ped,
        percentual_pago=percentual_pago,
        valor_preservado=valor_preservado,
        valor_pago=valor_pago,
        leitura=str(rule["leitura"]),
    )


def micro_result_rules_payload() -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    for key, rule in MICRO_RESULT_RULES.items():
        payload[key] = {
            "decisao_referencia": str(rule["decisao_referencia"]),
            "exito_financeiro": bool(rule["exito_financeiro"]),
            "desconto_ped": float(Decimal(rule["desconto_ped"]).quantize(CENTS)),
            "percentual_pago": float((Decimal("1") - Decimal(rule["desconto_ped"])).quantize(CENTS)),
            "leitura": str(rule["leitura"]),
        }
    return payload


def _count_qtd_docs(case: PolicyCaseInputV5) -> int:
    if case.qtd_docs_override is not None:
        if case.qtd_docs_override < 0 or case.qtd_docs_override > 6:
            raise ValueError("qtd_docs_override deve estar entre 0 e 6")
        return case.qtd_docs_override

    return (
        int(case.contrato)
        + int(case.comprovante_credito)
        + int(case.extrato)
        + int(case.demonstrativo_evolucao_divida)
        + int(case.dossie)
        + int(case.laudo_referenciado)
    )


def _select_matrix(sub: str) -> tuple[str, Matrix]:
    if sub == SUB_GENERICO:
        return "MATRIZ_GENERICO_6D", MATRIZ_GENERICO_6D
    if sub == SUB_GOLPE:
        return "MATRIZ_GOLPE_6D", MATRIZ_GOLPE_6D
    return "MATRIZ_GERAL_6D", MATRIZ_GERAL_6D


def _build_justificativa(decisao: str, ped: Decimal, vej: Decimal, alvo: Decimal, teto: Decimal) -> str:
    if decisao == "ACORDO":
        ganho = vej - alvo
        return f"ACORDO porque o ALVO fica abaixo do VEJ em R$ {ganho:.2f}."

    piso_comercial = ped * Decimal("0.25")
    diff = piso_comercial - vej
    return f"DEFESA porque o TETO racional fica abaixo do piso comercial em R$ {diff:.2f}."


def _enforce_offer_invariants(
    abertura: Decimal,
    alvo: Decimal,
    teto: Decimal,
    vej: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    alvo = max(alvo, abertura)
    teto = max(teto, alvo)

    if teto >= vej:
        teto = _max_hundred_below(vej)
        alvo = min(alvo, teto)
        abertura = min(abertura, alvo)

    return max(abertura, Decimal("0")), max(alvo, Decimal("0")), max(teto, Decimal("0"))


def build_policy_case_input(case_data: dict[str, Any]) -> PolicyCaseInputV5:
    subsidios = dict(case_data.get("subsidios") or {})
    ped = _to_decimal(case_data.get("valor_pedido_danos_morais"))
    if ped <= 0:
        ped = _to_decimal(case_data.get("valor_causa"))

    return PolicyCaseInputV5(
        ped=ped.quantize(CENTS) if ped > 0 else Decimal("0"),
        uf=_normalize_uf(case_data.get("uf")),
        sub=normalize_sub_assunto_v5(case_data.get("sub_assunto")),
        contrato=bool(subsidios.get("tem_contrato")),
        comprovante_credito=bool(subsidios.get("tem_comprovante")),
        extrato=bool(subsidios.get("tem_extrato")),
        demonstrativo_evolucao_divida=bool(subsidios.get("tem_demonstrativo_evolucao_divida")),
        dossie=bool(subsidios.get("tem_dossie")),
        laudo_referenciado=bool(subsidios.get("tem_laudo_referenciado")),
        documento_contraditorio=bool(subsidios.get("documento_contraditorio")),
    )


def documentos_presentes(case: PolicyCaseInputV5) -> list[str]:
    ordered = [
        ("contrato", case.contrato),
        ("comprovante_credito", case.comprovante_credito),
        ("extrato", case.extrato),
        ("demonstrativo_evolucao_divida", case.demonstrativo_evolucao_divida),
        ("dossie", case.dossie),
        ("laudo_referenciado", case.laudo_referenciado),
    ]
    return [name for name, present in ordered if present]


def calculate_policy_v5(case: PolicyCaseInputV5) -> PolicyResultV5:
    if case.ped <= 0:
        raise ValueError("PED deve ser maior que zero")

    uf = _normalize_uf(case.uf)
    sub = normalize_sub_assunto_v5(case.sub)
    qtd_docs = _count_qtd_docs(case)

    matrix_name, matrix = _select_matrix(sub)
    uf_key = uf if uf in matrix else "TOTAL"
    uf_sem_historico_proprio = uf_key == "TOTAL" and uf != "TOTAL"

    desc_uf = DISCOUNT_BY_UF.get(uf, Decimal("0.30"))
    total_row = matrix["TOTAL"]
    uf_row = matrix[uf_key]

    p_raw = [Decimal("0") for _ in range(7)]
    for docs in range(1, 7):
        p_total_docs = total_row["D"][docs]
        p_cell_docs = uf_row["D"][docs]
        p_raw[docs] = p_total_docs + W_DOC[docs] * (p_cell_docs - p_total_docs)

    p1_proxy = p_raw[1]
    gap0 = total_row["D"][1] - total_row["D"][0]
    uf_shift = uf_row["T"] - total_row["T"]
    p0_context = total_row["D"][0] + Decimal("0.15") * uf_shift
    p_raw[0] = _clamp(min(p0_context, p1_proxy - gap0), Decimal("0"), p1_proxy)

    p_corr = [Decimal("0") for _ in range(7)]
    p_corr[0] = _clamp(p_raw[0], Decimal("0"), MAX_SUCCESS)
    for docs in range(1, 7):
        p_corr[docs] = _clamp(max(p_raw[docs], p_corr[docs - 1]), Decimal("0"), MAX_SUCCESS)

    p_suc = _clamp(p_corr[qtd_docs], MIN_SUCCESS, MAX_SUCCESS)
    p_per = Decimal("1") - p_suc

    f_pag = Decimal("1") - desc_uf
    vpc = case.ped * f_pag
    vej = vpc * p_per

    f_ab = _clamp(Decimal("0.90") - Decimal("0.05") * Decimal(qtd_docs), Decimal("0.60"), Decimal("0.95"))
    f_al = _clamp(f_ab + Decimal("0.08"), Decimal("0.65"), Decimal("0.97"))
    f_tet = _clamp(f_ab + Decimal("0.15"), Decimal("0.70"), Decimal("0.99"))

    abertura = _round_to_nearest_100(vej * f_ab)
    alvo = _round_to_nearest_100(vej * f_al)
    teto = _round_to_nearest_100(vej * f_tet)
    abertura, alvo, teto = _enforce_offer_invariants(abertura, alvo, teto, vej)

    teto_pct = (teto / case.ped) if case.ped > 0 else Decimal("0")
    decisao = "ACORDO" if teto_pct >= Decimal("0.25") else "DEFESA"
    justificativa = _build_justificativa(decisao, case.ped, vej, alvo, teto)

    return PolicyResultV5(
        decisao=decisao,
        justificativa_curta=justificativa,
        ped=case.ped.quantize(CENTS),
        uf=uf,
        sub=sub,
        matriz_escolhida=matrix_name,
        uf_sem_historico_proprio=uf_sem_historico_proprio,
        revisao_humana=case.documento_contraditorio,
        qtd_docs=qtd_docs,
        p_suc=p_suc,
        p_per=p_per,
        vej=vej.quantize(CENTS),
        abertura=abertura.quantize(CENTS),
        alvo=alvo.quantize(CENTS),
        teto=teto.quantize(CENTS),
        teto_pct=teto_pct.quantize(Decimal("0.0001")),
    )


def resolve_policy_backtest_cost(result: PolicyResultV5) -> Decimal:
    return result.alvo if result.decisao == "ACORDO" else result.vej


def build_policy_trace(result: PolicyResultV5, case: PolicyCaseInputV5) -> dict[str, Any]:
    return {
        "mode": "v5",
        "matriz_escolhida": result.matriz_escolhida,
        "sub_estatistico": result.sub,
        "qtd_docs": result.qtd_docs,
        "documentos_presentes": documentos_presentes(case),
        "p_suc": float(result.p_suc),
        "p_per": float(result.p_per),
        "vej": float(result.vej),
        "abertura": float(result.abertura),
        "alvo": float(result.alvo),
        "teto": float(result.teto),
        "teto_pct": float(result.teto_pct),
        "revisao_humana": result.revisao_humana,
        "uf_sem_historico_proprio": result.uf_sem_historico_proprio,
    }
