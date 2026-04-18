# Docker

Este documento explica como o Docker está configurado neste repositório e como ele deve ser usado no dia a dia de desenvolvimento.

## Visão geral

A stack local é orquestrada por `compose.yaml` e sobe dois serviços:

- `api`: backend FastAPI
- `web`: frontend Next.js

Além disso, existem dois Dockerfiles principais:

- `src/api/Dockerfile`
- `src/web/Dockerfile`

O backend usa um contêiner voltado para execução da API. O frontend usa um Dockerfile multi-stage, e o `compose.yaml` seleciona o estágio `dev`, então o `web` roda em modo de desenvolvimento dentro do contêiner.

## Como a stack funciona

### Serviço `api`

O serviço `api`:

- faz build a partir de `src/api/Dockerfile`
- monta o diretório `./src/api` em `/app`
- roda `uvicorn main:app --reload`
- expõe a porta `8000`
- usa o banco SQLite em `data/app.db` via mount em `/workspace/data`
- lê a política em `src/policy/acordos_v1.yaml` via mount em `/workspace/src/policy`
- recebe os arquivos de exemplo por mount read-only em `/workspace/arquivos_adicionais`

Na prática, isso significa que alterações no código do backend são refletidas no contêiner e o reload da API acontece automaticamente.

### Serviço `web`

O serviço `web`:

- faz build a partir de `src/web/Dockerfile`
- usa o target `dev`
- monta `./src/web` em `/app`
- roda `npm run dev -- --hostname 0.0.0.0 --port 3000`
- expõe a porta `3000`
- conversa com a API usando `API_INTERNAL_URL=http://api:8000`

Além do bind mount do código, ele usa dois volumes nomeados:

- `web_node_modules:/app/node_modules`
- `web_next:/app/.next`

Esses volumes existem para que:

- você não dependa de `node_modules` no host para usar Docker
- as dependências do frontend fiquem dentro do ambiente Docker
- o cache/build do Next fique persistido entre reinícios do contêiner

## Pré-requisitos

Antes de usar a stack com Docker, tenha:

- Docker
- Docker Compose

Também é esperado que exista um arquivo `.env` na raiz do projeto.

Exemplo:

```bash
cp .env.example .env
```

Depois ajuste as variáveis necessárias.

## Variáveis importantes

As variáveis mais relevantes para o uso com Docker são:

- `APP_ENV`
- `DATABASE_URL`
- `CASE_STORAGE_DIR`
- `POLICY_PATH`
- `API_PORT`
- `WEB_PORT`
- `OPENAI_API_KEY`

### Sobre `OPENAI_API_KEY`

A chave da OpenAI **não fica no `compose.yaml`**.

Isso é intencional, para evitar exposição acidental em comandos como `docker compose config`.
A aplicação lê essa variável a partir do `.env` por conta própria.

## Fluxo básico de uso

### Subir tudo com build

```bash
docker compose up --build
```

Use esse comando quando:

- for a primeira vez rodando a stack
- você alterar Dockerfiles
- você quiser forçar rebuild das imagens

### Subir em background

```bash
docker compose up -d
```

### Ver o estado dos serviços

```bash
docker compose ps
```

### Derrubar a stack

```bash
docker compose down
```

### Derrubar a stack e remover volumes nomeados do frontend

```bash
docker compose down -v
```

Esse comando remove, por exemplo:

- `web_node_modules`
- `web_next`

Use isso quando quiser limpar completamente o ambiente do frontend no Docker.

## Desenvolvimento do frontend com Docker

O fluxo esperado para o frontend é este:

1. editar arquivos localmente em `src/web`
2. deixar o contêiner `web` rodando
3. deixar o Next recarregar automaticamente dentro do contêiner

### O que acontece quando você edita arquivos

Como `./src/web` está montado em `/app`, o código editado no host aparece imediatamente dentro do contêiner.
Como o comando do serviço `web` é `npm run dev`, o Next detecta as mudanças e faz hot reload.

### O que você não precisa fazer no host

Se você estiver usando Docker como fluxo principal, não precisa depender de:

```bash
cd src/web
npm install
npm run dev
```

