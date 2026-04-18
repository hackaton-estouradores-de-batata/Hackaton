from __future__ import annotations

import re
import unicodedata
from typing import Any

DOC_TYPES = (
    "contrato",
    "comprovante_credito",
    "extrato",
    "demonstrativo_evolucao_divida",
    "dossie",
    "laudo_referenciado",
)

FILENAME_MARKERS = {
    "contrato": ("contrato", "cedula_credito", "proposta_adesao"),
    "comprovante_credito": ("comprovante_credito", "credito_bacen", "bacen", "rdr"),
    "extrato": ("extrato", "extrato_bancario"),
    "demonstrativo_evolucao_divida": (
        "demonstrativo_evolucao_divida",
        "evolucao_divida",
        "demonstrativo_divida",
    ),
    "dossie": ("dossie", "dossi", "veritas"),
    "laudo_referenciado": ("laudo_referenciado", "laudo", "liveness", "biometria"),
}

TEXT_MARKERS = {
    "contrato": (
        "cedula de credito bancario",
        "numero do contrato",
        "assinatura do emitente",
        "assinatura do contratante",
    ),
    "comprovante_credito": (
        "comprovante de credito",
        "banco central do brasil",
        "conta creditada",
        "dados do credito",
    ),
    "extrato": (
        "extrato bancario",
        "saldo anterior",
        "lancamentos",
        "saldo do dia",
    ),
    "demonstrativo_evolucao_divida": (
        "demonstrativo de evolucao da divida",
        "saldo devedor",
        "evolucao da divida",
        "saldo atualizado",
    ),
    "dossie": (
        "dossie",
        "veritas",
        "parecer geral",
        "conformidade",
    ),
    "laudo_referenciado": (
        "laudo referenciado",
        "video de liveness",
        "biometria facial",
        "selfie",
    ),
}


def _normalize_token(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def classify_document(
    filename: str,
    text: str,
    *,
    category: str | None = None,
) -> set[str]:
    normalized_name = _normalize_token(filename)
    normalized_category = _normalize_token(category)
    matches: set[str] = set()

    for document_type, markers in FILENAME_MARKERS.items():
        if _contains_any(normalized_name, markers) or _contains_any(normalized_category, markers):
            matches.add(document_type)

    if matches:
        return matches

    normalized_text = _normalize_token(str(text or "")[:8000])
    for document_type, markers in TEXT_MARKERS.items():
        if _contains_any(normalized_text, markers):
            matches.add(document_type)

    return matches


def build_document_inventory(texts_by_category: dict[str, dict[str, str]]) -> dict[str, Any]:
    files_by_type: dict[str, list[str]] = {document_type: [] for document_type in DOC_TYPES}
    presence = {document_type: False for document_type in DOC_TYPES}

    for category, texts_by_file in texts_by_category.items():
        for filename, text in texts_by_file.items():
            document_types = classify_document(filename, text, category=category)
            for document_type in document_types:
                presence[document_type] = True
                if filename not in files_by_type[document_type]:
                    files_by_type[document_type].append(filename)

    documentos_presentes = [document_type for document_type in DOC_TYPES if presence[document_type]]
    return {
        **presence,
        "qtd_docs": len(documentos_presentes),
        "documentos_presentes": documentos_presentes,
        "files_by_type": {key: value for key, value in files_by_type.items() if value},
    }


def inventory_to_subsidios_fields(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "tem_contrato": bool(inventory.get("contrato")),
        "tem_comprovante": bool(inventory.get("comprovante_credito")),
        "tem_extrato": bool(inventory.get("extrato")),
        "tem_dossie": bool(inventory.get("dossie")),
        "tem_demonstrativo_evolucao_divida": bool(inventory.get("demonstrativo_evolucao_divida")),
        "tem_laudo_referenciado": bool(inventory.get("laudo_referenciado")),
    }


def merge_subsidios_with_inventory(
    subsidios_data: dict[str, Any],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(subsidios_data)
    merged.update(inventory_to_subsidios_fields(inventory))
    return merged
