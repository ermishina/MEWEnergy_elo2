# Contributing Guidelines

Welcome! This guide keeps contributions consistent, reviewable, and compliant with the MEWEnergy ELO2 capstone requirements.

## 🚀 Getting started
1) Clone and enter the repo (SSH/HTTPS as you prefer).  
2) Create a venv: `python -m venv .venv && source .venv/bin/activate`.  
3) Install deps: `pip install -r scripts/requirements.txt`.  
4) Copy `.env.example` to `.env` and set `NREL_API_KEY` + `SECRET_KEY` for local runs.  
5) Run `python scripts/app.py` to sanity check the Flask prototype.

## 🧰 Tools and stack
- Python 3.10+ with `black`, `ruff`, and `pytest` (already in `scripts/requirements.txt`).
- Flask prototype and helpers under `scripts/`; tests live in `tests/`.
- Git + GitHub project board for task tracking; main is protected.

## 🔄 Workflow and branches
- Open PRs from feature branches (`feature/<topic>`, `bugfix/<topic>`, `docs/<topic>`). Keep them small.
- Rebase on `main` before opening a PR; avoid merge commits.
- Use short, imperative commits (e.g., `Add pvwatts client`, `Fix rate parser tests`).
- Tag each milestone from the approved `main` commit (M0–M5) per syllabus.

## ✅ Pull requests
- Use the PR template `.github/pull_request_template.md`.
- Requirements for approval:
  - `black .`, `ruff check .`, and `pytest -q` all pass.
  - Docs updated when behavior, interfaces, data paths, or commands change.
  - Secrets are kept out of git; data policy respected.
- At least one reviewer signs off; address or justify all comments.

## 🧪 Code standards and tests
- Style: 4-space indent, max line length 88; snake_case for functions/files, CamelCase for classes, UPPER_SNAKE for constants.
- Tests: run `pytest -q` from repo root; add/adjust tests in `tests/` with your changes.
- Keep modules small and single-purpose; shared logic lives in `scripts/`.

## 🔐 Data and secrets
- Data home: `2_data_collection/data/`.
  - Raw pulls in `raw/` stay local (git-ignored) except small curated samples already present.
  - Processed CSV: `processed/solar_analysis_dataset.csv` (8 sample locations). Regenerate via the M2 pipeline; commit only updated, compact versions needed for milestones.
- Never commit API keys or secrets. Use `.env`; update `.env.example` when new vars are required.
- Document regeneration steps in the relevant README when data changes.

## 📝 Documentation expectations
- Keep milestone READMEs current: deliverables, artifacts/visuals, survey status, tags, and retrospectives.
- Update root `README.md` when structure, commands, or artifact locations change.
- If schemas or pipeline steps change, update `2_data_collection/data/README.md` and note downstream impacts in `3_data_analysis/README.md`.

## 🧭 Testing and quality checklist
- Run: `black .`, `ruff check .`, and `pytest -q` before pushing.
- Include or update tests with code changes; prefer fast, deterministic checks.
- Call out known limitations or uncertainties in docs and PR notes.
