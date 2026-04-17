# Divisão de Tarefas — Time (17→18/04)

> 5 pessoas · ~17h úteis · nunca mais de 2h sem algo rodando

---

## Pessoas

| ID | Nome | Frente principal |
|----|------|-----------------|
| P1 | Inacio   | Backend — Extração (Sprint 1) |
| P2 | Sergio e Alemao   | Backend — Motor de Decisão (Sprints 2 e 3) |
| P3 | Alemao   | Frontend — UI Advogado (Sprint 4) |
| P4 | Supino Alemao | Frontend — Dashboard Banco (Sprint 5) |
| P5 | Todos | Apresentação + suporte geral |

---

## Sprint 0 — Setup (1h) · TODO: todos

| Tarefa | Responsável |
|--------|-------------|
| `src/api/` — `fastapi`, `sqlalchemy`, `pdfplumber`, `openai`, `duckdb`, `faiss-cpu`, `numpy` via uv | P1 |
| `src/web/` — `npx create-next-app` + Tailwind + shadcn/ui | P3 |
| Converter `data/sentencas_60k.xlsx` → `sentencas_60k.csv` (`pandas read_excel → to_csv`) | P2 |
| Definir schema SQLite: tabelas `cases`, `recommendations`, `outcomes` | P1 |
| Mock data: 2 casos JSON hardcoded para P3/P4 não ficarem bloqueados | P2 |

---

## Sprint 1 — Pipeline de Extração + Features Ricas (3h) · P1

> **Camada 1 da arquitetura de IA** — LLM nas pontas, extração máxima de sinal.

| Tarefa | Arquivo |
|--------|---------|
| `POST /api/cases` — recebe multipart com PDFs, salva em `data/processos_exemplo/` | `src/api/routers/cases.py` |
| Ler PDF com `pdfplumber` → texto limpo por seção | `src/api/services/extractor.py` |
| Prompt `gpt-4o-mini` para autos → JSON básico: `numero_processo`, `valor_causa`, `alegacoes`, `pedidos`, `valor_danos_morais` | `src/api/llm/prompts/extract_autos.txt` |
| Prompt `gpt-4o-mini` para subsídios → JSON: flags `tem_contrato/extrato/dossie/comprovante`, `assinatura_validada`, `canal_contratacao`, `valor_emprestimo` | `src/api/llm/prompts/extract_subsidios.txt` |
| Prompt `gpt-4o` para **features ricas** (structured output): `red_flags` (list), `vulnerabilidade_autor`, `indicio_fraude` (0-1), `forca_narrativa_autor` (0-1), `inconsistencias_temporais` | `src/api/llm/prompts/extract_features.txt` |
| `embed_peticao(texto)` — chama `text-embedding-3-large` e retorna vetor 3072d | `src/api/llm/client.py` |
| Persistir caso completo no SQLite (inclui embedding como BLOB JSON) | `src/api/models/case.py` + `db.py` |
| **Checkpoint**: rodar nos 2 casos exemplo, imprimir JSON + features + confirmar embedding salvo | — |

---

## Sprint 2 — Análise Histórica + Retrieval Semântico (2h) · P2

> **Suporte ao núcleo estatístico** — embeddings viabilizam retrieval de casos *realmente* similares.

| Tarefa | Arquivo |
|--------|---------|
| EDA do CSV: distribuição de `valor_causa`, `resultado`, `valor_condenacao` | `scripts/analyze_historical.py` |
| **Batch embed dos 60k casos** (`text-embedding-3-large`, chunks de 500 com `asyncio`) — salva em `data/embeddings.npy` | `scripts/build_embeddings.py` |
| Indexar embeddings em FAISS (`IndexFlatIP`) — persistir `.faiss` local | idem |
| DuckDB view `taxa_vitoria_por_faixa`: faixas 0–5k, 5–15k, 15–50k, 50k+ | `src/api/analytics/historical.py` |
| `casos_similares(embedding, k=50) → list[case_id]` — cosine top-K + filtro `valor_causa ± 30%` | idem |
| `stats_similares(casos) → {prob_vitoria, custo_medio_defesa, percentil_25, percentil_50}` | idem |
| **Checkpoint**: dado um caso-exemplo, imprimir top-5 similares + stats; validar que fazem sentido | — |

---

## Sprint 3 — Motor Estatístico + Judge + Justificativa (3h) · P2

> **Camadas 2 e 3 da arquitetura** — núcleo estatístico auditável + LLM-as-judge + justificativa.

### Camada 2 — Núcleo estatístico (determinístico, sem LLM)

| Tarefa | Arquivo |
|--------|---------|
| Rascunhar `policy/acordos_v1.yaml`: regras DF-01 (defesa forte) e AP-01 (acordo prioritário), faixas de valor, limites de alçada, pesos dos ajustes | `policy/acordos_v1.yaml` |
| `score_robustez_subsidios(subsidios)` — soma ponderada de flags, retorna 0–1 | `src/api/services/decision_engine.py` |
| `ajustar_score(score, features_ricas)` — aplica deltas por `red_flags`, `indicio_fraude`, `vulnerabilidade_autor` | idem |
| `calcular_ev(stats_similares)` — `EV_defesa` e `EV_acordo` a partir dos top-K similares (sem LLM) | idem |
| `decidir(score_ajustado, ev, yaml)` → `"acordo"` ou `"defesa"` + `regras_aplicadas` | idem |
| `sugerir_valor(stats_similares, score_ajustado, yaml)` — percentil sobre casos similares + ajustes (canal, idade, fraude) | `src/api/services/value_estimator.py` |

