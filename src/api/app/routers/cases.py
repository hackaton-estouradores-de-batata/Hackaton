from datetime import date
from decimal import Decimal
from pathlib import Path
import re
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.schemas.case import CaseIngestResponse, CaseRead
from app.services import analyze_case_documents, build_recommendation_payload, load_policy

router = APIRouter(prefix="/api/cases", tags=["cases"])


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
    case.status = "analyzed"


def _upsert_recommendation(db: Session, case: Case, analysis: dict[str, Any]) -> Recommendation:
    policy = load_policy()
    recommendation_payload = build_recommendation_payload(
        {
            "valor_causa": case.valor_causa,
            "valor_pedido_danos_morais": case.valor_pedido_danos_morais,
            "red_flags": case.red_flags,
            "vulnerabilidade_autor": case.vulnerabilidade_autor,
            "indicio_fraude": case.indicio_fraude,
            "forca_narrativa_autor": case.forca_narrativa_autor,
            "subsidios": case.subsidios,
        },
        policy,
    )

    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.case_id == case.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
    if recommendation is None:
        recommendation = Recommendation(case_id=case.id, **recommendation_payload)
        db.add(recommendation)
        return recommendation

    for key, value in recommendation_payload.items():
        setattr(recommendation, key, value)
    return recommendation


@router.get("", response_model=list[CaseRead])
def list_cases(db: Session = Depends(get_db)) -> list[Case]:
    return [_normalize_case(case) for case in db.query(Case).order_by(Case.created_at.desc()).all()]


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: str, db: Session = Depends(get_db)) -> Case:
    return _normalize_case(_get_case_or_404(db, case_id))


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
    _upsert_recommendation(db, case, analysis)
    db.commit()

    return CaseIngestResponse(
        id=case.id,
        status=case.status,
        source_folder=case.source_folder,
        autos_count=autos_count,
        subsidios_count=subsidios_count,
    )
