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
