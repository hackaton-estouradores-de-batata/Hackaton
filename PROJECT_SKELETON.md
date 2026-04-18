# Hackathon UFMG 2026 — Esqueleto do Projeto

> Política de acordos automatizada para o Banco UFMG em casos de não reconhecimento de contratação de empréstimo.

---

## 1. Visão Geral da Solução

Plataforma web que recebe um processo judicial, extrai os dados relevantes dos autos e dos subsídios, monta um inventário probatório determinístico e aplica uma **política estatística V5** para recomendar **`acordo`** ou **`defesa`**. A recomendação sai com faixa sugerida, justificativa, confiança e rastro de decisão (`policy_trace`) para o advogado e para o dashboard do banco.

**Arquitetura de decisão atual:**

```text
LLM (extração estruturada + leitura qualitativa dos subsídios)
  ↓
Inventário documental determinístico (6 documentos)
  ↓
Política V5 (UF + subassunto + qtd_docs → defesa/acordo + faixa)
  ↓
LLM factual (judge somente quando necessário) + justificativa
```

**Princípio operacional**

- LLM não decide o valor nem a estratégia final.
- A decisão e a faixa vêm do núcleo determinístico da V5.
- O histórico de 60k casos serve para calibração e backtest offline, não para o hot path da recomendação.

**Fluxo end-to-end**

```text
[Advogado] → upload/visualiza processo → [Backend]
    ↓
[Pipeline de Análise]
  1. Ingestão dos PDFs (autos + subsídios)
  2. Extração estruturada dos autos e sinais qualitativos dos subsídios
  3. Inventário documental: contrato, comprovante, extrato, demonstrativo, dossiê, laudo
  4. Política V5 calcula `p_suc`, `VEJ`, `abertura`, `alvo`, `teto` e decide `acordo/defesa`
  5. Judge factual só revisa coerência, sem substituir a V5
  6. Justificativa usa `policy_trace` e sinais documentais
    ↓
[Recomendação] → advogado decide → registra outcome
    ↓
[Dashboard Banco] → aderência + aceite + disagreement do judge + leitura operacional
```

---

## 2. Arquitetura Técnica

### Stack sugerida

| Camada | Tecnologia | Papel no projeto |
|---|---|---|
| Frontend | **Next.js 15 + TypeScript + Tailwind + shadcn/ui** | Inbox, tela do caso, dashboard e formulários |
| Backend | **FastAPI + SQLAlchemy** | Orquestra ingestão, recomendação, outcomes e métricas |
| LLM | **OpenAI (`gpt-4o-mini` / `gpt-4o`)** | Extração, revisão factual e justificativa |
| Núcleo estatístico | **Python + `Decimal`** | Implementação determinística da V5 |
| Banco | **SQLite** (dev) / Postgres (produção futura) | Persistência de casos, recomendações e outcomes |
| Dados históricos | **Pandas + DuckDB** | EDA, calibração e backtest offline sobre o CSV de 60k |
| Storage | Filesystem local | Persistência dos PDFs no MVP |
| Embeddings | **Opcional/offline** | Fora do hot path; podem permanecer apenas para analytics experimentais |

### Diagrama de componentes

```text
┌──────────────────────────────────────────────────────────┐
│                FRONTEND (src/web — Next.js)             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ /inbox       │  │ /caso/[id]   │  │ /dashboard    │   │
│  │ advogado     │  │ recomendação │  │ banco         │   │
│  └──────────────┘  └──────────────┘  └───────────────┘   │
└───────────────────────────┬──────────────────────────────┘
                            │ REST/JSON
┌───────────────────────────▼──────────────────────────────┐
│                 BACKEND (src/api/app)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │ /api/cases                                       │  │
│  │ /api/cases/{id}/recommendation                   │  │
│  │ /api/cases/{id}/outcome                          │  │
│  │ /api/dashboard/metrics                           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────┐ ┌──────────────────┐ ┌────────────┐  │
│  │ Extractor    │ │ Document         │ │ Decision   │  │
│  │ + LLM        │ │ Inventory        │ │ Engine V5  │  │
│  └──────────────┘ └──────────────────┘ └────────────┘  │
│           ┌──────────────┐ ┌────────────────────────┐  │
│           │ Judge factual│ │ Justifier com trace V5 │  │
│           └──────────────┘ └────────────────────────┘  │
└───────────────────────────┬──────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
      ┌───────▼────────┐         ┌────────▼────────┐
      │ SQLite         │         │ CSV histórico   │
      │ casos/outcomes │         │ 60k + DuckDB    │
      │ recomendações  │         │ backtest offline│
      └────────────────┘         └─────────────────┘
```

