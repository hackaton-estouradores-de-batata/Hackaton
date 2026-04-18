from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models.case import Case
from app.schemas.case import CaseDocumentRead, CaseIngestResponse, CaseRead
from app.services.case_normalization import normalize_case_record
from app.services import (
    analyze_case_documents,
    apply_analysis_to_case,
    canonical_case_directory,
    upsert_case_recommendation,
)

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


def _get_case_directory(case: Case) -> Path:
    case_dir = canonical_case_directory(case)
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
    return normalize_case_record(case)


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
def get_case_document(
    case_id: str,
    document_name: str,
    download: bool = False,
    db: Session = Depends(get_db),
) -> FileResponse:
    case = _get_case_or_404(db, case_id)
    document_path = _resolve_case_document(case, document_name)
    return FileResponse(
        document_path,
        media_type="application/pdf",
        filename=document_path.name,
        content_disposition_type="attachment" if download else "inline",
    )


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
        id=str(uuid4()),
        numero_processo=numero_processo,
        valor_causa=valor_causa,
        autor_nome=autor_nome,
        autor_cpf=autor_cpf,
        status="pending",
    )
    db.add(case)
    db.commit()

    storage_root = Path(get_settings().case_storage_dir)
    case_dir = storage_root / f"case_{case.id}"

    autos_count = _persist_uploads(autos, case_dir / "autos")
    subsidios_count = _persist_uploads(subsidios, case_dir / "subsidios")

    case.source_folder = str(case_dir)
    db.commit()

    analysis = analyze_case_documents(
        sorted((case_dir / "autos").glob("*.pdf")),
        sorted((case_dir / "subsidios").glob("*.pdf")),
    )
    apply_analysis_to_case(case, analysis)
    upsert_case_recommendation(db, case)
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
