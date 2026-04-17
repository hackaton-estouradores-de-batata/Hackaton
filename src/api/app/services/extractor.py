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
