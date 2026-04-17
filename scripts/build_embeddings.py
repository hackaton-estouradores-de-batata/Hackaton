from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "data" / "sentencas_60k.csv"
OUTPUT_DIR = ROOT_DIR / "data"
EMBEDDINGS_PATH = OUTPUT_DIR / "embeddings.npy"
METADATA_PATH = OUTPUT_DIR / "embeddings_metadata.json"
INDEX_PATH = OUTPUT_DIR / "embeddings.faiss"
EMBEDDING_DIMENSIONS = 8
PROCESSO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="latin-1", newline="").readline().strip().split(",") if "processo" in name.lower()
)
UF_COLUMN = "UF"
ASSUNTO_COLUMN = "Assunto"
SUBASSUNTO_COLUMN = "Sub-assunto"
RESULTADO_MACRO_COLUMN = "Resultado macro"
RESULTADO_MICRO_COLUMN = "Resultado micro"
VALOR_CAUSA_COLUMN = "Valor da causa"
VALOR_CONDENACAO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="latin-1", newline="").readline().strip().split(",") if "indeniza" in name.lower()
)


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def build_case_text(row: dict[str, str]) -> str:
    parts = [
        f"processo {normalize_text(row[PROCESSO_COLUMN])}",
        f"uf {normalize_text(row[UF_COLUMN])}",
        f"assunto {normalize_text(row[ASSUNTO_COLUMN])}",
        f"sub assunto {normalize_text(row[SUBASSUNTO_COLUMN])}",
        f"resultado macro {normalize_text(row[RESULTADO_MACRO_COLUMN])}",
        f"resultado micro {normalize_text(row[RESULTADO_MICRO_COLUMN])}",
        f"valor da causa {normalize_text(row[VALOR_CAUSA_COLUMN])}",
        f"valor da condenacao {normalize_text(row[VALOR_CONDENACAO_COLUMN])}",
    ]
    return " | ".join(parts)


def build_stub_embedding(text: str) -> np.ndarray:
    raw = text.encode("utf-8")
    vector = np.zeros(EMBEDDING_DIMENSIONS, dtype=np.float32)

    if not raw:
        return vector

    for index, byte in enumerate(raw):
        vector[index % EMBEDDING_DIMENSIONS] += byte

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector /= norm
    return vector


def main() -> None:
    embeddings: list[np.ndarray] = []
    metadata: list[dict[str, str | int]] = []

    with CSV_PATH.open("r", encoding="latin-1", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_index, row in enumerate(reader):
            text = build_case_text(row)
            embeddings.append(build_stub_embedding(text))
            metadata.append(
                {
                    "row_index": row_index,
                    "case_id": normalize_text(row[PROCESSO_COLUMN]),
                    "text": text,
                    "valor_causa": normalize_text(row[VALOR_CAUSA_COLUMN]),
                }
            )

    matrix = np.vstack(embeddings) if embeddings else np.empty((0, EMBEDDING_DIMENSIONS), dtype=np.float32)
    np.save(EMBEDDINGS_PATH, matrix)
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    INDEX_PATH.write_bytes(matrix.tobytes())

    print(
        json.dumps(
            {
                "rows": len(metadata),
                "dimensions": EMBEDDING_DIMENSIONS,
                "embeddings_path": str(EMBEDDINGS_PATH),
                "metadata_path": str(METADATA_PATH),
                "index_path": str(INDEX_PATH),
                "mode": "stub",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
