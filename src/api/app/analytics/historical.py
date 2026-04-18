from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

import numpy as np

try:
    import faiss
except Exception:  # pragma: no cover - import guard for non-runtime tooling
    faiss = None

from app.analytics.semantic import (
    LOCAL_EMBEDDING_DIMENSIONS,
    LOCAL_EMBEDDING_MODEL,
    SEMANTIC_TEXT_STRATEGY,
    build_local_embedding,
    build_runtime_case_text,
    normalize_embedding_array,
)
from app.core.config import get_settings
from app.models.case import Case

UF_COLUMN = "UF"
ASSUNTO_COLUMN = "Assunto"
SUBASSUNTO_COLUMN = "Sub-assunto"
RESULTADO_MACRO_COLUMN = "Resultado macro"
RESULTADO_MICRO_COLUMN = "Resultado micro"
VALOR_CAUSA_COLUMN = "Valor da causa"


@dataclass(frozen=True)
class HistoricalCase:
    case_id: str
    uf: str
    assunto: str
    sub_assunto: str
    resultado_macro: str
    resultado_micro: str
    valor_causa: Decimal | None
    valor_condenacao: Decimal | None
    source_index: int


@dataclass(frozen=True)
class HistoricalCaseMatch(HistoricalCase):
    similarity_score: float


@dataclass(frozen=True)
class SimilarCasesStats:
    prob_vitoria: float
    custo_medio_defesa: Decimal
    percentil_25: Decimal
    percentil_50: Decimal


@dataclass(frozen=True)
class SemanticIndexMetadata:
    provider: str
    model: str
    dimensions: int
    row_count: int
    text_strategy: str


RESULTADOS_VITORIA = {
    "êxito",
    "exito",
    "procedente",
    "parcial procedência",
    "parcial procedencia",
}


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def parse_decimal(value: str) -> Decimal | None:
    normalized = normalize_text(value).replace(",", ".")
    if not normalized:
        return None

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _historical_csv_path() -> Path:
    settings = get_settings()
    if settings.historical_csv_path:
        return Path(settings.historical_csv_path)
    return Path(settings.case_storage_dir).expanduser().parent / "sentencas_60k.csv"


def _historical_data_dir() -> Path:
    return _historical_csv_path().parent


def _embeddings_matrix_path() -> Path:
    return _historical_data_dir() / "embeddings.npy"


def _embeddings_index_path() -> Path:
    return _historical_data_dir() / "embeddings.faiss"


def _embeddings_metadata_path() -> Path:
    return _historical_data_dir() / "embeddings_metadata.json"


@lru_cache
def _csv_columns() -> tuple[str, str]:
    csv_path = _historical_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo historico nao encontrado em {csv_path}")

    header = csv_path.open("r", encoding="utf-8", newline="").readline().strip().split(",")
    processo_column = next(name for name in header if "processo" in name.lower())
    valor_condenacao_column = next(name for name in header if "indeniza" in name.lower())
    return processo_column, valor_condenacao_column


@lru_cache
def load_historical_cases() -> tuple[HistoricalCase, ...]:
    csv_path = _historical_csv_path()
    if not csv_path.exists():
        return tuple()

    processo_column, valor_condenacao_column = _csv_columns()
    records: list[HistoricalCase] = []

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_index, row in enumerate(reader):
            records.append(
                HistoricalCase(
                    case_id=normalize_text(row[processo_column]),
                    uf=normalize_text(row[UF_COLUMN]),
                    assunto=normalize_text(row[ASSUNTO_COLUMN]),
                    sub_assunto=normalize_text(row[SUBASSUNTO_COLUMN]),
                    resultado_macro=normalize_text(row[RESULTADO_MACRO_COLUMN]),
                    resultado_micro=normalize_text(row[RESULTADO_MICRO_COLUMN]),
                    valor_causa=parse_decimal(row[VALOR_CAUSA_COLUMN]),
                    valor_condenacao=parse_decimal(row[valor_condenacao_column]),
                    source_index=row_index,
                )
            )

    return tuple(records)


def _load_legacy_metadata(raw_payload: Any, matrix: np.ndarray | None) -> SemanticIndexMetadata | None:
    if not isinstance(raw_payload, list):
        return None
    dimensions = int(matrix.shape[1]) if matrix is not None and matrix.ndim == 2 else LOCAL_EMBEDDING_DIMENSIONS
    return SemanticIndexMetadata(
        provider="legacy-local",
        model="legacy-stub-v0",
        dimensions=dimensions,
        row_count=len(raw_payload),
        text_strategy="legacy-unknown",
    )


