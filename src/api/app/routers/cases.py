from datetime import date
from decimal import Decimal
from pathlib import Path
import re
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.schemas.case import CaseDocumentRead, CaseIngestResponse, CaseRead
from app.services import (
    analyze_case_documents,
    apply_recommendation_payload,
    build_recommendation_for_case,
    sync_case_status,
)

router = APIRouter(prefix="/api/cases", tags=["cases"])
RECOMMENDATION_HISTORY_TOP_K = 10


def _safe_filename(filename: str | None, fallback: str) -> str:
    if not filename:
        return fallback
    return Path(filename).name or fallback


def _persist_uploads(files: list[UploadFile], target_dir: Path) -> int:
    saved = 0
    target_dir.mkdir(parents=True, exist_ok=True)

    for index, upload in enumerate(files, start=1):
        filename = _safe_filename(upload.filename, f"upload_{index}.pdf")
        destination = target_dir / f"{index:02d}_{filename}"
        payload = upload.file.read()
        destination.write_bytes(payload)
        saved += 1

    return saved


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso não encontrado.")
    return case


def _get_case_directory(case: Case) -> Path:
    if not case.source_folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso sem documentos persistidos.")
    case_dir = Path(case.source_folder)
    if not case_dir.exists() or not case_dir.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diretório de documentos não encontrado.")
    return case_dir


def _list_case_documents(case: Case) -> list[CaseDocumentRead]:
    case_dir = _get_case_directory(case)
    documents: list[CaseDocumentRead] = []

    for category in ("autos", "subsidios"):
        category_dir = case_dir / category
        if not category_dir.exists() or not category_dir.is_dir():
            continue

        for path in sorted(category_dir.glob("*.pdf")):
            documents.append(
                CaseDocumentRead(
                    name=path.name,
                    display_name=path.name.split("_", 1)[1] if "_" in path.name else path.name,
                    category=category,
                    url=f"/api/cases/{case.id}/documents/{path.name}",
                )
            )

    return documents


def _resolve_case_document(case: Case, document_name: str) -> Path:
    safe_name = Path(document_name).name
    if safe_name != document_name or not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    case_dir = _get_case_directory(case)
    for category in ("autos", "subsidios"):
        candidate = case_dir / category / safe_name
        if candidate.exists() and candidate.is_file():
            return candidate

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")


def _normalize_case(case: Case) -> Case:
    case.alegacoes = list(case.alegacoes or [])
    case.pedidos = list(case.pedidos or [])
    case.red_flags = list(case.red_flags or [])
    case.inconsistencias_temporais = list(case.inconsistencias_temporais or [])
    case.vulnerabilidade_autor = _coerce_vulnerabilidade(case.vulnerabilidade_autor)
    case.indicio_fraude = _coerce_float(case.indicio_fraude, 0.0)
    case.forca_narrativa_autor = _coerce_float(case.forca_narrativa_autor, 0.0)
    case.subsidios = _coerce_subsidios(case.subsidios)
    return case


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        chunks = [chunk.strip(" -•\n\t") for chunk in value.replace(";", "\n").splitlines()]
        return [chunk for chunk in chunks if chunk]
    return [str(value)]


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    match = re.search(r"(\d+(?:[\.,]\d+)?)", str(value))
    if match:
        return float(match.group(1).replace(",", "."))
    return default


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    lowered = str(value).strip().lower()
    return lowered in {"1", "true", "sim", "yes", "y", "presente"}


