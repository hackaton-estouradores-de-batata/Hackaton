from __future__ import annotations

from typing import Any
from unittest.mock import patch

from app.db import SessionLocal
from app.models.case import Case
from app.services.case_maintenance import (
    apply_analysis_to_case,
    canonical_case_directory,
    list_case_document_paths,
    upsert_case_recommendation,
)
from app.services.case_normalization import normalize_case_record
from app.services.extractor import analyze_case_documents


def _analyze_case_documents(
    autos_paths,
    subsidios_paths,
    *,
    allow_llm: bool,
) -> dict[str, object]:
    if allow_llm:
        return analyze_case_documents(autos_paths, subsidios_paths)

    with patch("app.llm.client.chat_json_prompt", return_value=None), patch(
        "app.llm.client.get_openai_client",
        return_value=None,
    ):
        return analyze_case_documents(autos_paths, subsidios_paths)


def repair_case(case: Case, *, allow_llm: bool) -> dict[str, object]:
    before = {
        "status": case.status,
        "source_folder": case.source_folder,
        "uf": case.uf,
        "assunto": case.assunto,
        "sub_assunto": case.sub_assunto,
        "embedding_source": getattr(case, "embedding_source", None),
    }

    normalize_case_record(case)
    canonical_dir = canonical_case_directory(case)
    case.source_folder = str(canonical_dir)
    autos_paths, subsidios_paths = list_case_document_paths(case)
    reanalyzed = False

    if autos_paths or subsidios_paths:
        analysis = _analyze_case_documents(autos_paths, subsidios_paths, allow_llm=allow_llm)
        apply_analysis_to_case(case, analysis)
        reanalyzed = True

    return {
        "before": before,
        "autos_count": len(autos_paths),
        "subsidios_count": len(subsidios_paths),
        "reanalyzed": reanalyzed,
    }


def sanitize_cases(
    *,
    case_id: str | None = None,
    allow_llm: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(Case).order_by(Case.created_at.asc())
        if case_id:
            query = query.filter(Case.id == case_id)
        cases = query.all()

        summary: list[dict[str, object]] = []
        for case in cases:
            result = repair_case(case, allow_llm=allow_llm)
            upsert_case_recommendation(db, case)
            after = {
                "status": case.status,
                "source_folder": case.source_folder,
                "uf": case.uf,
                "assunto": case.assunto,
                "sub_assunto": case.sub_assunto,
                "embedding_source": getattr(case, "embedding_source", None),
            }
            changed = {
                key: {"before": result["before"].get(key), "after": after.get(key)}
                for key in result["before"]
                if result["before"].get(key) != after.get(key)
            }
            summary.append({"case_id": case.id, **after, **result, "changed": changed})

        if dry_run:
            db.rollback()
        else:
            db.commit()

        return {
            "total_cases": len(summary),
            "dry_run": dry_run,
            "use_llm": allow_llm,
            "updated_cases": summary,
        }
    finally:
        db.close()