---

## 3. Estrutura de Diretórios

```text
hackathon-ufmg-2026-grupoN/
├── README.md
├── SETUP.md
├── .env.example
├── pOlITICA_ACordo_pipeLINE.txt      # Fonte textual da V5
├── pOlITICA_ACordo.py                # Oráculo de teste/paridade da V5
│
├── src/
│   ├── web/
│   │   ├── app/
│   │   │   ├── (advogado)/
│   │   │   │   ├── inbox/page.tsx
│   │   │   │   ├── caso/[id]/page.tsx
│   │   │   │   └── casos/novo/page.tsx
│   │   │   ├── (banco)/dashboard/page.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── CaseDocumentsViewer.tsx
│   │   │   ├── NewCaseForm.tsx
│   │   │   └── OutcomeForm.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types.ts
│   │
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── routers/
│       │   │   ├── cases.py
│       │   │   ├── recommendations.py
│       │   │   ├── outcomes.py
│       │   │   ├── dashboard.py
│       │   │   └── health.py
│       │   ├── services/
│       │   │   ├── extractor.py
│       │   │   ├── document_inventory.py
│       │   │   ├── agreement_policy_v5.py
│       │   │   ├── decision_engine.py
│       │   │   ├── recommendation_pipeline.py
│       │   │   ├── judge.py
│       │   │   ├── justifier.py
│       │   │   ├── case_normalization.py
│       │   │   └── case_maintenance.py
│       │   ├── llm/
│       │   │   ├── client.py
│       │   │   └── prompts/
│       │   │       ├── extract_autos.txt
│       │   │       ├── extract_subsidios.txt
│       │   │       ├── extract_features.txt
│       │   │       ├── extract_context.txt
│       │   │       ├── judge.txt
│       │   │       └── justify.txt
│       │   ├── analytics/
│       │   │   ├── historical.py      # offline / analytics
│       │   │   └── semantic.py        # offline / experimental
│       │   ├── models/
│       │   ├── schemas/
│       │   └── db.py
│       ├── tests/
│       └── pyproject.toml
│
├── policy/
│   └── acordos_v1.yaml                # legado/referência; fora do hot path
│
├── data/
│   ├── processos_exemplo/
│   ├── sentencas_60k.csv
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   └── policy_rationale.md
│
└── scripts/
    ├── analyze_historical.py
    ├── build_embeddings.py            # offline / experimental
    ├── convert_sentencas_xlsx_to_csv.py
    ├── sanitize_cases.py
    └── eval_policy.py                 # Sprint 6
```

---

## 4. Modelo de Domínio

### Entidades principais

```python
class Case:
    id: UUID
    numero_processo: str
    valor_causa: Decimal
    valor_pedido_danos_morais: Decimal | None
    autor_nome: str
    autor_cpf: str
    uf: str | None
    assunto: str | None
    sub_assunto: str | None
    alegacoes: list[str]
    pedidos: list[str]
    red_flags: list[str]
    vulnerabilidade_autor: str | None
    indicio_fraude: float | None
    forca_narrativa_autor: float | None
    subsidios: Subsidios
    document_inventory: dict
    status: Literal["pending", "analyzed", "needs_review", "decided", "closed"]


class Subsidios:
    tem_contrato: bool
    tem_comprovante: bool
    tem_extrato: bool
    tem_demonstrativo_evolucao_divida: bool
    tem_dossie: bool
    tem_laudo_referenciado: bool
    assinatura_validada: bool | None
    canal_contratacao: str | None
    valor_emprestimo: Decimal | None
    documento_contraditorio: bool


class Recommendation:
    case_id: UUID
    decisao: Literal["acordo", "defesa"]
    valor_sugerido_min: Decimal | None
    valor_sugerido_max: Decimal | None
    justificativa: str
    confianca: float
    regras_aplicadas: list[str]
    judge_concorda: bool
    judge_observacao: str | None
    policy_version: Literal["v5"]
    policy_trace: dict
    casos_similares_ids: list[str]  # compatibilidade; hoje tende a []


class Outcome:
    case_id: UUID
    recommendation_id: UUID | None
    decisao_advogado: Literal["acordo", "defesa"]
    seguiu_recomendacao: bool
    valor_proposto: Decimal | None
    valor_acordado: Decimal | None
    resultado_negociacao: Literal["aceito", "recusado", "em_andamento"] | None
    sentenca: str | None
    valor_condenacao: Decimal | None
    custos_processuais: Decimal | None
```

