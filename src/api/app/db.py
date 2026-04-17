from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.base import Base


def _ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        return

    Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
_ensure_sqlite_directory(settings.database_url)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


SQLITE_SCHEMA_MIGRATIONS: dict[str, dict[str, str]] = {
    "cases": {
        "data_distribuicao": "DATE",
        "alegacoes": "JSON",
        "pedidos": "JSON",
        "valor_pedido_danos_morais": "NUMERIC(12, 2)",
        "red_flags": "JSON",
        "vulnerabilidade_autor": "VARCHAR(32)",
        "indicio_fraude": "FLOAT DEFAULT 0",
        "forca_narrativa_autor": "FLOAT DEFAULT 0",
        "inconsistencias_temporais": "JSON",
        "subsidios": "JSON",
        "embedding": "JSON",
        "autos_text": "TEXT",
        "subsidios_text": "TEXT",
    },
    "recommendations": {
        "regras_aplicadas": "JSON",
        "casos_similares_ids": "JSON",
        "judge_concorda": "BOOLEAN",
        "judge_observacao": "TEXT",
    },
    "outcomes": {
        "sentenca": "VARCHAR(32)",
        "custos_processuais": "NUMERIC(12, 2)",
    },
}


def ensure_sqlite_schema() -> None:
    url = make_url(settings.database_url)
    if url.get_backend_name() != "sqlite":
        return

    with engine.begin() as connection:
        for table_name, columns in SQLITE_SCHEMA_MIGRATIONS.items():
            existing = {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info('{table_name}')").fetchall()
            }
            for column_name, column_type in columns.items():
                if column_name in existing:
                    continue
                connection.exec_driver_sql(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
