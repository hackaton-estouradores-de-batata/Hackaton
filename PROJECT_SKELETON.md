# Hackathon UFMG 2026 — Esqueleto do Projeto

> Política de Acordos automatizada para o Banco UFMG em casos de não reconhecimento de contratação de empréstimo.

---

## 1. Visão Geral da Solução

Plataforma web que recebe um processo (autos + subsídios), aplica uma **política de acordos** baseada em regras + LLM, retorna uma **recomendação** (acordo/defesa + valor sugerido + justificativa) para o advogado, e registra tudo em um **dashboard de monitoramento** para o banco.

**Fluxo end-to-end:**

```
[Advogado] → upload/visualiza processo → [Backend]
    ↓
[Pipeline de Análise]
  1. Ingestão de PDFs (autos + subsídios)
  2. Extração estruturada (LLM) → JSON normalizado do caso
  3. Motor de Decisão (regras + score) → acordo/defesa
  4. Calculadora de Valor (histórico + LLM) → faixa sugerida
    ↓
[Recomendação] → advogado decide → registra outcome
    ↓
[Dashboard Banco] → aderência + efetividade
```

---

## 2. Arquitetura Técnica

### Stack sugerida (otimizada para vibe coding)

| Camada | Tecnologia | Por quê |
|---|---|---|
| Frontend | **Next.js 15 + TypeScript + Tailwind + shadcn/ui** | Setup rápido, componentes prontos, deploy Vercel |
| Backend | **FastAPI (Python)** | Async, tipagem, ótimo para IA/ML, fácil de vibecodar |
| LLM | **OpenAI (gpt-4o-mini para extração, gpt-4o para decisão)** | Chave fornecida pelo hackathon |
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
    justificativa: str               # texto para o advogado
    regras_aplicadas: list[str]      # rastreabilidade
    confianca: float                 # 0-1
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
INPUT: caso estruturado
1. Calcular score_robustez_subsidios (0-1)
2. Buscar no histórico: casos similares (valor_causa ± 20%, mesmos pedidos)
   → custo médio de defesa (condenação + honorários + tempo)
   → taxa de vitória histórica
3. EV_defesa = prob_vitoria * 0 + (1-prob_vitoria) * custo_condenacao_esperado
4. EV_acordo = valor_acordo_sugerido
5. Decisão:
   - se score_robustez > 0.8 AND EV_defesa < EV_acordo → DEFESA
   - se score_robustez < 0.4 → ACORDO (agressivo)
   - caso contrário → ACORDO (conservador, usar percentil 25 histórico)
6. Aplicar regras YAML (overrides explícitos do jurídico)
7. Retornar recomendação com justificativa textual gerada por LLM
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

### Sprint 0 — Setup (1h)
- [x] Repo criado pelo template (estrutura `src/`, `data/`, `docs/` já existe)
- [x] `.env.example` com OPENAI_API_KEY, DATABASE_URL já presente
- [ ] Inicializar `src/web/` com Next.js 15 + Tailwind + shadcn/ui
- [ ] Inicializar `src/api/` com FastAPI + pyproject.toml (uv)
- [ ] Converter `sentencas_60k.xlsx` → `sentencas_60k.csv` (script único: `pandas read_excel → to_csv`)

### Sprint 1 — Pipeline de extração (3h)
- [ ] Endpoint `POST /api/cases` aceita PDFs
- [ ] Extractor lê PDF (`pypdf` ou `pdfplumber`) → texto
- [ ] LLM extrai JSON estruturado (autos + subsídios)
- [ ] Persiste no DB
- [ ] **Checkpoint**: rodar nos 2 casos exemplo e validar JSON

### Sprint 2 — Análise histórica (2h)
- [ ] Script `analyze_historical.py` — EDA do CSV de 60k
- [ ] DuckDB views: taxa_vitoria, valor_condenacao_medio por faixa
- [ ] Função `casos_similares(caso) → stats` pronta para o motor

### Sprint 3 — Motor de decisão + valor (3h)
- [ ] `policy/acordos_v1.yaml` inicial
- [ ] `decision_engine.py` lendo YAML
- [ ] `value_estimator.py` combinando histórico + regras
- [ ] Endpoint `GET /recommendation` funcionando
- [ ] **Checkpoint**: recomendação plausível para os 2 casos exemplo

### Sprint 4 — UI do advogado (3h)
- [ ] Inbox de casos
- [ ] Tela de caso com PDFs + card de recomendação
- [ ] Form de outcome (seguiu/divergiu + resultado)
- [ ] **Checkpoint**: gravar o vídeo de 2min aqui já é possível

### Sprint 5 — Dashboard do banco (2h)
- [ ] Métricas de aderência (gauge + série temporal)
- [ ] Métricas de efetividade (economia estimada vs. realizada)
- [ ] Filtros por período/escritório

### Sprint 6 — Backtest + polish (2h)
- [ ] `eval_policy.py` — roda política no histórico de 60k e reporta: economia estimada, casos impactados
- [ ] Justificativas com LLM mais polidas
- [ ] Ajustes finais de UX

### Sprint 7 — Entrega (2h)
- [ ] Gravar vídeo de 2min (demo pelo olhar do advogado)
- [ ] Fechar slides da apresentação
- [ ] README + SETUP finais
- [ ] Push final no repo + submissão no formulário

---

## 9. Decisões Técnicas e Trade-offs

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Política em YAML externo | Hardcode em Python | Jurídico precisa iterar sem dev |
| LLM para extração, regras para decisão | LLM para tudo | Decisão precisa ser auditável/rastreável |
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
| **Uso de IA** | LLM para extração (tarefa difícil), regras para decisão (auditável), LLM para gerar justificativas |

---

**Começar agora:** Sprint 0 → subir boilerplate, converter XLSX, distribuir frentes entre o time (ver `docs/TEAM.md`).