O fluxo Docker já cuida disso no contêiner.

### Comandos úteis do frontend

Ver logs:

```bash
docker compose logs -f web
```

Rodar lint dentro do contêiner:

```bash
docker compose exec web npm run lint
```

Abrir shell no contêiner:

```bash
docker compose exec web sh
```

Rebuildar só o frontend:

```bash
docker compose build web
```

Subir só o frontend:

```bash
docker compose up -d web
```

## Desenvolvimento do backend com Docker

O fluxo esperado para o backend é parecido:

1. editar arquivos localmente em `src/api`
2. deixar o contêiner `api` rodando
3. deixar o `uvicorn --reload` reiniciar a aplicação automaticamente

### Comandos úteis do backend

Ver logs:

```bash
docker compose logs -f api
```

Abrir shell no contêiner:

```bash
docker compose exec api sh
```

Rodar testes:

```bash
docker compose exec api python -m pytest
```

Validar importação/compilação:

```bash
docker compose exec api python -m compileall app
```

Rebuildar só a API:

```bash
docker compose build api
```

Subir só a API:

```bash
docker compose up -d api
```

## Mounts e volumes em detalhe

### Backend

No serviço `api`, os mounts atuais são:

- `./src/api:/app`
- `./data:/workspace/data`
- `./src/policy:/workspace/src/policy`
- `./arquivos_adicionais:/workspace/arquivos_adicionais:ro`

Isso significa:

- o código da API vem do diretório local `src/api`
- o banco SQLite e outros dados ficam em `data/`
- a política carregada pelo backend vem de `src/policy/`
- os arquivos jurídicos de exemplo entram apenas para leitura

### Frontend

No serviço `web`, os mounts e volumes atuais são:

- `./src/web:/app`
- `web_node_modules:/app/node_modules`
- `web_next:/app/.next`

Isso significa:

- o código do frontend vem do diretório local `src/web`
- as dependências instaladas pelo Node ficam armazenadas dentro de um volume Docker
- o diretório `.next` não depende do host

## Integração do frontend

O frontend conversa diretamente com a API da stack Docker via `API_INTERNAL_URL=http://api:8000`.

No navegador, as rotas `/api/*` continuam acessíveis pelo próprio host do Next.js e são
redirecionadas internamente para o backend.

## Comandos úteis no dia a dia

Subir tudo:

```bash
docker compose up --build
```

Ver containers:

```bash
docker compose ps
```

Ver logs da API:

```bash
docker compose logs -f api
```

Ver logs do frontend:

```bash
docker compose logs -f web
```

Rodar lint do frontend:

```bash
docker compose exec web npm run lint
```

Abrir shell no frontend:

```bash
docker compose exec web sh
```

Abrir shell na API:

```bash
docker compose exec api sh
```

Parar tudo:

```bash
docker compose down
```

## Troubleshooting

### O frontend sobe, mas o lint falha

Rode o lint dentro do contêiner `web`:

```bash
docker compose exec web npm run lint
```

Se necessário, rebuild:

```bash
docker compose build web
```

### O frontend não refletiu a mudança

Verifique:

- se o contêiner `web` está rodando
- se você editou arquivos em `src/web`
- se há logs do Next acusando erro

Comandos úteis:

```bash
docker compose ps
docker compose logs -f web
```

### A API não sobe

Cheque os logs:

```bash
docker compose logs -f api
```

Cheque também o healthcheck e os mounts de `data/` e `src/policy/`.

### Quero limpar o ambiente do frontend no Docker

```bash
docker compose down -v
docker compose up --build
```

### Quero rebuildar sem cache

```bash
docker compose build --no-cache
```

ou apenas um serviço:

```bash
docker compose build --no-cache web
docker compose build --no-cache api
```

## Resumo prático

Se você for usar Docker como fluxo principal, o caminho normal é:

```bash
cp .env.example .env
docker compose up --build
docker compose logs -f web
docker compose exec web npm run lint
```

E, no dia a dia:

- edite `src/web` para frontend
- edite `src/api` para backend
- use `docker compose exec` para rodar comandos dentro dos contêineres
- use `docker compose logs -f` para acompanhar o que está acontecendo
