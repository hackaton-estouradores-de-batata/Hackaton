from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable

import faiss
import numpy as np
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "src" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.analytics.semantic import (  # noqa: E402
    LOCAL_EMBEDDING_DIMENSIONS,
    LOCAL_EMBEDDING_MODEL,
    SEMANTIC_TEXT_STRATEGY,
    build_case_document_text,
    build_local_embedding,
    normalize_embedding_array,
)
from app.core.config import get_settings  # noqa: E402

CSV_PATH = ROOT_DIR / "data" / "sentencas_60k.csv"
OUTPUT_DIR = ROOT_DIR / "data"
EMBEDDINGS_PATH = OUTPUT_DIR / "embeddings.npy"
METADATA_PATH = OUTPUT_DIR / "embeddings_metadata.json"
INDEX_PATH = OUTPUT_DIR / "embeddings.faiss"
UF_COLUMN = "UF"
ASSUNTO_COLUMN = "Assunto"
SUBASSUNTO_COLUMN = "Sub-assunto"
RESULTADO_MACRO_COLUMN = "Resultado macro"
RESULTADO_MICRO_COLUMN = "Resultado micro"
VALOR_CAUSA_COLUMN = "Valor da causa"
PROCESSO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="utf-8", newline="").readline().strip().split(",") if "processo" in name.lower()
)
VALOR_CONDENACAO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="utf-8", newline="").readline().strip().split(",") if "indeniza" in name.lower()
)


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def build_case_text(row: dict[str, str]) -> str:
    return build_case_document_text(
        numero_processo=normalize_text(row[PROCESSO_COLUMN]),
        uf=normalize_text(row[UF_COLUMN]),
        assunto=normalize_text(row[ASSUNTO_COLUMN]),
        sub_assunto=normalize_text(row[SUBASSUNTO_COLUMN]),
        resultado_macro=normalize_text(row[RESULTADO_MACRO_COLUMN]),
        resultado_micro=normalize_text(row[RESULTADO_MICRO_COLUMN]),
        valor_causa=normalize_text(row[VALOR_CAUSA_COLUMN]),
        valor_condenacao=normalize_text(row[VALOR_CONDENACAO_COLUMN]),
    )


def _batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def _resolve_provider(requested_provider: str) -> tuple[str, str]:
    settings = get_settings()
    if requested_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY ausente para provider openai.")
        return "openai", settings.embedding_model
    if requested_provider == "local":
        return "local", LOCAL_EMBEDDING_MODEL

    if settings.openai_api_key:
        return "openai", settings.embedding_model
    return "local", LOCAL_EMBEDDING_MODEL


def _openai_embeddings(texts: list[str], *, batch_size: int, model: str) -> np.ndarray:
    client = OpenAI(api_key=get_settings().openai_api_key)
    vectors: list[np.ndarray] = []

    for batch in _batched(texts, batch_size):
        response = client.embeddings.create(model=model, input=batch)
        for item in response.data:
            vectors.append(normalize_embedding_array(np.asarray(item.embedding, dtype=np.float32)))

    if not vectors:
        return np.empty((0, 0), dtype=np.float32)
    return np.vstack(vectors).astype(np.float32)


def _local_embeddings(texts: list[str], *, dimensions: int) -> np.ndarray:
    if not texts:
        return np.empty((0, dimensions), dtype=np.float32)
    return np.vstack([build_local_embedding(text, dimensions=dimensions) for text in texts]).astype(np.float32)


def _read_rows(limit: int | None = None) -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows: list[dict[str, str]] = []
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break
            rows.append(row)
        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera embeddings do historico e persiste em FAISS.")
    parser.add_argument(
        "--provider",
        choices=("auto", "local", "openai"),
        default="auto",
        help="Provider de embeddings. 'auto' usa OpenAI quando a chave existe; senao usa embedding local deterministico.",
    )
    parser.add_argument("--batch-size", type=int, default=128, help="Tamanho do batch para o provider OpenAI.")
    parser.add_argument("--limit", type=int, default=None, help="Limite opcional de linhas para depuracao.")
    args = parser.parse_args()

    rows = _read_rows(limit=args.limit)
    texts = [build_case_text(row) for row in rows]
    provider, model = _resolve_provider(args.provider)

    if provider == "openai":
        matrix = _openai_embeddings(texts, batch_size=args.batch_size, model=model)
    else:
        matrix = _local_embeddings(texts, dimensions=LOCAL_EMBEDDING_DIMENSIONS)

    if matrix.size == 0:
        raise RuntimeError("Nenhum embedding foi gerado.")

    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)

    np.save(EMBEDDINGS_PATH, matrix)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(
        json.dumps(
            {
                "provider": provider,
                "model": model,
                "dimensions": int(matrix.shape[1]),
                "row_count": len(rows),
                "csv_path": str(CSV_PATH),
                "text_strategy": SEMANTIC_TEXT_STRATEGY,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "rows": len(rows),
                "dimensions": int(matrix.shape[1]),
                "provider": provider,
                "model": model,
                "embeddings_path": str(EMBEDDINGS_PATH),
                "metadata_path": str(METADATA_PATH),
                "index_path": str(INDEX_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
