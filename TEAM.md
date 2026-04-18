# Divisão de Tarefas — Time (17→18/04)

> 5 pessoas · ~17h úteis · nunca mais de 2h sem algo rodando

---

## Pessoas

| ID | Nome | Frente principal |
|----|------|-----------------|
| P1 | Inacio | Backend — Extração e persistência |
| P2 | Sergio e Alemao | Backend — Política V5, backtest e camada estatística |
| P3 | Alemao | Frontend — UI Advogado |
| P4 | Supino Alemao | Frontend — Dashboard Banco |
| P5 | Todos | Apresentação + suporte geral |

---

## Sprint 0 — Setup (1h) · TODO: todos

| Tarefa | Responsável |
|--------|-------------|
| `src/api/` — `fastapi`, `sqlalchemy`, `pdfplumber`, `openai`, `duckdb`, `numpy` via uv | P1 |
| `src/web/` — `npx create-next-app` + Tailwind + shadcn/ui | P3 |
| Converter `data/sentencas_60k.xlsx` → `sentencas_60k.csv` (`pandas read_excel → to_csv`) | P2 |
| Definir schema SQLite: tabelas `cases`, `recommendations`, `outcomes` | P1 |
| Mock data mínimo para destravar UI antes da API real | P2 |

---

## Sprint 1 — Implementação Base do Pipeline (3h) · P1

> Seguir a estrutura real em `src/api/app/...`, separando `routers`, `services` e `llm`.

| Etapa | Entrega |
|------|---------|
| 1. Ingestão | `POST /api/cases` recebe multipart, cria registro em `cases` e salva PDFs em `src/api/data/processos_exemplo/case_<id>/` |
| 2. Extração local | `app/services/extractor.py` lê PDFs com `pdfplumber` e gera texto-base por arquivo |
| 3. Contratos de IA | `app/llm/client.py` + prompts `extract_autos.txt`, `extract_subsidios.txt`, `extract_features.txt`, `extract_context.txt` |
| 4. Checkpoint | Subir API, enviar os 2 casos exemplo e validar: registro criado, arquivos persistidos e resposta consistente |

---

## Sprint 2 — Base Estatística Offline + Curadoria do Histórico (2h) · P2

> O histórico de 60k sai do hot path da recomendação. Nesta sprint ele serve para calibrar a V5, gerar insumos de backtest e consolidar médias nacionais.

| Tarefa | Arquivo |
|--------|---------|
| EDA do CSV: distribuição de `valor_causa`, `resultado_macro`, `resultado_micro`, `valor_condenacao` | `scripts/analyze_historical.py` |
| Consolidar mapa nacional de desconto efetivo sobre o PED por `Resultado micro` | `scripts/analyze_historical.py` |
| Conferir cobertura por `UF` e `Sub-assunto` para suportar as matrizes da V5 | `scripts/analyze_historical.py` |
| Isolar campos mínimos para backtest: `UF`, `Sub-assunto`, `Resultado micro`, `Valor da causa`, `Valor indenizacao` | idem |
| **Checkpoint**: relatório simples com percentuais nacionais e gaps de dados do histórico | — |

---

## Sprint 3 — Motor V5 + Judge Factual + Justificativa (3h) · P2

> Camada central determinística: inventário documental + política V5. LLM fica nas pontas.

### Camada 2 — Núcleo estatístico V5

| Tarefa | Arquivo |
|--------|---------|
| Portar a lógica da V5 para serviço interno, com paridade ao arquivo-oráculo `pOlITICA_ACordo.py` | `src/api/app/services/agreement_policy_v5.py` |
| Inventário documental determinístico dos 6 documentos | `src/api/app/services/document_inventory.py` |
| `build_recommendation_payload(...)` usando `UF + sub_assunto + qtd_docs` | `src/api/app/services/decision_engine.py` |
| `recommendation_pipeline.py` sem histórico, similaridade ou embeddings no hot path | `src/api/app/services/recommendation_pipeline.py` |
| `policy_trace` com matriz, `qtd_docs`, `p_suc`, `VEJ`, `abertura`, `alvo`, `teto` | `src/api/app/schemas/recommendation.py` + `src/web/lib/types.ts` |

### Camada 3 — LLM nas pontas

