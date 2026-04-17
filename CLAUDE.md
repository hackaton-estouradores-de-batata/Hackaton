# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

- The implemented code is currently concentrated in `src/api/`, a FastAPI backend scaffold for the hackathon MVP.
- Repository-level product and target-architecture context lives in `README.md`, `PROJECT_SKELETON.md`, and `TEAM.md`.
- `AGENTS.md` is outdated: it describes the repo as documentation-only, but the backend scaffold, Docker setup, and SQLite bootstrap already exist.

## Common commands

### Backend setup and local run

From `src/api/`:

```bash
../../.tools/uv/bin/uv python install 3.12
../../.tools/uv/bin/uv sync --frozen --python 3.12
../../.tools/uv/bin/uv run --python 3.12 uvicorn app.main:app --reload
```

### Run with Docker

From the repository root:

```bash
docker compose up --build api
```

The API is exposed on `http://localhost:${API_PORT:-8000}`.

### Tests

From `src/api/`:

```bash
../../.tools/uv/bin/uv run --python 3.12 pytest
../../.tools/uv/bin/uv run --python 3.12 pytest path/to/test_file.py
../../.tools/uv/bin/uv run --python 3.12 pytest path/to/test_file.py -k test_name
```

There is a pytest dependency configured in `src/api/pyproject.toml`, but the repository currently does not include committed test files.

### Useful validation commands

From `src/api/`:

```bash
../../.tools/uv/bin/uv run --python 3.12 python -m compileall app
```

From the repository root:

```bash
docker compose build api
```

## Architecture overview

### Product shape

This project is a legal-tech recommendation system for loan-contract dispute cases. The intended end-to-end flow, described across `README.md` and `PROJECT_SKELETON.md`, is:

1. ingest process PDFs and bank supporting documents;
2. extract structured case data with LLM assistance;
3. apply a hybrid decision policy (rules + statistical signals + LLM review);
4. recommend either defense or settlement, optionally with a suggested value range;
5. record the lawyer's final decision and downstream outcome;
6. surface adherence/effectiveness metrics in a bank-facing dashboard.

The current implementation only covers the backend foundation for that flow.

### Implemented backend structure

`src/api/app/main.py` creates the FastAPI app, wires the lifespan hook, and creates tables on startup. `src/api/app/routers/health.py` exposes the currently implemented routes: `/` and `/healthz`.

`src/api/app/core/config.py` centralizes environment-backed settings via `pydantic-settings`. The active settings today are:

- `APP_ENV`
- `DATABASE_URL`
- `OPENAI_API_KEY`

`src/api/app/db.py` builds the SQLAlchemy engine and session factory. For SQLite URLs it also creates the parent directory automatically before the engine is initialized. Default development storage is `src/api/data/app.db` when running through the backend README commands, or `/app/data/app.db` inside Docker.

### Current data model

The domain foundation is already encoded in SQLAlchemy models under `src/api/app/models/`:

- `Case`: top-level judicial case metadata, workflow status, and `source_folder` pointer for ingested documents.
- `Recommendation`: the generated strategy recommendation for a case, including decision, optional settlement range, confidence, justification, and policy version.
- `Outcome`: what the lawyer actually did after reviewing a recommendation, including whether they followed it and the negotiated or judicial result.

Relationships are already wired so one case can own many recommendations and outcomes.

### Planned architecture not yet implemented

`PROJECT_SKELETON.md` and `TEAM.md` describe the intended next layers. Treat them as roadmap context, not current code:

- `src/web/` Next.js frontend for lawyer inbox/case review and bank dashboard.
- Additional FastAPI routers for cases, recommendations, outcomes, and metrics.
- Service layer for PDF extraction, decision engine, value estimation, judge/justification, and policy loading.
- Historical analytics using DuckDB plus semantic retrieval using embeddings/FAISS.
- Versioned agreement policy in `policy/acordos_v1.yaml` so legal/business rules stay editable outside application code.

When implementing new features, prefer aligning with that split: routers orchestrate, services hold domain logic, models/schemas define persisted and API shapes.

## Data and runtime context

- `arquivos_adicionais/` contains the example legal case materials used by the project; the Docker setup mounts this directory read-only into the API container.
- `.env.example` documents the expected root-level environment variables.
- `compose.yaml` mounts only `src/api/app`, `src/api/data`, and `arquivos_adicionais/`, so changes outside those paths will not automatically reflect inside the running API container.

## Guidance from existing repo docs

- Prefer Portuguese for product/legal content; the repository documentation and domain language are written in Portuguese.
- Preserve the existing numbered filenames in `arquivos_adicionais/`; they encode document order for each case.
- If you touch repository guidance, update or replace `AGENTS.md` assumptions that still describe the repository as docs-only.
