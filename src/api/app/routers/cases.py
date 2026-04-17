from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models.case import Case
from app.schemas.case import CaseIngestResponse, CaseRead

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


@router.get("", response_model=list[CaseRead])
def list_cases(db: Session = Depends(get_db)) -> list[Case]:
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: str, db: Session = Depends(get_db)) -> Case:
    return _get_case_or_404(db, case_id)


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
    db.commit()

    return CaseIngestResponse(
        id=case.id,
        status=case.status,
        source_folder=case.source_folder,
        autos_count=autos_count,
        subsidios_count=subsidios_count,
    )
