# Changelog

## 2026-04-17

### Consolidação do dia

O projeto recebeu uma rodada grande de integração entre backend, frontend e infraestrutura Docker, com foco em fechar os entregáveis das Sprints 0, 1 e 2, destravar a Sprint 4 e estabilizar o fluxo de desenvolvimento em contêiner.

### Sprints 0 e 1 — consolidação do backend

Implementado e consolidado:

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
  - persistir recomendação inicial não-stub

Status consolidado:

- Sprint 0: `substancialmente alinhada`
- Sprint 1: `MVP funcional implementado`

Ponto residual:

- ainda existe uma camada de compatibilidade `src/api/app/...` coexistindo com a estrutura root-level `src/api/...`

### Sprint 2 — base histórica e recommendation enriquecida

Implementado:

- leitura e sumarização do histórico em `src/api/app/analytics/historical.py`
- cálculo de casos similares e estatísticas (`prob_vitoria`, `percentil_25`, `percentil_50`)
- enriquecimento da recommendation com resumo histórico e ids de casos similares
- recommendation passou a refletir a base histórica disponível, preparando o terreno para a Sprint 3

### Infra e Docker de desenvolvimento

Implementado:

- `compose.yaml` ajustado para tratar o frontend como ambiente de desenvolvimento real
- `src/web/Dockerfile` convertido para fluxo multi-stage com estágio `dev`
- serviço `web` passou a usar:
  - `target: dev`
  - `npm run dev -- --hostname 0.0.0.0 --port 3000`
  - volume de código em `./src/web:/app`
  - volumes nomeados para `node_modules` e `.next`
- lint do frontend passou a funcionar dentro do contêiner com `docker compose exec web npm run lint`
- remoção da exposição de `OPENAI_API_KEY` do `compose.yaml` para evitar vazamento em `docker compose config`

### Documentação Docker

Implementado:

- criação de `DOCKER.md` na raiz com explicação detalhada de:
  - arquitetura da stack
  - uso diário do Docker
  - mounts e volumes
  - variáveis importantes
  - fluxo dev do frontend e backend
  - troubleshooting

### Sprint 4 — UI do advogado integrada ao que já existe

Atualizado no frontend:

- inbox enriquecida com dados reais de contexto (`assunto`, `uf`, `sub_assunto`)
- tela do caso enriquecida com dados reais da Sprint 1
- `CaseViewer` passou a mostrar:
  - `uf`
  - `assunto`
  - `sub_assunto`
  - `inconsistencias_temporais`
  - `subsidios` estruturados
- seção de documentos passou a usar `source_folder` real quando disponível
- `RecommendationCard` passou a comunicar melhor quando a recommendation já vem enriquecida por histórico
- `OutcomeForm` foi alinhado ao payload atual do backend, incluindo:
  - `sentenca`
  - `custos_processuais`
- mensagens da UI deixaram de assumir fluxo puramente mockado

### Segurança e higiene de configuração

Ajustes feitos:

- remoção da interpolação de `OPENAI_API_KEY` no `compose.yaml`
- revisão dos arquivos do repositório para confirmar ausência de outros vazamentos óbvios em código versionado
- identificado arquivo duplicado `changelog.md`; consolidado tudo neste `CHANGELOG.md`

### Verificações executadas

- `docker compose config`
- `docker compose build web`
- `docker compose up -d web`
- `docker compose exec -T web npm run lint`
- validação da stack com `docker compose ps`
