# Repository Guidelines

## Project Structure & Module Organization

This repository is currently documentation-first. Use `README.md` for the product overview, `PROJECT_SKELETON.md` for the target architecture, and `TEAM.md` for execution planning. Store source case material under `arquivos_adicionais/` and preserve the existing per-case layout and numbered filenames such as `Caso_01_.../01_Autos_Processo_...pdf`.

The `hackathon-ufmg-2026/` path is tracked as a subproject pointer and may be empty in this clone, so coordinate before changing its state. When implementation begins, follow the planned structure in `PROJECT_SKELETON.md`: `src/web` for Next.js, `src/api` for FastAPI, plus `policy/`, `data/`, `docs/`, and `scripts/`.

## Build, Test, and Development Commands

No runnable app, build script, or automated test command is committed yet. For day-to-day contribution work, use:

```bash
git status
git log --oneline --no-merges -5
find arquivos_adicionais -maxdepth 2 -type f | sort
```

Use these to review local edits, inspect recent history, and confirm supporting files are still present after reorganizing docs. If you add executable code, include real setup and run commands in `SETUP.md` within the same PR.

## Coding Style & Naming Conventions

Keep Markdown concise, heading-driven, and specific to the legal-tech scope of the project. Prefer Portuguese for product and legal content because the existing repository materials follow that language. Use descriptive canonical filenames in the current style: `README.md`, `PROJECT_SKELETON.md`, `TEAM.md`.

Do not rename case folders or remove numeric file prefixes; they encode document order and make review easier.

## Testing Guidelines

There is no automated test suite yet. For documentation changes, manually verify links, paths, and command examples. For future code, place backend tests under `src/api/tests/` and frontend tests near the relevant UI module, then document the test command in `SETUP.md`.

## Commit & Pull Request Guidelines

Recent history includes both useful messages and placeholders like `wewr` and `.`. Do not continue that pattern. Prefer short, imperative commit subjects such as `Refine README architecture section` or `Add case-ingestion notes`.

Pull requests should state the scope, list affected docs or data paths, and separate binary/data updates from prose edits whenever possible. Include screenshots only when the PR introduces UI work.


## vexp <!-- vexp v2.0.11 -->

**MANDATORY: use `run_pipeline` — do NOT grep or glob the codebase.**
vexp returns pre-indexed, graph-ranked context in a single call.

### Workflow
1. `run_pipeline` with your task description — ALWAYS FIRST (replaces all other tools)
2. Make targeted changes based on the context returned
3. `run_pipeline` again only if you need more context

### Available MCP tools
- `run_pipeline` — **PRIMARY TOOL**. Runs capsule + impact + memory in 1 call.
  Auto-detects intent. Includes file content. Example: `run_pipeline({ "task": "fix auth bug" })`
- `get_skeleton` — compact file structure
- `index_status` — indexing status
- `expand_vexp_ref` — expand V-REF placeholders in v2 output

### Agentic search
- Do NOT use built-in file search, grep, or codebase indexing — always call `run_pipeline` first
- If you spawn sub-agents or background tasks, pass them the context from `run_pipeline`
  rather than letting them search the codebase independently

### Smart Features
Intent auto-detection, hybrid ranking, session memory, auto-expanding budget.

### Multi-Repo
`run_pipeline` auto-queries all indexed repos. Use `repos: ["alias"]` to scope. Run `index_status` to see aliases.
<!-- /vexp -->