### Observações importantes

- `document_inventory` é determinístico e conta no máximo 6 documentos válidos.
- `documento_contraditorio` não muda sozinho a decisão da V5; ele força revisão factual.
- O histórico de 60k não precisa estar no banco transacional para a recomendação online funcionar.

---

## 5. Política de Acordo e Defesa — V5

### 5.1. Entradas da política

- `PED`: usar `valor_pedido_danos_morais`; se ausente, cair para `valor_causa`
- `UF`
- `sub_assunto`: `generico`, `golpe` ou `indefinido`
- `qtd_docs`: total de documentos válidos entre os 6 tipos da V5
- `documento_contraditorio`: sinalizador para revisão humana

### 5.2. Os 6 documentos da V5

1. Contrato
2. Comprovante de crédito
3. Extrato
4. Demonstrativo de evolução da dívida
5. Dossiê
6. Laudo referenciado

Regras:

- documento duplicado não soma de novo
- documento inutilizável não soma
- documento contraditório deve ser sinalizado
- `qtd_docs` sempre fica entre `0` e `6`

### 5.3. Escolha da matriz

- `sub_assunto = generico` → `MATRIZ_GENERICO_6D`
- `sub_assunto = golpe` → `MATRIZ_GOLPE_6D`
- fallback → `MATRIZ_GERAL_6D`

### 5.4. Regras de sanidade

- Mais prova nunca pode piorar a chance estimada de sucesso.
- Piso técnico de sucesso: `1%`
- Teto técnico de sucesso: `98%`
- `RR` e outras lacunas históricas usam fallback nacional (`TOTAL`) quando necessário.

### 5.5. Saídas da V5

A política calcula:

- `p_suc`: probabilidade estimada de sucesso em defesa
- `p_per`: probabilidade estimada de perda
- `desc_uf`: desconto médio da UF quando o banco perde
- `VEJ`: valor esperado do julgamento
- `abertura`, `alvo`, `teto`: faixa econômica racional de acordo
- `teto_pct = teto / PED`

### 5.6. Regra final de decisão

- `ACORDO` se `teto_pct >= 0.25`
- `DEFESA` se `teto_pct < 0.25`

### 5.7. Papel do judge

O judge não recalcula a V5. Ele apenas:

- confirma coerência entre decisão, faixa e `policy_trace`
- sinaliza revisão humana se houver contradição documental, ausência de insumo crítico ou inconsistência estrutural
- pode reduzir a confiança e preencher `judge_observacao`

---

## 6. Backtest da Sprint 6

### Objetivo

Medir se a V5 teria melhor desempenho econômico do que o histórico observado, sem recolocar histórico, similaridade ou embeddings no fluxo online.

### Método esperado

1. Carregar o CSV de 60k casos.
2. Normalizar `UF`, `Sub-assunto`, `Resultado macro`, `Resultado micro`, `Valor da causa` e `Valor indenizacao`.
3. Converter `Resultado micro` em régua econômica padronizada da V5.
4. Aplicar a V5 nos casos elegíveis.
5. Comparar o que a política recomendaria contra o desfecho econômico histórico.
6. Reportar economia estimada, taxa de preservação do PED, mix `acordo/defesa` e taxa de revisão humana.

### Camadas da Sprint 6

#### Camada 6.1 — Ajuste da V5 para histórico

- Criar uma taxonomia única de `Resultado micro`.
- Fixar a decisão de referência histórica por bucket:
  - `procedente` → `defesa`
  - `parcial_procedencia` → `defesa`
  - `improcedente` → `defesa`
  - `extinto` → `nula`
  - `acordo` → `acordo`
