# Setup

## Requisitos

- Docker
- Docker Compose

## Variaveis

Copie `.env.example` para `.env` e ajuste se necessario.

## Subir a stack

```bash
docker compose build api web
docker compose up -d
docker compose ps
```

## Desenvolvimento com Docker

O serviço `web` roda em modo desenvolvimento com hot reload e ferramentas de dev instaladas no contêiner.

```bash
# acompanhar logs do frontend
docker compose logs -f web

# rodar lint dentro do contêiner
docker compose exec web npm run lint

# abrir shell no frontend
docker compose exec web sh
```

## Testes basicos

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/api/cases
curl -I http://127.0.0.1:3000/inbox
```

## Ingestao de um caso exemplo

```bash
curl -X POST http://127.0.0.1:8000/api/cases \
  -F numero_processo=0801234-56.2024.8.10.0001 \
  -F valor_causa=15000 \
  -F autor_nome='Maria Aparecida Silva' \
  -F autos_files=@'arquivos_adicionais/Caso_01_0801234-56-2024-8-10-0001/01_Autos_Processo_0801234-56-2024-8-10-0001.pdf' \
  -F subsidios_files=@'arquivos_adicionais/Caso_01_0801234-56-2024-8-10-0001/02_Contrato_502348719.pdf'
```
