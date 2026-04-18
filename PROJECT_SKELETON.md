# Hackathon UFMG 2026 — Esqueleto do Projeto

> Política de Acordos automatizada para o Banco UFMG em casos de não reconhecimento de contratação de empréstimo.

---

## 1. Visão Geral da Solução

Plataforma web que recebe um processo (autos + subsídios), aplica uma **política de acordos híbrida (LLM + estatística)** e retorna uma **recomendação** (acordo/defesa + valor sugerido + justificativa + confiança) para o advogado, registrando tudo em um **dashboard de monitoramento** para o banco.

**Arquitetura de decisão — LLM nas pontas, estatística no núcleo auditável:**

```
LLM (extração + feature engineering rica + red flags + embeddings)
  ↓
Estatística (score_robustez + EV histórico + percentil + regras YAML) ← núcleo auditável
  ↓
LLM (judge + calibração de confiança + justificativa)
```

**Fluxo end-to-end:**

```
[Advogado] → upload/visualiza processo → [Backend]
    ↓
[Pipeline de Análise]
  1. Ingestão de PDFs (autos + subsídios)
  2. Extração estruturada (LLM) → JSON + features ricas (red flags, vulnerabilidade, inconsistências)
  3. Embedding da petição (OpenAI) → retrieval top-K casos similares no histórico
  4. Motor de Decisão (score_robustez + EV sobre casos similares + regras YAML) → acordo/defesa
  5. Calculadora de Valor (percentil sobre casos similares + ajustes YAML) → faixa sugerida
  6. LLM-as-judge revisa a recomendação; se divergir → flag para revisão humana
  7. LLM calibra confiança (lê contexto completo) e gera justificativa auditável
    ↓
[Recomendação] → advogado decide → registra outcome
    ↓
[Dashboard Banco] → aderência + efetividade + taxa de disagreement do judge
```

---

## 2. Arquitetura Técnica

### Stack sugerida (otimizada para vibe coding)

| Camada | Tecnologia | Por quê |
|---|---|---|
| Frontend | **Next.js 15 + TypeScript + Tailwind + shadcn/ui** | Setup rápido, componentes prontos, deploy Vercel |
| Backend | **FastAPI (Python)** | Async, tipagem, ótimo para IA/ML, fácil de vibecodar |
| LLM | **OpenAI: gpt-4o-mini (extração em lote), gpt-4o (features ricas + judge + justificativa), text-embedding-3-large (retrieval)** | Chave fornecida pelo hackathon — acesso irrestrito |
| Vector search | **pgvector ou FAISS local** sobre embeddings dos 60k casos | Retrieval semântico de casos similares |
| DB | **SQLite (dev) → Postgres (prod)** via SQLAlchemy | Zero config inicial |
| Storage | Filesystem local → S3-compatible | Simples para MVP |
| Análise histórica | **Pandas + DuckDB** sobre o CSV de 60k sentenças | Query SQL direto no CSV |
| Dashboard | **Recharts + shadcn** (ou Streamlit como plano B) | Componentes prontos |
| Deploy | Vercel (front) + Railway/Render (back) | Deploy em minutos |

### Diagrama de componentes

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (src/web — Next.js)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ /advogado    │  │ /caso/[id]   │  │ /dashboard   │   │
│  │ (inbox)      │  │ (recomenda.) │  │ (banco)      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└───────────────────────────┬─────────────────────────────┘
                            │ REST/JSON
