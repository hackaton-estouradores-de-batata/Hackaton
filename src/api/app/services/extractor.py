import re
from pathlib import Path

import pdfplumber


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