### Camada 3 — LLM nas pontas (judge + justificativa)

| Tarefa | Arquivo |
|--------|---------|
| `judge(caso, decisao, valor, casos_similares) → {concorda, observacao, confianca}` — `gpt-4o` recebe tudo e revisa | `src/api/services/judge.py` + `src/api/llm/prompts/judge.txt` |
| Se `judge.concorda == False` → setar `status = "needs_review"` na recomendação | `src/api/services/judge.py` |
| `justificar(caso, decisao, valor, casos_similares, judge_observacao) → str` — `gpt-4o` gera texto citando precedentes e fatores determinantes | `src/api/services/justifier.py` + `src/api/llm/prompts/justify.txt` |

### Orquestração + persistência

| Tarefa | Arquivo |
|--------|---------|
| `GET /api/cases/{id}/recommendation` — pipeline: `casos_similares → stats → score → decidir → valor → judge → justificar` | `src/api/routers/recommendations.py` |
| `POST /api/cases/{id}/outcome` — advogado registra `decisao_advogado`, `valor_proposto`, `resultado` | `src/api/routers/outcomes.py` |
| **Checkpoint**: para os 2 casos exemplo, log completo: top-K similares → score/EV → decisão → judge aprova → justificativa menciona precedentes | — |

---

## Sprint 4 — UI do Advogado (3h) · P3

| Tarefa | Arquivo |
|--------|---------|
| `GET /api/cases` — lista casos com status (para inbox) | `src/api/routers/cases.py` |
| InboxPage: tabela de casos com `numero_processo`, `valor_causa`, `status`, link para caso | `src/web/app/(advogado)/inbox/page.tsx` |
| CasoPage: visualizador de PDFs (iframe) + painel lateral com card de recomendação | `src/web/app/(advogado)/caso/[id]/page.tsx` |
| `RecommendationCard`: badge `decisao`, faixa valor, justificativa, `confianca` (progress), alerta se `judge_concorda == false`, lista colapsável de `casos_similares` (precedentes) | `src/web/components/RecommendationCard.tsx` |
| `OutcomeForm`: radio acordo/defesa, campo valor proposto, resultado negociação, botão salvar | `src/web/components/OutcomeForm.tsx` |
| `lib/api.ts`: funções `getCases()`, `getCase(id)`, `getRecommendation(id)`, `postOutcome(id, data)` | `src/web/lib/api.ts` |
| **Checkpoint**: demo completo advogado → recomendação → registrar outcome | — |

---

## Sprint 5 — Dashboard do Banco (2h) · P4

| Tarefa | Arquivo |
|--------|---------|
| `GET /api/metrics/adherence` — `% seguiu recomendação` agrupado por período | `src/api/routers/metrics.py` |
| `GET /api/metrics/effectiveness` — `economia_estimada`, `taxa_acordo_aceito`, `custo_medio_real` | idem |
| `GET /api/metrics/ai_quality` — `taxa_disagreement_judge`, `confianca_media`, `% casos_needs_review` | idem |
| DashboardPage: gauge de aderência + linha temporal de aderência por semana | `src/web/app/(banco)/dashboard/page.tsx` |
| Cards de efetividade: economia acumulada (recomendado vs. realizado), taxa de acordo fechado | idem |
| Painel "Qualidade da IA": disagreement do judge, distribuição de confiança, casos em revisão | idem |
| Filtro de período (date range picker shadcn) passado como query param para a API | idem |
| Seed de dados fictícios para popular o dashboard sem depender de outcomes reais | `scripts/seed_db.py` |
| **Checkpoint**: dashboard com dados semeados mostrando métricas coerentes | — |

---

## Sprint 6 — Backtest + Polish (2h) · P2 + P3

| Tarefa | Responsável | Arquivo |
|--------|-------------|---------|
| `eval_policy.py`: aplica motor no CSV de 60k, reporta economia estimada e casos impactados | P2 | `scripts/eval_policy.py` |
| Refinar prompts de justificativa (tom jurídico, brevidade) | P2 | `src/api/llm/prompts/decide.txt` |
| Ajustes de UX: loading states, mensagens de erro, responsividade básica | P3 | `src/web/` |

---

## Sprint 7 — Entrega (2h) · P5 (todos revisam)

| Tarefa | Responsável |
|--------|-------------|
| Gravar vídeo de 2min (fluxo: inbox → analisar caso → ver recomendação → registrar outcome) | P5 + P3 |
| Slides: política de acordos, potencial financeiro (output do `eval_policy.py`), arquitetura, UX, limitações, próximos passos | P5 |
| `docs/policy_rationale.md`: explicação da política em linguagem acessível ao time jurídico | P5 |
| `SETUP.md` com passos reais de instalação e execução | P1 |
| Push final + submissão no formulário | P1 |

---

## Dependências Críticas

```
P1 (extractor JSON)  ──►  P2 (motor precisa do schema de caso)
P2 (motor pronto)    ──►  P3 (CasoPage precisa de /recommendation real)
P2 (outcomes no DB)  ──►  P4 (métricas precisam de dados)
P2 (eval_policy.py)  ──►  P5 (slides de potencial financeiro)
```

**Desbloquear P3 e P4 cedo:** P2 entrega mock JSON de caso + recomendação no Sprint 0 para P3/P4 não ficarem ociosos.