┌───────────────────────────▼─────────────────────────────┐
│               BACKEND (src/api — FastAPI)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ /api/cases        POST (ingestão)                │   │
│  │ /api/cases/{id}/recommendation   GET             │   │
│  │ /api/cases/{id}/outcome          POST            │   │
│  │ /api/metrics/adherence           GET             │   │
│  │ /api/metrics/effectiveness       GET             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────┐     │
│  │ Extractor  │ │ Decision   │ │ Value Estimator  │     │
│  │ (LLM)      │ │ Engine     │ │ (histórico+LLM)  │     │
│  └────────────┘ └────────────┘ └──────────────────┘     │
└───────────────────────────┬─────────────────────────────┘
                            │
                ┌───────────┴────────────┐
                │                        │
         ┌──────▼──────┐         ┌───────▼──────┐
         │  SQLite/    │         │  DuckDB      │
         │  Postgres   │         │  (60k        │
         │  (casos,    │         │   sentenças) │
         │   outcomes) │         │              │
         └─────────────┘         └──────────────┘
```

---

## 3. Estrutura de Diretórios

```
hackathon-ufmg-2026-grupoN/
├── README.md                    # Pitch + resumo (complementar template)
├── SETUP.md                     # Como rodar local + env vars
├── .env.example                 # OPENAI_API_KEY, DATABASE_URL, etc.
├── .gitignore
│
├── src/
│   ├── web/                     # Frontend Next.js
│   │   ├── app/
│   │   │   ├── (advogado)/
│   │   │   │   ├── inbox/page.tsx           # Lista de casos
│   │   │   │   └── caso/[id]/page.tsx       # Tela de recomendação
│   │   │   ├── (banco)/
│   │   │   │   └── dashboard/page.tsx       # Métricas
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── CaseViewer.tsx
│   │   │   ├── OutcomeForm.tsx
│   │   │   └── charts/
│   │   ├── lib/api.ts           # Client do backend
│   │   └── package.json
│   │
│   └── api/                     # Backend FastAPI
│       ├── main.py              # Entrypoint + rotas
│       ├── pyproject.toml       # uv/poetry
│       ├── routers/
│       │   ├── cases.py
│       │   ├── recommendations.py
│       │   ├── outcomes.py
│       │   └── metrics.py
│       ├── services/
│       │   ├── extractor.py          # PDF → JSON estruturado
│       │   ├── decision_engine.py    # Regra de decisão
│       │   ├── value_estimator.py    # Sugestão de valor
│       │   └── policy.py             # Config da política (YAML)
│       ├── models/
│       │   ├── case.py               # SQLAlchemy
│       │   ├── recommendation.py
│       │   └── outcome.py
│       ├── schemas/                  # Pydantic
│       │   ├── case.py
│       │   └── recommendation.py
│       ├── llm/
│       │   ├── client.py             # Wrapper OpenAI
│       │   └── prompts/
│       │       ├── extract_autos.txt
│       │       ├── extract_subsidios.txt
│       │       └── decide.txt
│       ├── analytics/
│       │   ├── historical.py         # Queries no CSV de 60k
│       │   └── metrics.py
│       ├── db.py
│       └── tests/
│
├── policy/
│   └── acordos_v1.yaml          # Política versionada (editável sem deploy)
│
├── data/
│   ├── processos_exemplo/       # 2 processos exemplo do enunciado (não versionados)
│   │   ├── caso_001/
│   │   │   ├── autos/
│   │   │   └── subsidios/
│   │   └── caso_002/
│   │       ├── autos/
│   │       └── subsidios/
│   ├── subsidios/               # Base de subsídios dos últimos 12 meses (não versionada)
│   ├── sentencas_60k.csv        # Histórico de 60k sentenças (não versionado)
│   └── README.md                # Descrição dos dados
│
├── docs/
│   ├── presentation.pdf         # Slides finais
│   ├── architecture.md          # Decisões arquiteturais
│   ├── policy_rationale.md      # Justificativa da política (linguagem jurídica)
│   └── demo.mp4                 # Vídeo de 2min
│
└── scripts/
    ├── seed_db.py               # Popula DB com casos exemplo
    ├── analyze_historical.py    # EDA do CSV de 60k
    └── eval_policy.py           # Backtest da política no histórico
