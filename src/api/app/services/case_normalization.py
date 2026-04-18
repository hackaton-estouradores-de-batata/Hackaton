from __future__ import annotations

import re
from typing import Any, Mapping

from app.models.case import Case


def coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        chunks = [chunk.strip(" -•\n\t") for chunk in value.replace(";", "\n").splitlines()]
        return [chunk for chunk in chunks if chunk]
    return [str(value)]


def coerce_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    match = re.search(r"(\d+(?:[\.,]\d+)?)", str(value))
    if match:
        return float(match.group(1).replace(",", "."))
    return default


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    lowered = str(value).strip().lower()
    return lowered in {"1", "true", "sim", "yes", "y", "presente"}


def coerce_subsidios(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    normalized = dict(value)
    for key in ("tem_contrato", "tem_extrato", "tem_dossie", "tem_comprovante", "assinatura_validada"):
        if key in normalized:
            normalized[key] = coerce_bool(normalized[key])
    if "valor_emprestimo" in normalized:
        normalized["valor_emprestimo"] = coerce_float(normalized["valor_emprestimo"], 0.0)
    return normalized


def coerce_vulnerabilidade(value: Any) -> str:
    lowered = str(value or "").strip().lower()
    if "idos" in lowered:
        return "idoso"
    if "analfabet" in lowered:
        return "analfabeto"
    if "baixa renda" in lowered or "hipossuf" in lowered:
        return "baixa_renda"
    return "nenhuma"


def normalize_case_record(case: Case) -> Case:
    case.alegacoes = coerce_list(case.alegacoes)
    case.pedidos = coerce_list(case.pedidos)
    case.red_flags = coerce_list(case.red_flags)
    case.inconsistencias_temporais = coerce_list(case.inconsistencias_temporais)
    case.vulnerabilidade_autor = coerce_vulnerabilidade(case.vulnerabilidade_autor)
    case.indicio_fraude = coerce_float(case.indicio_fraude, 0.0)
    case.forca_narrativa_autor = coerce_float(case.forca_narrativa_autor, 0.0)
    case.subsidios = coerce_subsidios(case.subsidios)
    return case


def normalize_case_snapshot(snapshot: Mapping[str, Any]) -> dict[str, object]:
    return {
        **snapshot,
        "uf": _coerce_text(snapshot.get("uf"), uppercase=True),
        "assunto": _coerce_text(snapshot.get("assunto")),
        "sub_assunto": _coerce_text(snapshot.get("sub_assunto")),
        "alegacoes": coerce_list(snapshot.get("alegacoes")),
        "pedidos": coerce_list(snapshot.get("pedidos")),
        "case_text": _coerce_text(snapshot.get("case_text")),
        "red_flags": coerce_list(snapshot.get("red_flags")),
        "vulnerabilidade_autor": coerce_vulnerabilidade(snapshot.get("vulnerabilidade_autor")),
        "indicio_fraude": coerce_float(snapshot.get("indicio_fraude"), 0.0),
        "forca_narrativa_autor": coerce_float(snapshot.get("forca_narrativa_autor"), 0.0),
        "subsidios": coerce_subsidios(snapshot.get("subsidios")),
    }


def _coerce_text(value: Any, *, uppercase: bool = False) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text.upper() if uppercase else text
