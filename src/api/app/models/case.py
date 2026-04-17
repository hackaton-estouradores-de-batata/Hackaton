from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    numero_processo: Mapped[str | None] = mapped_column(String(32), index=True)
    valor_causa: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    autor_nome: Mapped[str | None] = mapped_column(String(255))
    autor_cpf: Mapped[str | None] = mapped_column(String(14), index=True)
    uf: Mapped[str | None] = mapped_column(String(2), index=True)
    assunto: Mapped[str | None] = mapped_column(String(255), index=True)
    sub_assunto: Mapped[str | None] = mapped_column(String(255), index=True)
    case_text: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    source_folder: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    outcomes: Mapped[list["Outcome"]] = relationship(
        "Outcome",
        back_populates="case",
        cascade="all, delete-orphan",
    )
