# Changelog

## Responsável

- `pedrocaete`

## Sprint 0 — P1 concluído

- Estruturado o backend em `src/api/`.
- Criado `pyproject.toml` com dependências do Sprint 0: `fastapi`, `sqlalchemy`, `pdfplumber`, `openai`, `duckdb`, `faiss-cpu`, `numpy` e `uvicorn`.
- Gerado `uv.lock` para travar versões e manter o ambiente reproduzível.
- Adicionado bootstrap inicial com FastAPI e configuração por ambiente.
- Criado setup de SQLite para desenvolvimento.
- Modeladas as tabelas iniciais `cases`, `recommendations` e `outcomes`.

## Infra adicional — containerização

- Adicionado `Dockerfile` em `src/api/`.
- Adicionado `compose.yaml` na raiz do projeto.
- Configurado volume para persistência do banco SQLite em `src/api/data/`.
- Montado `arquivos_adicionais/` como leitura apenas no container.
- Validado build da imagem e inicialização da API em container.
- Subida validada na porta `8000`.

## Verificações executadas

- Lock de dependências com `uv`.
- Compilação dos arquivos Python do backend.
- Build do container com `docker compose build api`.
- Health check da aplicação com backend SQLite ativo.
