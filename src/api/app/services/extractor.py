from pathlib import Path
from typing import Any

import pdfplumber

from app.analytics.historical import load_semantic_index_metadata
from app.analytics.semantic import SEMANTIC_TEXT_STRATEGY, build_runtime_case_text
from app.llm.client import (
    build_embedding_payload,
    extract_autos_structured,
    extract_case_context_structured,
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

    extracted_features = extract_case_context_structured(
        autos_bundle["combined_text"],
        subsidios_bundle["combined_text"],
        autos_data,
        subsidios_data,
        features_data,
        filenames=[*autos_bundle["filenames"], *subsidios_bundle["filenames"]],
    )
    embedding_text = build_runtime_case_text(
        numero_processo=autos_data.get("numero_processo"),
        uf=extracted_features.get("uf"),
        assunto=extracted_features.get("assunto"),
        sub_assunto=extracted_features.get("sub_assunto"),
        valor_causa=autos_data.get("valor_causa"),
        alegacoes=autos_data.get("alegacoes"),
        pedidos=autos_data.get("pedidos"),
        red_flags=features_data.get("red_flags"),
        vulnerabilidade_autor=features_data.get("vulnerabilidade_autor"),
        subsidios=subsidios_data,
        case_text=extracted_features.get("case_text")
        or autos_bundle["combined_text"]
        or subsidios_bundle["combined_text"]
        or " ".join([*autos_bundle["filenames"], *subsidios_bundle["filenames"]]),
    )
    historical_metadata = load_semantic_index_metadata()
    embedding_payload = build_embedding_payload(
        embedding_text,
        provider=historical_metadata.provider if historical_metadata else None,
        model=historical_metadata.model if historical_metadata else None,
        allow_local_fallback=not bool(historical_metadata and historical_metadata.provider == "openai"),
    )

    return {
        "autos_text": autos_bundle["combined_text"],
        "subsidios_text": subsidios_bundle["combined_text"],
        "autos_data": autos_data,
        "subsidios_data": subsidios_data,
        "features_data": features_data,
        "embedding": list(embedding_payload["vector"]) if embedding_payload else [],
        "embedding_provider": embedding_payload["provider"] if embedding_payload else None,
        "embedding_model": embedding_payload["model"] if embedding_payload else None,
        "embedding_dimensions": embedding_payload["dimensions"] if embedding_payload else 0,
        "embedding_source": SEMANTIC_TEXT_STRATEGY,
        "structured_features": extracted_features,
    }
