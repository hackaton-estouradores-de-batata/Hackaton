# Backlog — Correções e Melhorias pós-análise

> Gerado em 2026-04-18. Prioridade: ALTA → MÉDIA → BAIXA.

---

## ~~Etapa 1 — Judge ativo~~ ✅ Falso alarme

O `judge_concorda: True` em `decision_engine.py` é o valor inicial do payload, sobrescrito imediatamente por `_apply_judge_and_justification()` em `recommendation_pipeline.py` (que chama `review_recommendation_with_judge()`). O judge já está funcional no pipeline real.

---

## Etapa 2 — Sentença para casos de acordo (MÉDIA)

**Problema:** Quando decisao=acordo, `sentença` fica `null` no outcome. Os casos resolvidos por acordo não aparecem no `resultado_micro` do dashboard. `MICRO_RESULT_ACORDO` existe na política mas nunca é populado.

**Tarefas:**
- [ ] 2.1 — No backend (`outcomes.py`), quando `resultado_negociacao == "aceito"`, gravar `sentenca = "acordo"` automaticamente
- [ ] 2.2 — Verificar que `resultado_micro` do dashboard começa a contar casos de acordo

**Arquivos:** `src/api/app/routers/outcomes.py`

---

## Etapa 3 — Opção "extinto" no OutcomeForm (BAIXA)

**Problema:** O engine analítico suporta `MICRO_RESULT_EXTINTO` mas o `OutcomeForm` só oferece `procedente | improcedente | parcial`. Casos extintos sem mérito são perdidos.

**Tarefas:**
- [ ] 3.1 — Adicionar opção `extinto` no ToggleGroup de sentença do `OutcomeForm.tsx`
- [ ] 3.2 — Atualizar tipo `Sentenca` em `src/web/lib/types.ts`
- [ ] 3.3 — Garantir que `extinto` não exige campos de condenação/custos (igual ao `improcedente`)

**Arquivos:** `src/web/components/OutcomeForm.tsx`, `src/web/lib/types.ts`

---

## Etapa 4 — Limpeza dos diretórios analytics duplicados (BAIXA)

**Problema:** Há dois módulos: `src/api/analytics/` e `src/api/app/analytics/`. Apenas o de dentro de `app/` é usado. O módulo externo é dead code.

**Tarefas:**
- [ ] 4.1 — Confirmar que nenhum import usa `src/api/analytics/` (fora de `app/`)
- [ ] 4.2 — Remover `src/api/analytics/` se confirmado como dead code

**Arquivos:** `src/api/analytics/`, `src/api/app/analytics/`

---

## Status

| Etapa | Descrição | Status |
|-------|-----------|--------|
| 1 | Judge ativo | ✅ Falso alarme — já funcionava |
| 2 | Sentença para acordos | ✅ Concluído |
| 3 | Opção extinto no form | ✅ Concluído |
| 4 | Limpeza analytics duplicado | ✅ Concluído |