| Tarefa | Arquivo |
|--------|---------|
| `judge(...)` apenas como revisor factual, sem reabrir a decisão estatística | `src/api/app/services/judge.py` + `src/api/app/llm/prompts/judge.txt` |
| `justificar(...)` usando `policy_trace` e sinais documentais, sem precedentes/similares | `src/api/app/services/justifier.py` + `src/api/app/llm/prompts/justify.txt` |
| Ajustar prompts de extração para não inferirem presença documental | `src/api/app/llm/prompts/extract_subsidios.txt` |

### Orquestração + persistência

| Tarefa | Arquivo |
|--------|---------|
| `GET /api/cases/{id}/recommendation` — pipeline: extração → inventário → V5 → judge factual → justificativa | `src/api/app/routers/recommendations.py` |
| `POST /api/cases/{id}/outcome` — advogado registra `decisao_advogado`, `valor_proposto`, `resultado_negociacao`, `sentenca` | `src/api/app/routers/outcomes.py` |
| **Checkpoint**: `Caso_01` e `Caso_02` batem com o gabarito documental e com a V5 | — |

---

## Sprint 4 — UI do Advogado (3h) · P3

| Tarefa | Arquivo |
|--------|---------|
| `GET /api/cases` — lista casos com status (para inbox) | `src/api/app/routers/cases.py` |
| InboxPage: tabela de casos com `numero_processo`, `valor_causa`, `status`, link para caso | `src/web/app/(advogado)/inbox/page.tsx` |
| CasoPage: visualizador de PDFs + painel lateral com card de recomendação | `src/web/app/(advogado)/caso/[id]/page.tsx` |
| `RecommendationCard`: badge `decisao`, faixa, justificativa, `confianca`, alerta se `judge_concorda == false`, resumo do `policy_trace` | `src/web/components/RecommendationCard.tsx` |
| `OutcomeForm`: radio acordo/defesa, campo valor proposto, resultado negociação, botão salvar | `src/web/components/OutcomeForm.tsx` |
| `lib/api.ts`: funções `getCases()`, `getCase(id)`, `getRecommendation(id)`, `postOutcome(id, data)` | `src/web/lib/api.ts` |
| **Checkpoint**: demo completo advogado → recomendação → registrar outcome | — |

---

## Sprint 5 — Dashboard do Banco (2h) · P4

| Tarefa | Arquivo | Status |
|--------|---------|--------|
| Endpoint `/api/dashboard/metrics` com KPIs operacionais | `src/api/app/routers/dashboard.py` | ✅ |
| Endpoint `/api/dashboard/analytics?uf=&sub_assunto=` com dados analíticos | `src/api/app/routers/dashboard.py` | ✅ |
| Schemas para todos os payloads analíticos | `src/api/app/schemas/dashboard.py` | ✅ |
| Gráfico de Pareto: Eixo X = Sub-assunto, Y = Valor Pedido + linha acumulada | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| Card Valor Pedido × Valor Pago (percentual efetivamente pago) | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| Filtros interativos: UF e Sub-assunto (re-fetch ao mudar) | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| KPI Economia quando Resultado Macro = Não Êxito e há defesa | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| Card Resultado Macro: % Êxito e % Não Êxito com barra visual | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| Gráfico de Pizza: Distribuição de Resultado Micro (quantidade por tipo) | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| Matriz: Linhas = Qtd Docs, Colunas = UF, Valores = Taxa de Sucesso | `src/web/app/(banco)/dashboard/page.tsx` | ✅ |
| Tipos TS para todos os novos payloads | `src/web/lib/types.ts` | ✅ |
| `getDashboardAnalytics(uf?, subAssunto?)` no cliente API | `src/web/lib/api.ts` | ✅ |
| **Checkpoint**: dashboard com Pareto, Pie, Matriz e KPIs financeiros | — | ✅ |

---

## Sprint 6 — Backtest + Polish (2h) · P2 + P3

> Esta sprint fecha o ciclo estatístico. O runtime segue usando a V5; o histórico de 60k entra aqui para medir efeito econômico, não para decidir online.

### Camada 6.1 — Ajuste da V5 para histórico e classificação econômica

