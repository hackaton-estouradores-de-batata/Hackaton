<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes. Before changing routing, data fetching, or server/client boundaries, read the relevant guide in `node_modules/next/dist/docs/`.
<!-- END:nextjs-agent-rules -->

# Frontend Agent Notes

## Scope

`src/web/` is the Next.js frontend for the lawyer workspace and the bank dashboard. The app is already wired to the real backend. Do not reintroduce mocks, fake recommendation flows, or historical-mode UI.

## Current Product Contract

- The recommendation engine is **V5**, not the old historical/YAML/retrieval flow.
- The frontend should treat `policy_trace` as the main explanation surface for the recommendation.
- `casos_similares_ids` still exists for compatibility, but the runtime does not use it as a user-facing concept anymore.
- The dashboard currently reads only `/api/dashboard/metrics`.
- Case ingestion uses real multipart upload to `POST /api/cases`.

## Critical Invariants

- Do not reintroduce "modo histórico", "precedentes", or "casos similares" as primary UI.
- Keep `RecommendationCard` aligned with the V5 fields:
  - `matriz_escolhida`
  - `sub_estatistico`
  - `qtd_docs`
  - `documentos_presentes`
  - `p_suc`
  - `p_per`
  - `vej`
  - `abertura`
  - `alvo`
  - `teto`
  - `teto_pct`
  - `revisao_humana`
  - `uf_sem_historico_proprio`
- If the backend changes recommendation payload shape, update both:
  - `src/web/lib/types.ts`
  - `src/web/lib/api.ts`
- If the backend changes endpoint paths, update only through `src/web/lib/api.ts`; do not scatter raw fetches across pages/components.

## Key Files

- Lawyer case page:
  - `src/web/app/(advogado)/caso/[id]/page.tsx`
- Lawyer inbox:
  - `src/web/app/(advogado)/inbox/page.tsx`
- New case form:
  - `src/web/components/NewCaseForm.tsx`
- Recommendation UI:
  - `src/web/components/RecommendationCard.tsx`
- Outcome form:
  - `src/web/components/OutcomeForm.tsx`
- Dashboard:
  - `src/web/app/(banco)/dashboard/page.tsx`
- Typed API contract:
  - `src/web/lib/types.ts`
  - `src/web/lib/api.ts`

## Data Fetching Rules

- The app uses server components for page-level reads and a centralized API client in `src/web/lib/api.ts`.
- Keep fetches `cache: "no-store"` unless there is a clear reason to cache.
- Preserve graceful degradation already present in the lawyer case page:
  - case load failure is fatal
  - recommendation failure shows fallback UI
  - document list failure shows warning UI

## UI Guidance

- Preserve the existing visual language unless the task explicitly asks for redesign.
- `RecommendationCard` should stay V5-first:
  - decision badge
  - agreement range when applicable
  - confidence
  - factual review warning when `judge_concorda === false`
  - `Trace V5`
  - justification
  - applied rules
- The dashboard is still partial. Prefer incremental evolution over speculative metric panels that the backend does not support yet.

## Backend Reality the Frontend Should Respect

- `POST /api/cases` now uses the real pipeline and writes to SQLite. The backend recently mitigated lock errors by shortening transactions, but the UI should still surface API failures cleanly.
- `GET /api/cases/{id}/recommendation` returns V5 recommendations and may mark factual review via `judge_concorda` / `judge_observacao`.
- `GET /api/dashboard/metrics` returns aggregate operational metrics, not backtest output.

## Sprint 6 Context

- `Resultado micro` now matters for historical calibration and backtest, but not as a direct feature in the online recommendation UI.
- If Sprint 6 surfaces backtest insights in the frontend later, treat them as a separate reporting layer, not as part of the per-case recommendation card.

## Safe Change Checklist

Before finishing frontend work:

1. Update types if the payload changed.
2. Update normalization in `src/web/lib/api.ts` if numeric/boolean fields changed.
3. Check the lawyer case page for fallback states.
4. Run `npm run lint` in `src/web`.
