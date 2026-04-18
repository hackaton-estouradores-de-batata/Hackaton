from __future__ import annotations

import hashlib
import re
import unicodedata
from decimal import Decimal
from typing import Iterable, Mapping, Sequence

import numpy as np

LOCAL_EMBEDDING_DIMENSIONS = 64
LOCAL_EMBEDDING_MODEL = f"local-semantic-v1-{LOCAL_EMBEDDING_DIMENSIONS}d"
SEMANTIC_TEXT_STRATEGY = "case-document-text:v2"
TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}")


def _ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def normalize_semantic_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(_ascii_fold(str(value)).lower().split())


def compose_semantic_text(parts: Iterable[str | None]) -> str:
    normalized = [normalize_semantic_text(part) for part in parts]
    return " | ".join(part for part in normalized if part)


def _decimal_text(value: Decimal | float | int | str | None) -> str | None:
    if value is None:
        return None
    return normalize_semantic_text(str(value))


def build_case_document_text(
    *,
    numero_processo: str | None = None,
    uf: str | None = None,
    assunto: str | None = None,
    sub_assunto: str | None = None,
    resultado_macro: str | None = None,
    resultado_micro: str | None = None,
    valor_causa: Decimal | float | int | str | None = None,
    valor_condenacao: Decimal | float | int | str | None = None,
    alegacoes: Sequence[str] | None = None,
    pedidos: Sequence[str] | None = None,
    red_flags: Sequence[str] | None = None,
    vulnerabilidade_autor: str | None = None,
    subsidios: Mapping[str, object] | None = None,
    body_text: str | None = None,
) -> str:
    subsidios = subsidios or {}
    subsidios_tokens = [
        key.replace("_", " ")
        for key, value in subsidios.items()
        if value not in (None, False, "", [], {})
    ]
    return compose_semantic_text(
        [
            f"processo {numero_processo}" if numero_processo else None,
            f"uf {uf}" if uf else None,
            f"assunto {assunto}" if assunto else None,
            f"sub assunto {sub_assunto}" if sub_assunto else None,
            f"resultado macro {resultado_macro}" if resultado_macro else None,
            f"resultado micro {resultado_micro}" if resultado_micro else None,
            f"valor causa {_decimal_text(valor_causa)}" if valor_causa is not None else None,
            f"valor condenacao {_decimal_text(valor_condenacao)}" if valor_condenacao is not None else None,
            f"alegacoes {' '.join(alegacoes)}" if alegacoes else None,
            f"pedidos {' '.join(pedidos)}" if pedidos else None,
            f"red flags {' '.join(red_flags)}" if red_flags else None,
            f"vulnerabilidade {vulnerabilidade_autor}" if vulnerabilidade_autor else None,
            f"subsidios {' '.join(subsidios_tokens)}" if subsidios_tokens else None,
            body_text,
        ]
    )


def build_runtime_case_text(
    *,
    numero_processo: str | None = None,
    uf: str | None = None,
    assunto: str | None = None,
    sub_assunto: str | None = None,
    valor_causa: Decimal | float | int | str | None = None,
    alegacoes: Sequence[str] | None = None,
    pedidos: Sequence[str] | None = None,
    red_flags: Sequence[str] | None = None,
    vulnerabilidade_autor: str | None = None,
    subsidios: Mapping[str, object] | None = None,
    case_text: str | None = None,
) -> str:
    return build_case_document_text(
        numero_processo=numero_processo,
        uf=uf,
        assunto=assunto,
        sub_assunto=sub_assunto,
        valor_causa=valor_causa,
        alegacoes=alegacoes,
        pedidos=pedidos,
        red_flags=red_flags,
        vulnerabilidade_autor=vulnerabilidade_autor,
        subsidios=subsidios,
        body_text=case_text,
    )


def _hash_feature(feature: str, dimensions: int) -> tuple[int, float]:
    digest = hashlib.sha256(feature.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % dimensions
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return bucket, sign


def _feature_stream(text: str) -> Iterable[tuple[str, float]]:
    tokens = TOKEN_PATTERN.findall(normalize_semantic_text(text))
    for token in tokens:
        yield f"tok:{token}", 1.0 + min(len(token), 12) / 12.0

    for index in range(len(tokens) - 1):
        yield f"bi:{tokens[index]}::{tokens[index + 1]}", 0.65

    for token in tokens:
        if len(token) < 5:
            continue
        for start in range(len(token) - 2):
            yield f"tri:{token[start:start + 3]}", 0.18


def normalize_embedding_array(vector: np.ndarray) -> np.ndarray:
    normalized = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(normalized))
    if norm > 0:
        normalized = normalized / norm
    return normalized.astype(np.float32)


def build_local_embedding(text: str, dimensions: int = LOCAL_EMBEDDING_DIMENSIONS) -> np.ndarray:
    vector = np.zeros(dimensions, dtype=np.float32)
    normalized_text = normalize_semantic_text(text)
    if not normalized_text:
        return vector

    feature_count = 0
    for feature, weight in _feature_stream(normalized_text):
        bucket, sign = _hash_feature(feature, dimensions)
        vector[bucket] += np.float32(sign * weight)
        feature_count += 1

    if feature_count == 0:
        return vector
    return normalize_embedding_array(vector)


def build_local_embedding_list(text: str, dimensions: int = LOCAL_EMBEDDING_DIMENSIONS) -> list[float]:
    return build_local_embedding(text, dimensions=dimensions).tolist()
