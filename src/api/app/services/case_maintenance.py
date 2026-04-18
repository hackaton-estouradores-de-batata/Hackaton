from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.services.case_normalization import (
    coerce_float,
    coerce_list,
    coerce_subsidios,
    coerce_vulnerabilidade,
    normalize_case_record,
)
from app.services.recommendation_pipeline import (
    apply_recommendation_payload,
    build_recommendation_for_case,
    sync_case_status,
)

RECOMMENDATION_HISTORY_TOP_K = 10
TERMINAL_CASE_STATUSES = {"decided", "closed"}


def canonical_case_directory(case: Case) -> Path:
    storage_root = Path(get_settings().case_storage_dir)
    preferred = storage_root / f"case_{case.id}"
    if preferred.exists():
        return preferred

    current = Path(case.source_folder) if case.source_folder else preferred
    if current.exists():
        return current
    return preferred


def list_case_document_paths(case: Case) -> tuple[list[Path], list[Path]]:
    case_dir = canonical_case_directory(case)
    autos = sorted((case_dir / "autos").glob("*.pdf"))
    subsidios = sorted((case_dir / "subsidios").glob("*.pdf"))
    return autos, subsidios


def _to_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))

    cleaned = re.sub(r"[^\d,\.\-]", "", str(value))
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        decimals = cleaned.rsplit(",", 1)[-1]
        if len(decimals) <= 2:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")

    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except Exception:
        return None


def _to_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            if fmt == "%Y-%m-%d":
                return date.fromisoformat(str(value))
            return date.fromisoformat(
                f"{str(value)[6:10]}-{str(value)[3:5]}-{str(value)[0:2]}"
            )
        except Exception:
            continue
    return None


def apply_analysis_to_case(case: Case, analysis: dict[str, Any]) -> Case:
    autos_data = analysis["autos_data"]
    features_data = analysis["features_data"]
    original_status = case.status

    case.numero_processo = autos_data.get("numero_processo") or case.numero_processo
    case.autor_nome = autos_data.get("autor_nome") or case.autor_nome
    case.autor_cpf = autos_data.get("autor_cpf") or case.autor_cpf
    case.valor_causa = _to_decimal(autos_data.get("valor_causa")) or case.valor_causa
    case.data_distribuicao = _to_date(autos_data.get("data_distribuicao"))
    case.alegacoes = coerce_list(autos_data.get("alegacoes"))
    case.pedidos = coerce_list(autos_data.get("pedidos"))
    case.valor_pedido_danos_morais = _to_decimal(autos_data.get("valor_danos_morais"))
    case.red_flags = coerce_list(features_data.get("red_flags"))
    case.vulnerabilidade_autor = coerce_vulnerabilidade(features_data.get("vulnerabilidade_autor"))
    case.indicio_fraude = coerce_float(features_data.get("indicio_fraude"), 0.0)
    case.forca_narrativa_autor = coerce_float(features_data.get("forca_narrativa_autor"), 0.0)
    case.inconsistencias_temporais = coerce_list(features_data.get("inconsistencias_temporais"))
    case.subsidios = coerce_subsidios(analysis["subsidios_data"])
    case.embedding = analysis["embedding"]
    case.embedding_provider = analysis.get("embedding_provider")
    case.embedding_model = analysis.get("embedding_model")
    case.embedding_dimensions = analysis.get("embedding_dimensions")
    case.embedding_source = analysis.get("embedding_source")
    case.autos_text = analysis["autos_text"]
    case.subsidios_text = analysis["subsidios_text"]
    structured_features = analysis.get("structured_features", {})
    case.uf = structured_features.get("uf")
    case.assunto = structured_features.get("assunto")
    case.sub_assunto = structured_features.get("sub_assunto")
    case.case_text = structured_features.get("case_text")
    case.source_folder = str(canonical_case_directory(case))
    case.status = original_status if original_status in TERMINAL_CASE_STATUSES else "analyzed"
    return normalize_case_record(case)


def upsert_case_recommendation(
    db: Session,
    case: Case,
    *,
    history_k: int = RECOMMENDATION_HISTORY_TOP_K,
) -> Recommendation:
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == case.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
    recommendation_payload, _ = build_recommendation_for_case(
        case,
        existing_recommendation=recommendation,
        history_k=history_k,
    )
    sync_case_status(case, recommendation_payload)

    if recommendation is None:
        recommendation = Recommendation(case_id=case.id, **recommendation_payload)
        db.add(recommendation)
        return recommendation

    return apply_recommendation_payload(recommendation, recommendation_payload)