def _coerce_subsidios(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized = dict(value)
    for key in ("tem_contrato", "tem_extrato", "tem_dossie", "tem_comprovante", "assinatura_validada"):
        if key in normalized:
            normalized[key] = _coerce_bool(normalized[key])
    if "valor_emprestimo" in normalized:
        normalized["valor_emprestimo"] = _coerce_float(normalized["valor_emprestimo"], 0.0)
    return normalized


def _coerce_vulnerabilidade(value: Any) -> str:
    lowered = str(value or "").strip().lower()
    if "idos" in lowered:
        return "idoso"
    if "analfabet" in lowered:
        return "analfabeto"
    if "baixa renda" in lowered or "hipossuf" in lowered:
        return "baixa_renda"
    return "nenhuma"


def _to_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


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


def _apply_analysis_to_case(case: Case, analysis: dict[str, Any]) -> None:
    autos_data = analysis["autos_data"]
    features_data = analysis["features_data"]

    case.numero_processo = autos_data.get("numero_processo") or case.numero_processo
    case.valor_causa = _to_decimal(autos_data.get("valor_causa")) or case.valor_causa
    case.data_distribuicao = _to_date(autos_data.get("data_distribuicao"))
    case.alegacoes = _coerce_list(autos_data.get("alegacoes"))
    case.pedidos = _coerce_list(autos_data.get("pedidos"))
    case.valor_pedido_danos_morais = _to_decimal(autos_data.get("valor_danos_morais"))
    case.red_flags = _coerce_list(features_data.get("red_flags"))
    case.vulnerabilidade_autor = _coerce_vulnerabilidade(features_data.get("vulnerabilidade_autor"))
    case.indicio_fraude = _coerce_float(features_data.get("indicio_fraude"), 0.0)
    case.forca_narrativa_autor = _coerce_float(features_data.get("forca_narrativa_autor"), 0.0)
    case.inconsistencias_temporais = _coerce_list(features_data.get("inconsistencias_temporais"))
    case.subsidios = _coerce_subsidios(analysis["subsidios_data"])
    case.embedding = analysis["embedding"]
    case.autos_text = analysis["autos_text"]
    case.subsidios_text = analysis["subsidios_text"]
    structured_features = analysis.get("structured_features", {})
    case.uf = structured_features.get("uf")
    case.assunto = structured_features.get("assunto")
    case.sub_assunto = structured_features.get("sub_assunto")
    case.case_text = structured_features.get("case_text")
    case.status = "analyzed"


def _upsert_recommendation(db: Session, case: Case) -> Recommendation:
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == case.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
    recommendation_payload, _ = build_recommendation_for_case(
        case,
        existing_recommendation=recommendation,
        history_k=RECOMMENDATION_HISTORY_TOP_K,
    )
    sync_case_status(case, recommendation_payload)

    if recommendation is None:
        recommendation = Recommendation(case_id=case.id, **recommendation_payload)
        db.add(recommendation)
        return recommendation

    return apply_recommendation_payload(recommendation, recommendation_payload)


@router.get("", response_model=list[CaseRead])
def list_cases(db: Session = Depends(get_db)) -> list[Case]:
    return [_normalize_case(case) for case in db.query(Case).order_by(Case.created_at.desc()).all()]


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: str, db: Session = Depends(get_db)) -> Case:
    return _normalize_case(_get_case_or_404(db, case_id))


@router.get("/{case_id}/documents", response_model=list[CaseDocumentRead])
def list_case_documents(case_id: str, db: Session = Depends(get_db)) -> list[CaseDocumentRead]:
    case = _get_case_or_404(db, case_id)
    return _list_case_documents(case)


@router.get("/{case_id}/documents/{document_name}")
def get_case_document(case_id: str, document_name: str, db: Session = Depends(get_db)) -> FileResponse:
    case = _get_case_or_404(db, case_id)
    document_path = _resolve_case_document(case, document_name)
    return FileResponse(document_path, media_type="application/pdf", filename=document_path.name)


@router.post("", response_model=CaseIngestResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    numero_processo: str | None = Form(default=None),
    valor_causa: Decimal | None = Form(default=None),
    autor_nome: str | None = Form(default=None),
    autor_cpf: str | None = Form(default=None),
    autos_files: list[UploadFile] | None = File(default=None),
    subsidios_files: list[UploadFile] | None = File(default=None),
    db: Session = Depends(get_db),
) -> CaseIngestResponse:
    autos = autos_files or []
    subsidios = subsidios_files or []

    if not autos and not subsidios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie ao menos um PDF em autos_files ou subsidios_files.",
        )

    case = Case(
        numero_processo=numero_processo,
        valor_causa=valor_causa,
        autor_nome=autor_nome,
        autor_cpf=autor_cpf,
        status="pending",
    )
    db.add(case)
    db.flush()

    storage_root = Path(get_settings().case_storage_dir)
    case_dir = storage_root / f"case_{case.id}"

    autos_count = _persist_uploads(autos, case_dir / "autos")
    subsidios_count = _persist_uploads(subsidios, case_dir / "subsidios")

    case.source_folder = str(case_dir)
    analysis = analyze_case_documents(
        sorted((case_dir / "autos").glob("*.pdf")),
        sorted((case_dir / "subsidios").glob("*.pdf")),
    )
    _apply_analysis_to_case(case, analysis)
    _upsert_recommendation(db, case)
    db.commit()

    return CaseIngestResponse(
        id=case.id,
        status=case.status,
        source_folder=case.source_folder,
        autos_count=autos_count,
        subsidios_count=subsidios_count,
        uf=case.uf,
        assunto=case.assunto,
        sub_assunto=case.sub_assunto,
    )