@lru_cache
def load_semantic_index_metadata() -> SemanticIndexMetadata | None:
    metadata_path = _embeddings_metadata_path()
    matrix = load_semantic_matrix()
    if not metadata_path.exists():
        if matrix is None:
            return None
        return SemanticIndexMetadata(
            provider="local",
            model=LOCAL_EMBEDDING_MODEL,
            dimensions=int(matrix.shape[1]),
            row_count=int(matrix.shape[0]),
            text_strategy=SEMANTIC_TEXT_STRATEGY,
        )

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return SemanticIndexMetadata(
            provider=str(payload.get("provider", "local")),
            model=str(payload.get("model", LOCAL_EMBEDDING_MODEL)),
            dimensions=int(payload.get("dimensions") or (matrix.shape[1] if matrix is not None else 0)),
            row_count=int(payload.get("row_count") or (matrix.shape[0] if matrix is not None else 0)),
            text_strategy=str(payload.get("text_strategy") or SEMANTIC_TEXT_STRATEGY),
        )
    return _load_legacy_metadata(payload, matrix)


@lru_cache
def load_semantic_matrix() -> np.ndarray | None:
    matrix_path = _embeddings_matrix_path()
    if not matrix_path.exists():
        return None

    matrix = np.load(matrix_path)
    if matrix.ndim != 2:
        return None
    return np.asarray(matrix, dtype=np.float32)


@lru_cache
def load_semantic_index():
    metadata = load_semantic_index_metadata()
    if metadata is None or metadata.dimensions <= 0 or faiss is None:
        return None

    index_path = _embeddings_index_path()
    if index_path.exists():
        try:
            index = faiss.read_index(str(index_path))
            return index, metadata
        except Exception:
            pass

    matrix = load_semantic_matrix()
    if matrix is None or matrix.size == 0:
        return None

    normalized = np.vstack([normalize_embedding_array(row) for row in matrix]).astype(np.float32)
    index = faiss.IndexFlatIP(normalized.shape[1])
    index.add(normalized)
    return index, metadata


def _cause_bounds(valor_causa: Decimal | None) -> tuple[Decimal | None, Decimal | None]:
    if valor_causa is None:
        return None, None
    lower = valor_causa * Decimal("0.7")
    upper = valor_causa * Decimal("1.3")
    return lower, upper


def _value_distance(case: Case, item: HistoricalCase) -> Decimal:
    return abs((item.valor_causa or Decimal("0")) - (case.valor_causa or Decimal("0")))


def _value_similarity(case: Case, item: HistoricalCase) -> float:
    if case.valor_causa is None or item.valor_causa is None or case.valor_causa <= 0:
        return 0.0

    delta = abs(item.valor_causa - case.valor_causa)
    ratio = delta / case.valor_causa
    normalized = min(float(ratio / Decimal("0.30")), 1.0)
    return round(max(0.0, 1.0 - normalized), 4)


def _pedido_overlap_score(case: Case, item: HistoricalCase) -> float:
    pedidos = [str(pedido).strip().casefold() for pedido in (case.pedidos or []) if str(pedido).strip()]
    if not pedidos:
        return 0.0

    haystack = " ".join([item.assunto, item.sub_assunto, item.resultado_macro, item.resultado_micro]).casefold()
    hits = 0

    for pedido in pedidos:
        tokens = [token for token in pedido.replace("_", " ").split() if len(token) >= 5]
        if tokens and any(token in haystack for token in tokens):
            hits += 1

    return round(min(hits / max(len(pedidos), 1), 1.0), 4)


def _structured_similarity(case: Case, item: HistoricalCase) -> float:
    weighted_score = 0.0
    total_weight = 0.0

    if case.uf:
        total_weight += 0.20
        if item.uf.casefold() == case.uf.casefold():
            weighted_score += 0.20

    if case.assunto:
        total_weight += 0.35
        if item.assunto.casefold() == case.assunto.casefold():
            weighted_score += 0.35

    if case.sub_assunto:
        total_weight += 0.15
        if item.sub_assunto.casefold() == case.sub_assunto.casefold():
            weighted_score += 0.15

    if case.valor_causa is not None and item.valor_causa is not None:
        total_weight += 0.20
        weighted_score += 0.20 * _value_similarity(case, item)

    pedido_overlap = _pedido_overlap_score(case, item)
    if pedido_overlap:
        total_weight += 0.10
        weighted_score += 0.10 * pedido_overlap

    if total_weight == 0:
        return 0.0
    return round(weighted_score / total_weight, 4)


