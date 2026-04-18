from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "apply_recommendation_payload": ("app.services.recommendation_pipeline", "apply_recommendation_payload"),
    "analyze_case_documents": ("app.services.extractor", "analyze_case_documents"),
    "apply_analysis_to_case": ("app.services.case_maintenance", "apply_analysis_to_case"),
    "build_recommendation_payload": ("app.services.decision_engine", "build_recommendation_payload"),
    "build_recommendation_for_case": ("app.services.recommendation_pipeline", "build_recommendation_for_case"),
    "case_snapshot": ("app.services.recommendation_pipeline", "case_snapshot"),
    "canonical_case_directory": ("app.services.case_maintenance", "canonical_case_directory"),
    "derive_case_status": ("app.services.recommendation_pipeline", "derive_case_status"),
    "extract_text_from_pdf": ("app.services.extractor", "extract_text_from_pdf"),
    "extract_texts_from_paths": ("app.services.extractor", "extract_texts_from_paths"),
    "generate_recommendation_justification": ("app.services.justifier", "generate_recommendation_justification"),
    "list_case_document_paths": ("app.services.case_maintenance", "list_case_document_paths"),
    "load_policy": ("app.services.policy", "load_policy"),
    "review_recommendation_with_judge": ("app.services.judge", "review_recommendation_with_judge"),
    "sanitize_cases": ("app.services.case_sanitizer", "sanitize_cases"),
    "sync_case_status": ("app.services.recommendation_pipeline", "sync_case_status"),
    "upsert_case_recommendation": ("app.services.case_maintenance", "upsert_case_recommendation"),
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted([*globals().keys(), *__all__])
