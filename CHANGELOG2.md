# Changelog

## 2026-04-17

### Sprints 0 a 3 concluídas

- Sprint 0 concluída com `src/web/`, `src/api/`, `compose.yaml`, `Dockerfile`s e script de conversão `xlsx -> csv`.
- Sprint 1 concluída com ingestão `POST /api/cases`, extração de PDFs via `pdfplumber`, extração estruturada com fallback heurístico, features ricas, embeddings e persistência no banco.
- Sprint 2 concluída com:
  - `scripts/analyze_historical.py`
  - geração de embeddings do histórico em `data/embeddings.npy`
  - índice FAISS real em `data/embeddings.faiss`
  - metadados consolidados em `data/embeddings_metadata.json`
  - retrieval híbrido em `src/api/app/analytics/historical.py`
  - views DuckDB para `taxa_vitoria_por_faixa` e `valor_condenacao_medio_por_faixa`
- Sprint 3 concluída com:
  - `policy/acordos_v1.yaml`
  - `decision_engine.py`
  - `value_estimator.py`
  - `judge.py`
  - `justifier.py`
  - pipeline unificado de recommendation
  - status `needs_review`

### Documentação consolidada

- `PROJECT_SKELETON.md` atualizado para refletir as tarefas concluídas das Sprints 0, 1, 2 e 3.
- `SETUP.md` simplificado para fluxo exclusivamente via Docker, incluindo build, preparação do histórico, smoke tests e teste fim a fim.
- Mantido apenas `CHANGELOG.md` como arquivo oficial de histórico.

### Validações executadas

- `docker compose run --rm -v "$PWD:/workspace" api python /workspace/scripts/build_embeddings.py --provider local`
- `docker compose run --rm -v "$PWD:/workspace" api python /workspace/scripts/analyze_historical.py`
- smoke tests da API executados dentro do container `api`
- ingestão real de caso exemplo e consulta de recommendation via HTTP

### Em aberto

- Sprint 4 segue parcial.
- Sprints 5, 6 e 7 ainda não foram concluídas.
