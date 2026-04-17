# Setup

## Requisitos

- Docker
- Docker Compose

## Variáveis

Crie o arquivo `.env` a partir de `.env.example`.

`OPENAI_API_KEY` é opcional para subir o sistema. Sem a chave, a API usa fallbacks heurísticos e embeddings locais para desenvolvimento e testes.

## Subir a stack

Rode tudo a partir da raiz do repositório.

```bash
docker compose build api web
docker compose up -d
docker compose ps
```

## Preparar a base histórica

Gere o índice histórico e rode a análise do CSV dentro do container `api`.

```bash
docker compose run --rm -v "$PWD:/workspace" api python /workspace/scripts/build_embeddings.py --provider local
docker compose run --rm -v "$PWD:/workspace" api python /workspace/scripts/analyze_historical.py
```

Se quiser gerar embeddings reais com a OpenAI:

```bash
docker compose run --rm -v "$PWD:/workspace" api python /workspace/scripts/build_embeddings.py --provider openai
```

## Smoke tests

Execute os smoke tests da API dentro do container:

```bash
docker compose exec api python - <<'PY'
import runpy
namespace = runpy.run_path('/app/tests/test_smoke.py')
for name in sorted(key for key in namespace if key.startswith('test_')):
    namespace[name]()
    print(f'{name}: ok')
PY
```

## Validação básica

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/api/cases
curl -I http://127.0.0.1:3000/inbox
```

## Teste fim a fim

Ingestão de um caso exemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/cases \
  -F numero_processo=0654321-09.2024.8.04.0001 \
  -F valor_causa=25000 \
  -F autor_nome='Jose Raimundo Oliveira Costa' \
  -F autos_files=@'arquivos_adicionais/Caso_02_0654321-09-2024-8-04-0001/01_Autos_Processo_0654321-09-2024-8-04-0001.pdf' \
  -F subsidios_files=@'arquivos_adicionais/Caso_02_0654321-09-2024-8-04-0001/02_Comprovante_de_Credito_BACEN.pdf' \
  -F subsidios_files=@'arquivos_adicionais/Caso_02_0654321-09-2024-8-04-0001/03_Demonstrativo_Evolucao_Divida.pdf' \
  -F subsidios_files=@'arquivos_adicionais/Caso_02_0654321-09-2024-8-04-0001/04_Laudo_Referenciado.pdf'
```

Depois consulte a recomendação:

```bash
curl http://127.0.0.1:8000/api/cases/<CASE_ID>/recommendation
```

## Encerrar

```bash
docker compose down
```
