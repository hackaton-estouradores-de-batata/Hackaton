# Setup

## Pré-requisitos

- Docker + Docker Compose
- Chave da OpenAI

## Rodar com Docker (recomendado)

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env

# 2. Preencher a chave da OpenAI
#    Edite .env e insira: OPENAI_API_KEY=sk-...

# 3. Subir os serviços
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000
- Docs API: http://localhost:8000/docs

---

## Rodar localmente (sem Docker)

### Backend

```bash
cd src/api
../../.tools/uv/bin/uv sync --frozen --python 3.12
../../.tools/uv/bin/uv run --python 3.12 uvicorn app.main:app --reload
```

### Frontend

```bash
cd src/web
npm install
npm run dev
```

---

## Dados de exemplo

Os arquivos dos dois casos de exemplo estão em `arquivos_adicionais/` e são montados automaticamente no container da API.

## Mock (frontend sem backend)

Para rodar o frontend com dados simulados, sem precisar da API:

```bash
# Em src/web/.env.local
NEXT_PUBLIC_USE_MOCK=true
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENAI_API_KEY` | — | Chave da OpenAI (**obrigatória**) |
| `API_PORT` | `8000` | Porta do backend |
| `WEB_PORT` | `3000` | Porta do frontend |
| `DATABASE_URL` | `sqlite:////app/data/app.db` | Banco de dados |
| `APP_ENV` | `development` | Ambiente |
| `NEXT_PUBLIC_USE_MOCK` | `false` | Usar dados simulados no frontend |
