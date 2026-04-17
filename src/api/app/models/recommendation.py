from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    decisao: Mapped[str] = mapped_column(String(32), nullable=False)
    valor_sugerido_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    valor_sugerido_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    justificativa: Mapped[str | None] = mapped_column(Text())
    confianca: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(16), default="v1", nullable=False)
    regras_aplicadas: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    casos_similares_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    judge_concorda: Mapped[bool | None] = mapped_column(Boolean)
    judge_observacao: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="recommendations")
    outcomes: Mapped[list["Outcome"]] = relationship("Outcome", back_populates="recommendation")