```

---

## 4. Modelo de Domínio

### Entidades principais

```python
# Case — um processo judicial
class Case:
    id: UUID
    numero_processo: str
    valor_causa: Decimal
    autor_nome: str
    autor_cpf: str
    data_distribuicao: date
    # extraídos dos autos via LLM
    alegacoes: list[str]
    pedidos: list[str]          # dano moral, repetição indébito, etc.
    valor_pedido_danos_morais: Decimal | None
    # features ricas extraídas por LLM (gpt-4o)
    red_flags: list[str]        # ex: "data_contrato_anterior_ao_cpf", "assinatura_divergente"
    vulnerabilidade_autor: Literal["idoso", "analfabeto", "baixa_renda", "nenhuma"] | None
    indicio_fraude: float       # 0-1, estimado pelo LLM
    forca_narrativa_autor: float  # 0-1, quão coerente/persuasiva é a petição
    # embedding para retrieval semântico
    embedding: list[float]      # text-embedding-3-large (3072d)
    # extraídos dos subsídios
    subsidios: Subsidios         # ver abaixo
    status: Literal["pending", "analyzed", "decided", "closed"]

class Subsidios:
    tem_contrato: bool
    tem_extrato: bool
    tem_comprovante_credito: bool
    tem_dossie: bool
    tem_demonstrativo: bool
    tem_laudo: bool
    contrato_assinado: bool
    assinatura_validada_dossie: bool | None
    valor_emprestimo: Decimal | None
    data_contratacao: date | None
    canal_contratacao: str | None   # presencial, digital, correspondente
    score_robustez: float           # 0-1, calculado

# Recommendation — output do pipeline
class Recommendation:
    case_id: UUID
    decisao: Literal["acordo", "defesa"]
    valor_sugerido_min: Decimal | None
    valor_sugerido_max: Decimal | None
    justificativa: str               # texto para o advogado (gerado por LLM)
    regras_aplicadas: list[str]      # rastreabilidade
    casos_similares_ids: list[str]   # top-K usados no EV/percentil (rastreabilidade)
    confianca: float                 # 0-1, calibrada pelo LLM-as-judge
    judge_concorda: bool             # True se judge aprovou; False → revisar
    judge_observacao: str | None     # por que discordou, se discordou
    policy_version: str              # "v1", "v2"...
    created_at: datetime

# Outcome — o que o advogado efetivamente fez
class Outcome:
    case_id: UUID
    recommendation_id: UUID
    decisao_advogado: Literal["acordo", "defesa"]
    seguiu_recomendacao: bool        # derivado
    valor_proposto: Decimal | None
    valor_acordado: Decimal | None   # se fechou acordo
    resultado_negociacao: Literal["aceito", "recusado", "em_andamento"] | None
    # se foi a julgamento
    sentenca: Literal["procedente", "improcedente", "parcial"] | None
    valor_condenacao: Decimal | None
    custos_processuais: Decimal | None
    updated_at: datetime
```

---

## 5. A Política de Acordos (core do negócio)

Separar política de código é **crítico** — o time jurídico precisa revisar/ajustar sem depender de deploy.

### `policy/acordos_v1.yaml`

```yaml
version: "1.0"
description: "Política de acordos para casos de não reconhecimento de empréstimo"

# Regras de defesa forte (não oferecer acordo)
defesa_forte:
  - id: DF-01
    nome: "Subsídios completos e robustos"
    condicoes:
      - tem_contrato: true
      - tem_comprovante_credito: true
      - tem_dossie: true
      - assinatura_validada_dossie: true
    acao: "defesa"
    confianca: 0.9

# Regras de acordo prioritário (oferecer acordo agressivo)
acordo_prioritario:
  - id: AP-01
    nome: "Subsídios frágeis"
    condicoes:
      - tem_contrato: false
      - OR:
          - tem_comprovante_credito: false
          - tem_dossie: false
    acao: "acordo"
    faixa_valor: "60-80%_valor_pedido"

