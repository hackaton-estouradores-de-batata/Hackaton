from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    recommendation_id: Mapped[str | None] = mapped_column(ForeignKey("recommendations.id"), index=True)
    decisao_advogado: Mapped[str] = mapped_column(String(32), nullable=False)
    seguiu_recomendacao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    valor_proposto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    valor_acordado: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    resultado_negociacao: Mapped[str | None] = mapped_column(String(32))
    valor_condenacao: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="outcomes")
    recommendation: Mapped["Recommendation | None"] = relationship(
        "Recommendation",
        back_populates="outcomes",
    )
