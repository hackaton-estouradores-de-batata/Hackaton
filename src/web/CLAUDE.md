@AGENTS.md

# Claude Quick Context

Use `AGENTS.md` as the source of truth. These are the high-risk points that usually matter first.

## What This Frontend Is Rendering

- Real backend only.
- Recommendation engine = **V5**.
- Explanation surface = `policy_trace`.
- Dashboard endpoint = `/api/dashboard/metrics`.

## Touch These Together

When the backend recommendation contract changes, update all of:

- `src/web/lib/types.ts`
- `src/web/lib/api.ts`
- `src/web/components/RecommendationCard.tsx`

When case ingestion changes, check:

- `src/web/components/NewCaseForm.tsx`
- `src/web/lib/api.ts`

When dashboard metrics change, check:

- `src/web/app/(banco)/dashboard/page.tsx`
- `src/web/lib/types.ts`
- `src/web/lib/api.ts`

## Current Frontend Invariants

- Do not reintroduce UI for `casos_similares`.
- Do not describe the recommendation as retrieval- or precedent-driven.
- Keep the lawyer case page resilient when recommendation/doc fetches fail.
- Keep V5 terms visible when useful: matrix, docs, VEJ, target, ceiling.

## Validation

Preferred check after frontend edits:

```bash
npm run lint
```