# Calculadora de valor
valor:
  base: "percentil_25_historico_casos_similares"
  teto: "min(valor_pedido_danos_morais, custo_processo_estimado)"
  piso: "custas_judiciais_estimadas"
  fatores_ajuste:
    - se: "canal_contratacao == 'correspondente'"
      multiplicador: 1.15   # risco maior para o banco
    - se: "autor_idoso"     # proteção CDC
      multiplicador: 1.10

# Limites de alçada
alcada:
  aprovacao_automatica_ate: 5000.00
  requer_aprovacao_gestor_ate: 20000.00
  requer_aprovacao_diretoria_acima: 20000.00
```

### Lógica do Decision Engine

```
INPUT: caso estruturado + features ricas (red_flags, vulnerabilidade, indicio_fraude)

[Camada 1 — LLM feature extraction já feita no Sprint 1]

[Camada 2 — Retrieval semântico]
1. Embedding da petição (text-embedding-3-large)
2. Top-K (k=50) casos similares por cosine similarity no histórico de 60k
3. Filtrar top-K por valor_causa ± 30% e pedidos compatíveis → casos_similares

[Camada 3 — Núcleo estatístico determinístico]
4. score_robustez_subsidios (0-1) — soma ponderada das flags dos subsídios
5. Ajustes por features ricas:
   - red_flags não-vazia → score -= 0.2
   - indicio_fraude > 0.7 → score += 0.15 (favorece defesa)
   - vulnerabilidade_autor != "nenhuma" → score -= 0.1 (CDC/proteção)
6. Sobre casos_similares:
   - prob_vitoria = taxa_improcedente
   - custo_esperado_defesa = média(valor_condenacao | procedente) + custas
7. EV_defesa = (1 - prob_vitoria) × custo_esperado_defesa
8. EV_acordo = percentil_25(valor_condenacao em casos_similares) × ajustes_yaml
9. Decisão:
   - score_robustez > 0.8 AND EV_defesa < EV_acordo → DEFESA
   - score_robustez < 0.4 → ACORDO (agressivo: percentil 35)
   - caso contrário → ACORDO (conservador: percentil 25)
10. Aplicar regras YAML (overrides explícitos do jurídico)

[Camada 4 — LLM judge + calibração + justificativa]
11. LLM-as-judge (gpt-4o): recebe caso + casos_similares + decisão + valor
    → retorna {concorda: bool, observacao: str, confianca_calibrada: 0-1}
12. Se judge discorda → status = "needs_review"; advogado decide sem auto-aprovação
13. LLM gera justificativa narrativa citando casos similares, red flags e fatores decisivos
```

---

## 6. Requisitos do Enunciado — Mapeamento

| # | Requisito | Onde é atendido |
|---|---|---|
| 1 | **Regra de decisão** | `src/api/services/decision_engine.py` + `policy/acordos_v1.yaml` |
| 2 | **Sugestão de valor** | `src/api/services/value_estimator.py` (histórico CSV + regras YAML) |
| 3 | **Acesso à recomendação** | Frontend `src/web/app/(advogado)/caso/[id]` — card com decisão, valor, justificativa, botão "aceitar/divergir" |
| 4 | **Monitoramento de aderência** | Dashboard: % advogados que seguiram recomendação, por escritório/advogado/faixa de valor |
| 5 | **Monitoramento de efetividade** | Dashboard: economia estimada (EV recomendado vs. realizado), taxa de acordo aceito, custo médio |

---

## 7. Endpoints da API (contrato)

```
POST   /api/cases                        # Ingestão de um caso (upload PDFs)
GET    /api/cases                        # Lista (inbox do advogado)
GET    /api/cases/{id}                   # Detalhes + estruturado
GET    /api/cases/{id}/recommendation    # Gera/retorna recomendação
POST   /api/cases/{id}/outcome           # Advogado registra decisão/resultado

GET    /api/metrics/adherence            # ?de=YYYY-MM-DD&ate=...
GET    /api/metrics/effectiveness        # Economia, taxa acordo, etc.
GET    /api/metrics/lawyers              # Ranking/performance