- Fixar o desconto nacional de referência sobre o PED:
  - `procedente` → `10%`
  - `parcial_procedencia` → `38%`
  - `improcedente` → `100%`
  - `extinto` → `100%`
  - `acordo` → `70%`
- Tratar `Resultado micro` como camada de calibração e backtest, não como feature do motor online.

#### Camada 6.2 — Backtest econômico

- Rodar a V5 em cenários de `qtd_docs`, porque o histórico de 60k não traz os PDFs.
- Separar `casos elegiveis` de `casos inconclusivos`.
- Comparar custo esperado da política contra custo histórico observado.

#### Camada 6.3 — Polish

- Melhorar a justificativa textual com base em `policy_trace`.
- Melhorar legibilidade do `Trace V5` na UI.
- Fechar mensagens de erro e estados de carregamento.

### Régua econômica por `Resultado micro`

| Resultado micro | Classe econômica | Desconto de referência sobre o PED | Interpretação |
|---|---|---:|---|
| `procedente` | derrota | `10%` | autor recebeu indenização relevante |
| `parcial procedencia` / `parcial procedência` | derrota parcial | `38%` | banco perdeu parte do PED |
| `improcedente` | êxito | `100%` | defesa preservou integralmente o PED |
| `extinto` | êxito fora do mérito | `100%` | banco ganhou sem julgamento de mérito |
| `acordo` | êxito parcial | `70%` | houve pagamento, mas parte material do PED foi preservada |

### Saídas esperadas do backtest

- total de casos elegíveis e inconclusivos
- mix de recomendações da V5
- economia estimada frente ao histórico observado
- taxa de revisão humana
- corte por `UF`
- corte por `sub_assunto`
- leitura específica de `extinto` como bucket separado

### Restrições

- Se `qtd_docs` não estiver disponível no histórico, o backtest precisa declarar explicitamente o proxy usado ou separar o caso como inconclusivo.
- A implementação preferencial é cenário por `qtd_docs`, não inferência artificial do inventário documental a partir do resultado.
- O backtest usa médias nacionais de desconto por `Resultado micro`; isso não substitui o motor online.

---

## 7. Requisitos do Enunciado — Mapeamento

| # | Requisito | Onde é atendido |
|---|---|---|
| 1 | Regra de decisão | `src/api/app/services/agreement_policy_v5.py` + `src/api/app/services/decision_engine.py` |
| 2 | Sugestão de valor | mesma V5 (`abertura`, `alvo`, `teto`) |
| 3 | Acesso à recomendação | `src/web/app/(advogado)/caso/[id]/page.tsx` + `RecommendationCard` |
| 4 | Monitoramento de aderência | `src/api/app/routers/dashboard.py` + dashboard web |
| 5 | Monitoramento de efetividade | dashboard + `scripts/eval_policy.py` no Sprint 6 |

---

## 8. Endpoints da API

```text
GET    /healthz

POST   /api/cases
GET    /api/cases
GET    /api/cases/{id}
GET    /api/cases/{id}/recommendation
POST   /api/cases/{id}/outcome

GET    /api/dashboard/metrics
```

Observação:

- Não há dependência de endpoint de política dinâmica no runtime atual.
- `policy_trace` faz parte da resposta de recomendação e é o principal mecanismo de auditabilidade.

---

## 9. Roadmap de Execução

> Objetivo: entregar algo funcional em cada sprint, sempre com o runtime principal rodando.

### Sprint 0 — Setup (1h) · Todos
- [x] Repo-base, `.env.example`, `src/web/` e `src/api/` inicializados
- [x] Schema SQLite criado para `cases`, `recommendations` e `outcomes`
- [x] Conversão `sentencas_60k.xlsx` → `data/sentencas_60k.csv`

### Sprint 1 — Implementação Base do Pipeline (3h) · P1
- [x] Ingestão multipart funcional
- [x] Extração de PDFs com `pdfplumber`
- [x] Estrutura LLM integrada à análise
- [x] Persistência inicial do caso analisado

### Sprint 2 — Base Estatística Offline + Curadoria do Histórico (2h) · P2
- [x] `scripts/analyze_historical.py` com leitura do histórico
- [x] Conversão e saneamento mínimo do CSV
- [ ] Normalização econômica completa por `Resultado micro`
- [ ] Relatório definitivo para alimentar o backtest