| Tarefa | Responsável | Arquivo |
|--------|-------------|---------|
| Padronizar `Resultado micro` em taxonomia única da V5 (`procedente`, `parcial_procedencia`, `improcedente`, `extinto`, `acordo`) | P2 | `src/api/app/services/agreement_policy_v5.py` + `pOlITICA_ACordo.py` |
| Corrigir a leitura de êxito/não êxito usando `Resultado micro` como prioridade, sem depender só de `Resultado macro` | P2 | `scripts/analyze_historical.py` |
| Fixar os descontos nacionais por `Resultado micro` e a decisão de referência histórica (`defesa`, `acordo`, `nula`) | P2 | `src/api/app/services/agreement_policy_v5.py` + `pOlITICA_ACordo_pipeLINE.txt` |

### Camada 6.2 — Backtest econômico da V5

| Tarefa | Responsável | Arquivo |
|--------|-------------|---------|
| Criar `eval_policy.py`: aplicar a V5 no histórico elegível e reportar mix `acordo/defesa`, economia estimada, custo esperado e distribuição por `UF`/`Sub-assunto` | P2 | `scripts/eval_policy.py` |
| Rodar cenários por `qtd_docs` (`0..6`), já que o CSV não traz os PDFs nem o inventário documental real | P2 | `scripts/eval_policy.py` |
| Separar `casos elegiveis` de `casos inconclusivos` no relatório final | P2 | `scripts/eval_policy.py` |

### Camada 6.3 — Polish jurídico e UX

| Tarefa | Responsável | Arquivo |
|--------|-------------|---------|
| Refinar prompt de justificativa para tom jurídico breve, citando matriz, `qtd_docs` e `VEJ` | P2 | `src/api/app/llm/prompts/justify.txt` |
| Ajustes de UX: loading states, mensagens de erro e responsividade do card de recomendação | P3 | `src/web/` |
| Exibir melhor o `Trace V5` para o advogado entender por que saiu `acordo` ou `defesa` | P3 | `src/web/components/RecommendationCard.tsx` |

### Régua de backtest por `Resultado micro`

| Resultado micro | Tratamento no backtest | Desconto de referência sobre o PED | Leitura econômica |
|-----------------|------------------------|------------------------------------|-------------------|
| `procedente` | derrota em defesa | `10%` | banco preserva pouco valor; autor obteve indenização |
| `parcial procedencia` / `parcial procedência` | derrota parcial em defesa | `38%` | banco perde parcialmente |
| `improcedente` | êxito em defesa | `100%` | banco preserva integralmente o PED |
| `extinto` | êxito financeiro fora do mérito; marcar bucket próprio | `100%` | banco ganha sem mérito e preserva integralmente o PED |
| `acordo` | êxito parcial econômico | `70%` | banco preserva parte relevante do PED, mas houve pagamento |

### Regras operacionais da sprint

- A V5 continua escolhendo entre `acordo` e `defesa` com base em `UF`, `sub_assunto` e `qtd_docs`.
- `Resultado micro` entra na V5 como camada de calibração histórica e backtest, não como feature do motor online.
- O backtest mede efeito econômico ex post no histórico; ele não reintroduz retrieval, similaridade ou embeddings na recomendação online.
- `Extinto` deve aparecer separado no relatório, mesmo contando como êxito financeiro.
- Se o histórico não tiver insumos mínimos para a V5 em parte das linhas, o relatório deve separar `casos elegiveis` de `casos inconclusivos`.

---

## Sprint 7 — Entrega (2h) · P5 (todos revisam)

| Tarefa | Responsável |
|--------|-------------|
| Gravar vídeo de 2min (fluxo: inbox → analisar caso → ver recomendação → registrar outcome) | P5 + P3 |
| Slides: política V5, backtest, arquitetura, UX, limitações e próximos passos | P5 |
| `docs/policy_rationale.md`: explicar a política em linguagem acessível ao jurídico | P5 |
| `SETUP.md` com passos reais de instalação e execução | P1 |
| Push final + submissão no formulário | P1 |

---

## Dependências Críticas

```
P1 (extração + schema de caso)      ──►  P2 (inventário documental + V5)
P2 (recomendação + policy_trace)    ──►  P3 (card do advogado usa saída real)
P2 (outcomes + backtest econômico)  ──►  P4 (métricas e narrativa do dashboard)
P2 (eval_policy.py)                 ──►  P5 (slides de potencial financeiro)
```

**Desbloquear P3 cedo:** entregar payload real de recomendação com `policy_trace` antes do polish da UI.