GET    /api/policy/current               # Versão ativa
POST   /api/policy                       # Upload nova versão (admin)
```

---

## 8. Roadmap de Execução (vibe coding — 17→18/04)

**Objetivo: entregar algo funcional em cada sprint. Nunca ficar mais de 2h sem algo rodando.**

> Roadmap alinhado ao `TEAM.md`: Sprints 0–4 refletem o fluxo principal já implementado; Sprint 5 está parcial no runtime atual; Sprints 6–7 seguem pendentes.

### Sprint 0 — Setup (1h) · Todos
- [x] Repo-base, `.env.example`, `src/web/` e `src/api/` inicializados
- [x] Schema SQLite criado para `cases`, `recommendations` e `outcomes`
- [x] Conversão `sentencas_60k.xlsx` → `data/sentencas_60k.csv`
- [x] Casos exemplo e mock data preparados para destravar frontend e dashboard

### Sprint 1 — Implementação Base do Pipeline (3h) · P1
- [x] `POST /api/cases` recebe multipart, cria `case` e persiste PDFs em `data/processos_exemplo/case_<id>/`
- [x] `extractor.py` lê PDFs com `pdfplumber` e monta texto-base por arquivo
- [x] `llm/client.py` + prompts de extração/features/embedding integrados ao fluxo
- [x] Persistência inicial do caso analisado no banco, incluindo texto e features
- [x] **Checkpoint**: 2 casos exemplo processados com arquivos persistidos e resposta consistente

### Sprint 2 — Análise Histórica + Retrieval Semântico (2h) · P2
- [x] `scripts/analyze_historical.py` faz EDA do histórico de 60k casos
- [x] `scripts/build_embeddings.py` gera embeddings e persiste `data/embeddings.npy`, `.faiss` e metadata
- [x] FAISS local + metadata ficam disponíveis para retrieval
- [x] `casos_similares(...)` e `stats_similares(...)` alimentam o núcleo estatístico com top-K e percentis
- [x] **Checkpoint**: recomendações já passam a usar similares e estatística histórica

### Sprint 3 — Motor Estatístico + Judge + Justificativa (3h) · P2
- [x] `policy/acordos_v1.yaml` versionada e conectada ao motor
- [x] `decision_engine.py` calcula score, EV, decisão e `regras_aplicadas`
- [x] `value_estimator.py` sugere faixa com base em histórico + policy
- [x] `judge.py` e `justifier.py` revisam decisão, calibram confiança e geram justificativa
- [x] `GET /api/cases/{id}/recommendation` orquestra o pipeline completo
- [x] `POST /api/cases/{id}/outcome` registra o desfecho do advogado
- [x] **Checkpoint**: casos exemplo com recomendação plausível, judge e justificativa auditável

### Sprint 4 — UI do Advogado (3h) · P3
- [x] Inbox de casos conectada ao backend
- [x] Tela do caso com visualização inline de PDFs + card de recomendação
- [x] Formulário de novo caso alinhado ao fluxo real: upload de PDFs → extração automática
- [x] `OutcomeForm` registra aderência/divergência e resultado
- [x] **Checkpoint**: fluxo demo do advogado já é possível (`inbox → caso → recomendação → outcome`)

### Sprint 5 — Dashboard do Banco (2h) · P4
- [x] Endpoint consolidado `/api/dashboard/metrics` com métricas agregadas reais
- [x] Dashboard básico com cards de aderência, aceitação e disagreement do judge
- [ ] Gauge e série temporal
- [ ] Economia estimada vs. realizada
- [ ] Filtros por período/escritório
- [ ] Seed específico para cenários de dashboard

### Sprint 6 — Backtest + Polish (2h) · P2 + P3
- [ ] `eval_policy.py` para backtest no histórico de 60k
- [ ] Refino final de justificativas/prompts
- [ ] Polish de UX: responsividade, loading, erros e ajustes finos

### Sprint 7 — Entrega (2h) · P5
- [ ] Gravar vídeo de 2min (fluxo: inbox → analisar caso → recommendation → outcome)
- [ ] Fechar slides da apresentação
- [ ] README + SETUP finais
- [ ] Push final no repo + submissão no formulário

---

## 9. Decisões Técnicas e Trade-offs

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Política em YAML externo | Hardcode em Python | Jurídico precisa iterar sem dev |
| LLM nas pontas (features + judge + justificativa), estatística no núcleo | LLM decidindo tudo OU só estatística pura | Extração rica (red flags, vulnerabilidade) e retrieval semântico são inviáveis sem LLM; decisão e valor continuam auditáveis no núcleo estatístico; judge evita erros óbvios que stats não detecta |
| Embeddings + retrieval semântico | Filtro por `valor_causa ± 20%` | Similaridade semântica captura casos realmente análogos; filtro numérico deixa passar ruído |
| LLM-as-judge como segunda camada | Confiar na decisão estatística sozinha | Sistemas high-stakes (Anthropic/OpenAI) usam judge para flag de revisão humana |
| DuckDB sobre CSV | Subir tudo pro Postgres | Zero ETL, query rápida no hackathon |
| SQLite único | SQLite dev + Postgres prod | MVP local — sem Docker, sem credenciais, um arquivo |
| XLSX → CSV (conversão única) | DuckDB lendo XLSX direto | CSV é mais simples e sem dependência de openpyxl no runtime |
| Next.js + FastAPI separados | Full-stack Next | Backend Python é melhor para IA + time provavelmente mais confortável |
| Recharts | D3 custom | Vibe coding friendly |

---

## 10. Limitações Conhecidas (para a apresentação)

- Política v1 baseada em heurísticas + histórico agregado; uma v2 poderia usar modelo preditivo treinado caso a caso
- PDFs escaneados não são suportados (MVP assume texto selecionável, que é o caso atual)
- Dashboard assume dados razoavelmente limpos — produção precisaria de data quality checks
- Não há fluxo de aprovação multi-nível (alçada) implementado — apenas sinalizado
- Monitoramento de efetividade depende de advogados reportarem outcomes corretamente

---

## 11. Próximos Passos (1 mês adicional)

1. **Modelo preditivo próprio** — treinar classificador (acordo/defesa) e regressor (valor ótimo) no histórico
2. **Fluxo de alçada** — aprovação multi-nível baseada em valor
3. **Integração real com a plataforma Enter** — receber casos via webhook
4. **Feedback loop** — política se ajusta automaticamente com base em efetividade observada (bandit/A-B por versão)
5. **Explicabilidade** — SHAP values ou LLM reasoning expandido para cada recomendação
6. **Alerta de drift** — quando a efetividade cai abaixo de threshold, notificar gestor
7. **Simulador "what-if"** — jurídico testa mudanças na política antes de publicar

---

## 12. Critérios de Avaliação — Como Endereçamos

| Critério | Como atendemos |
|---|---|
| **Leitura do problema** | Seção 5 (política) + docs/policy_rationale.md + backtest no histórico |
| **Criatividade e usabilidade** | UX do advogado com recomendação + justificativa + 1-clique outcome |
| **Colaboração** | Divisão clara: front / back-extração / back-motor / dashboard-analytics |
| **Execução** | MVP funcional end-to-end nos 2 casos exemplo + backtest nos 60k |
| **Uso de IA** | Arquitetura em 3 camadas: (1) LLM para extração + features ricas + embeddings, (2) núcleo estatístico determinístico (score + EV + percentil) auditável, (3) LLM-as-judge + calibração de confiança + justificativa. Padrões globais: RAG, function calling, LLM-as-judge |

---

**Começar agora:** Sprint 0 → subir boilerplate, converter XLSX, distribuir frentes entre o time (ver `docs/TEAM.md`).
