# Changelog

## 2026-04-17

### Base de avaliação

Auditoria de Sprint 0 e Sprint 1 feita usando `PROJECT_SKELETON.md` como referência principal de arquitetura, estrutura de diretórios e escopo funcional.

### Status consolidado

- Sprint 0: `parcialmente implementado`, funcionalmente forte, mas ainda não `100%` alinhado ao esqueleto.
- Sprint 1: `parcialmente implementado`, com ingestão e Docker funcionando, mas ainda longe de `100%` do pipeline descrito no esqueleto.

### Sprint 0

Implementado:

- `src/api/` existe com `FastAPI`, `SQLAlchemy`, `pdfplumber`, `openai`, `duckdb`, `faiss-cpu`, `numpy` e `uv.lock`.
- `src/web/` existe com `Next.js`, `Tailwind`, `TypeScript` e componentes `shadcn/ui`.
- `data/sentencas_60k.csv` existe.
- Schema SQLite base existe com tabelas `cases`, `recommendations` e `outcomes`.
- Mock data de 2 casos existe em `data/processos_exemplo/caso_001/mock_case.json` e `data/processos_exemplo/caso_002/mock_case.json`.

Lacunas frente ao `PROJECT_SKELETON.md`:

- O backend real está em `src/api/app/...`, enquanto o esqueleto define `src/api/main.py`, `src/api/routers/`, `src/api/services/`, `src/api/models/` e `src/api/schemas/` direto na raiz de `src/api/`.
- Ainda não existe `src/api/tests/`.
- Ainda não existe `data/README.md`.
- Ainda não existe `SETUP.md`, que faz parte da estrutura esperada do projeto.

Conclusão Sprint 0:

- Funcionalmente, o setup base existe.
- Estruturalmente, ainda não está `100%` aderente ao esqueleto.

### Sprint 1

Implementado:

- `POST /api/cases` existe e recebe multipart.
- PDFs são persistidos em disco e o caso é salvo em SQLite.
- `app/services/extractor.py` extrai texto básico com `pdfplumber`.
- `app/llm/client.py` existe.
- Prompts base existem:
  - `extract_autos.txt`
  - `extract_subsidios.txt`
  - `extract_features.txt`
- O stack sobe integralmente em Docker (`api` e `web`).
- O fluxo mínimo de UI está operacional com `GET /api/cases`, `GET /api/cases/{id}` e `POST /api/cases/{id}/outcome`.

Lacunas frente ao `PROJECT_SKELETON.md`:

- O `POST /api/cases` salva em `src/api/data/processos_exemplo/...`, mas o esqueleto define `data/processos_exemplo/...` na raiz do projeto.
- O extractor atual só concatena texto; ele ainda não separa por seção nem produz JSON estruturado.
- Os prompts existem, mas não estão conectados ao pipeline de ingestão.
- Não há extração LLM real de:
  - `numero_processo`
  - `valor_causa`
  - `alegacoes`
  - `pedidos`
  - `valor_pedido_danos_morais`
  - sinais de subsídios
  - features ricas
- Não há `embed_peticao(...)`.
- Não existe persistência de embedding.
- O modelo `Case` ainda não representa o domínio descrito no esqueleto:
  - faltam campos como `data_distribuicao`, `alegacoes`, `pedidos`, `red_flags`, `vulnerabilidade_autor`, `indicio_fraude`, `forca_narrativa_autor` e `embedding`.
- A recomendação atual é `stub`, não uma recomendação derivada do pipeline do Sprint 1.
- Ainda não existem `analytics/`, `policy/` e o motor estatístico previsto pelo esqueleto.

Conclusão Sprint 1:

- Existe um MVP operacional de ingestão e navegação.
- O pipeline descrito no esqueleto ainda não está `100%` implementado.

### Plano curto para fechar as lacunas

1. Alinhar a estrutura do backend com o `PROJECT_SKELETON.md`, removendo a divergência `src/api/app/...` versus `src/api/...`, ou formalizar essa exceção em documentação se a migração for evitada.
2. Mover o storage de ingestão para `data/processos_exemplo/` na raiz do projeto e adicionar `data/README.md`.
3. Implementar o pipeline real do Sprint 1:
   - leitura por seção
   - chamada dos prompts
   - extração estruturada
   - features ricas
   - embedding
   - persistência completa no banco
4. Expandir `Case`, `Recommendation` e schemas para refletir o modelo de domínio definido no esqueleto, eliminando o `stub` de recomendação.

### Observação

Se a referência principal continuar sendo `PROJECT_SKELETON.md`, então a resposta objetiva é:

- Sprint 0: `não está 100%`
- Sprint 1: `não está 100%`

### Atualização posterior no mesmo dia

Plano executado:

- backend alinhado ao esqueleto com wrappers root-level em `src/api/`
- `SETUP.md`, `data/README.md`, `policy/acordos_v1.yaml` e `src/api/tests/` adicionados
- runtime Docker da API ajustado para a estrutura `src/api/...`
- storage de ingestão movido para `data/processos_exemplo/` na raiz
- modelo de domínio expandido com campos de extração, features e embedding
- pipeline de ingestão passou a:
  - ler PDFs
  - extrair estrutura via LLM com fallback heurístico
  - gerar features
  - criar embedding
  - persistir recomendação não-stub

Status após implementação:

- Sprint 0: `substancialmente alinhado`
- Sprint 1: `MVP funcional implementado`

Ponto residual:

- ainda existe uma camada de compatibilidade `src/api/app/...` coexistindo com a estrutura root-level `src/api/...`; funcionalmente está alinhado, mas ainda não é uma remoção completa da estrutura antiga.
