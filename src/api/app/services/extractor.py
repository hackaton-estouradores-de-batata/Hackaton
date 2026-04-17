import re
from pathlib import Path
from typing import Any

import pdfplumber

from app.llm.client import (
    embed_peticao,
    extract_autos_structured,
    extract_features_structured,
    extract_subsidios_structured,
)


def extract_text_from_pdf(pdf_path: Path) -> str:
    pages: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            stripped = text.strip()
            if stripped:
                pages.append(stripped)

    return "\n\n".join(pages)


def extract_texts_from_paths(pdf_paths: list[Path]) -> dict[str, str]:
    extracted: dict[str, str] = {}

    for path in pdf_paths:
        extracted[path.name] = extract_text_from_pdf(path)

    return extracted


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return " ".join(match.group(1).split())


def _normalize_uf(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[^A-Za-z]", "", value).upper()
    return cleaned[:2] if cleaned else None


def extract_case_features(texts: dict[str, str]) -> dict[str, str | None]:
    combined_text = "\n\n".join(text for text in texts.values() if text.strip())
    compact_text = " ".join(combined_text.split())

    return {
        "uf": _normalize_uf(_search(r"\bUF\s*[:\-]?\s*([A-Za-z]{2})\b", combined_text)),
        "assunto": _search(r"\bAssunto\s*[:\-]?\s*(.+)", combined_text),
        "sub_assunto": _search(r"\bSub[- ]assunto\s*[:\-]?\s*(.+)", combined_text),
        "case_text": compact_text or None,
    }


def _bundle_documents(pdf_paths: list[Path]) -> dict[str, Any]:
    texts = extract_texts_from_paths(pdf_paths)
    sections = [f"## {name}\n{text}" for name, text in texts.items() if text]
    return {
        "texts_by_file": texts,
        "combined_text": "\n\n".join(sections).strip(),
        "filenames": list(texts.keys()),
    }


def analyze_case_documents(autos_paths: list[Path], subsidios_paths: list[Path]) -> dict[str, Any]:
    autos_bundle = _bundle_documents(autos_paths)
    subsidios_bundle = _bundle_documents(subsidios_paths)

    autos_data = extract_autos_structured(autos_bundle["combined_text"])
    subsidios_data = extract_subsidios_structured(subsidios_bundle["combined_text"])
    features_data = extract_features_structured(
        autos_bundle["combined_text"],
        autos_data,
        subsidios_data,
    )

    extracted_features = extract_case_features(
        {
            **autos_bundle["texts_by_file"],
            **subsidios_bundle["texts_by_file"],
        }
    )

    return {
        "autos_text": autos_bundle["combined_text"],
        "subsidios_text": subsidios_bundle["combined_text"],
        "autos_data": autos_data,
        "subsidios_data": subsidios_data,
        "features_data": features_data,
        "embedding": embed_peticao(autos_bundle["combined_text"] or subsidios_bundle["combined_text"]),
        "structured_features": extracted_features,
    }