def _serialize_match(item: HistoricalCaseMatch) -> dict[str, object]:
    payload = asdict(item)
    for field_name in ("valor_causa", "valor_condenacao"):
        value = payload[field_name]
        payload[field_name] = str(value) if value is not None else None
    return payload


def _semantic_query_text(case: Case) -> str:
    return build_runtime_case_text(
        numero_processo=case.numero_processo,
        uf=case.uf,
        assunto=case.assunto,
        sub_assunto=case.sub_assunto,
        valor_causa=case.valor_causa,
        alegacoes=case.alegacoes,
        pedidos=case.pedidos,
        red_flags=case.red_flags,
        vulnerabilidade_autor=case.vulnerabilidade_autor,
        subsidios=case.subsidios or {},
        case_text=case.case_text,
    )


def _provider_family(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized.startswith("legacy"):
        return "local"
    if normalized.startswith("local"):
        return "local"
    if normalized.startswith("openai"):
        return "openai"
    return normalized


def _can_reuse_existing_embedding(case: Case, metadata: SemanticIndexMetadata) -> bool:
    existing_embedding = list(case.embedding or [])
    if not existing_embedding or len(existing_embedding) != metadata.dimensions:
        return False

    if getattr(case, "embedding_source", None) != metadata.text_strategy:
        return False
    if _provider_family(getattr(case, "embedding_provider", None)) != _provider_family(metadata.provider):
        return False
    if str(getattr(case, "embedding_model", "") or "") != metadata.model:
        return False
    if int(getattr(case, "embedding_dimensions", 0) or 0) != metadata.dimensions:
        return False
    return True


def _build_query_embedding(case: Case, metadata: SemanticIndexMetadata) -> np.ndarray | None:
    if _can_reuse_existing_embedding(case, metadata):
        return normalize_embedding_array(np.asarray(case.embedding, dtype=np.float32))

    semantic_text = _semantic_query_text(case)
    if not semantic_text:
        return None

    if metadata.provider.startswith("local") or metadata.provider.startswith("legacy"):
        return build_local_embedding(semantic_text, dimensions=metadata.dimensions)

    from app.llm.client import build_embedding_payload

    payload = build_embedding_payload(
        semantic_text,
        provider=metadata.provider,
        model=metadata.model,
        allow_local_fallback=False,
    )
    if payload is None:
        return None

    vector = np.asarray(payload["vector"], dtype=np.float32)
    if vector.size == metadata.dimensions:
        return normalize_embedding_array(vector)
    return None


def _normalized_semantic_score(score: float) -> float:
    normalized = (score + 1.0) / 2.0
    return round(max(0.0, min(1.0, normalized)), 4)


def _semantic_candidates(case: Case, search_k: int) -> list[tuple[HistoricalCase, float]]:
    index_bundle = load_semantic_index()
    if index_bundle is None:
        return []

    index, metadata = index_bundle
    cases = load_historical_cases()
    if not cases:
        return []

    query_vector = _build_query_embedding(case, metadata)
    if query_vector is None:
        return []

    limit = min(search_k, len(cases))
    distances, indices = index.search(np.asarray([query_vector], dtype=np.float32), limit)

    matches: list[tuple[HistoricalCase, float]] = []
    for raw_score, raw_index in zip(distances[0], indices[0], strict=False):
        candidate_index = int(raw_index)
        if candidate_index < 0 or candidate_index >= len(cases):
            continue
        matches.append((cases[candidate_index], _normalized_semantic_score(float(raw_score))))
    return matches


def casos_similares(case: Case, k: int = 50) -> list[HistoricalCaseMatch]:
    lower_bound, upper_bound = _cause_bounds(case.valor_causa)
    semantic_matches = _semantic_candidates(case, search_k=max(k * 6, 60))
    semantic_score_map = {item.source_index: score for item, score in semantic_matches}

    if semantic_matches:
        candidates = [item for item, _ in semantic_matches]
        if lower_bound is not None and upper_bound is not None:
            filtered = [
                item
                for item in candidates
                if item.valor_causa is not None and lower_bound <= item.valor_causa <= upper_bound
            ]
            if len(filtered) >= min(k, 10):
                candidates = filtered
    else:
        candidates = list(load_historical_cases())
        if lower_bound is not None and upper_bound is not None:
            filtered = [
                item
                for item in candidates
                if item.valor_causa is not None and lower_bound <= item.valor_causa <= upper_bound
            ]
            if filtered:
                candidates = filtered

    ranked: list[HistoricalCaseMatch] = []
    for item in candidates:
        structured_score = _structured_similarity(case, item)
        semantic_score = semantic_score_map.get(item.source_index)
        if semantic_score is None:
            similarity = structured_score
        else:
            similarity = round((semantic_score * 0.65) + (structured_score * 0.35), 4)

        ranked.append(
            HistoricalCaseMatch(
                **asdict(item),
                similarity_score=similarity,
            )
        )

    ordered = sorted(
        ranked,
        key=lambda item: (
            -item.similarity_score,
            _value_distance(case, item),
            item.source_index,
        ),
    )
    return ordered[:k]


def _is_victory(item: HistoricalCase) -> bool:
    macro = item.resultado_macro.casefold()
    micro = item.resultado_micro.casefold()
    return macro in RESULTADOS_VITORIA or micro in RESULTADOS_VITORIA


def _percentile(values: list[Decimal], percentile: Decimal) -> Decimal:
    if not values:
        return Decimal("0")

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    return lower_value + (upper_value - lower_value) * fraction


def stats_similares(casos: Sequence[HistoricalCase]) -> SimilarCasesStats:
    if not casos:
        return SimilarCasesStats(
            prob_vitoria=0.0,
            custo_medio_defesa=Decimal("0"),
            percentil_25=Decimal("0"),
            percentil_50=Decimal("0"),
        )

    victories = sum(1 for item in casos if _is_victory(item))
    condenacoes = [item.valor_condenacao for item in casos if item.valor_condenacao is not None]
    custo_medio = sum(condenacoes, Decimal("0")) / Decimal(len(condenacoes)) if condenacoes else Decimal("0")

    return SimilarCasesStats(
        prob_vitoria=victories / len(casos),
        custo_medio_defesa=custo_medio,
        percentil_25=_percentile(condenacoes, Decimal("0.25")),
        percentil_50=_percentile(condenacoes, Decimal("0.5")),
    )


def summarize_case_history(case: Case, k: int = 5) -> dict[str, object]:
    similares = casos_similares(case, k=k)
    stats = stats_similares(similares)
    return {
        "casos_similares_ids": [item.case_id for item in similares],
        "casos_similares": [_serialize_match(item) for item in similares],
        "total_casos_similares": len(similares),
        "stats": {
            "prob_vitoria": stats.prob_vitoria,
            "custo_medio_defesa": str(stats.custo_medio_defesa),
            "percentil_25": str(stats.percentil_25),
            "percentil_50": str(stats.percentil_50),
        },
    }


def summarize_mock_file(mock_file: Path, k: int = 5) -> dict[str, object]:
    payload = json.loads(mock_file.read_text(encoding="utf-8"))
    case = Case(
        id=payload["id"],
        numero_processo=payload.get("numero_processo"),
        valor_causa=Decimal(str(payload.get("valor_causa"))) if payload.get("valor_causa") is not None else None,
        autor_nome=payload.get("autor_nome"),
        status=payload.get("status", "analyzed"),
        alegacoes=list(payload.get("alegacoes") or []),
        pedidos=list(payload.get("pedidos") or []),
        red_flags=list(payload.get("red_flags") or []),
        vulnerabilidade_autor=payload.get("vulnerabilidade_autor"),
        indicio_fraude=float(payload.get("indicio_fraude") or 0.0),
        forca_narrativa_autor=float(payload.get("forca_narrativa_autor") or 0.0),
        subsidios=dict(payload.get("subsidios") or {}),
        case_text=build_runtime_case_text(
            numero_processo=payload.get("numero_processo"),
            valor_causa=payload.get("valor_causa"),
            alegacoes=list(payload.get("alegacoes") or []),
            pedidos=list(payload.get("pedidos") or []),
            case_text="\n".join(payload.get("alegacoes") or []),
            subsidios=dict(payload.get("subsidios") or {}),
        ),
    )
    return summarize_case_history(case, k=k)
