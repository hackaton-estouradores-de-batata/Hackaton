from .historical import (
    HistoricalCase,
    HistoricalCaseMatch,
    SimilarCasesStats,
    casos_similares,
    load_historical_cases,
    load_semantic_index_metadata,
    stats_similares,
    summarize_case_history,
    summarize_mock_file,
)
from .metrics import describe_metrics_stub
from .semantic import (
    LOCAL_EMBEDDING_DIMENSIONS,
    build_case_document_text,
    build_local_embedding,
    build_local_embedding_list,
    compose_semantic_text,
    normalize_embedding_array,
    normalize_semantic_text,
)

__all__ = [
    "HistoricalCase",
    "HistoricalCaseMatch",
    "SimilarCasesStats",
    "casos_similares",
    "load_historical_cases",
    "load_semantic_index_metadata",
    "stats_similares",
    "summarize_case_history",
    "summarize_mock_file",
    "describe_metrics_stub",
    "LOCAL_EMBEDDING_DIMENSIONS",
    "build_case_document_text",
    "build_local_embedding",
    "build_local_embedding_list",
    "compose_semantic_text",
    "normalize_embedding_array",
    "normalize_semantic_text",
]
