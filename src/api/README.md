# API

Backend scaffold do projeto em FastAPI com SQLite e SQLAlchemy.

## Comandos

```bash
../../.tools/uv/bin/uv python install 3.12
../../.tools/uv/bin/uv sync --frozen --python 3.12
../../.tools/uv/bin/uv run --python 3.12 uvicorn app.main:app --reload
docker compose up --build api
```

## Estrutura

- `app/main.py`: inicialização da API e criação das tabelas.
- `app/db.py`: engine, sessão e bootstrap do SQLite.
- `app/models/`: tabelas `cases`, `recommendations` e `outcomes`.
- `app/schemas/`: contratos Pydantic iniciais.