### Sprint 3 — Motor V5 + Judge Factual + Justificativa (3h) · P2
- [x] `document_inventory.py` com os 6 documentos
- [x] `agreement_policy_v5.py` em paridade com o oráculo
- [x] `decision_engine.py` e `recommendation_pipeline.py` sem histórico no hot path
- [x] `judge.py` e `justifier.py` alinhados ao `policy_trace`

### Sprint 4 — UI do Advogado (3h) · P3
- [x] Inbox conectada ao backend
- [x] Tela do caso com visualização de documentos
- [x] Card de recomendação com `policy_trace`
- [x] Registro de outcome

### Sprint 5 — Dashboard do Banco (2h) · P4
- [x] Endpoint agregado `/api/dashboard/metrics`
- [x] Dashboard básico com métricas principais
- [ ] Série temporal
- [ ] Filtros por período
- [ ] Economia realizada vs. estimada

### Sprint 6 — Backtest + Polish (2h) · P2 + P3
- [ ] Camada 6.1: taxonomia econômica por `Resultado micro`
- [ ] Camada 6.1: correção do histórico para êxito/não êxito
- [ ] Camada 6.2: `scripts/eval_policy.py`
- [ ] Camada 6.2: análise por cenários de `qtd_docs`
- [ ] Camada 6.3: prompt de justificativa polido
- [ ] Camada 6.3: melhorias finais de UX na tela do caso

### Sprint 7 — Entrega (2h) · P5
- [ ] Vídeo
- [ ] Slides
- [ ] `docs/policy_rationale.md`
- [ ] `SETUP.md` final

---

## 10. Decisões Técnicas e Trade-offs

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| V5 determinística no hot path | Histórico + retrieval + percentis online | Mais previsível, rápida e auditável |
| LLM nas pontas | LLM decidindo tudo | Extração e justificativa ganham com LLM; decisão e valor precisam ser estáveis |
| Inventário documental determinístico | Presença documental inferida pelo LLM | Reduz erro factual em contrato, extrato, comprovante, dossiê e laudo |
| Judge como revisão factual | Judge com poder de veto econômico | Evita conflito entre estatística e narrativa |
| Histórico só para backtest/calibração | Histórico na recomendação ao vivo | Remove latência e instabilidade do núcleo |
| Embeddings opcionais/offline | Embeddings obrigatórios no runtime | Não agregam ao fluxo principal da V5 |
| SQLite no MVP | Postgres desde o início | Menor atrito para o hackathon |
| Next.js + FastAPI | App monolítica full-stack | Melhor divisão entre UI e serviços Python |

---

## 11. Limitações Conhecidas

- O backtest ainda depende da normalização correta de `Resultado micro`.
- Parte do histórico pode não ter insumos suficientes para executar a V5 sem proxy.
- PDFs escaneados continuam fora do escopo do MVP.
- O dashboard ainda é agregado; falta corte temporal e financeiro mais fino.
- `policy/acordos_v1.yaml` permanece no repositório como legado, mas não representa mais o runtime principal.

---

## 12. Próximos Passos

1. Implementar `scripts/eval_policy.py` com saída pronta para slides.
2. Persistir classificação econômica derivada do outcome para alimentar métricas reais.
3. Adicionar simulações `what-if` da V5 para o jurídico.
4. Evoluir o dashboard para comparação entre resultado recomendado e resultado realizado.
5. Considerar embeddings apenas para analytics exploratório, sem tocar o motor decisório.

---

## 13. Critérios de Avaliação — Como Endereçamos

| Critério | Como atendemos |
|---|---|
| Leitura do problema | Política V5 focada em acordo vs. defesa com prova documental e racional econômico |
| Criatividade e usabilidade | Tela do advogado com recomendação explicável via `policy_trace` |
| Colaboração | Separação clara entre extração, motor V5, UI e dashboard |
| Execução | Pipeline real funcional nos casos exemplo |
| Uso de IA | LLM para extração, revisão factual e justificativa; estatística determinística para decisão e valor |

---

**Começar agora:** fechar Sprint 6 com `eval_policy.py`, régua por `Resultado micro` e polish final da interface.
