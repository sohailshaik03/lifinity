<<<<<<< HEAD
RetailSight
===============

Enterprise-ready scaffolding for the RetailSight Streamlit application.

Overview
- Purpose: inventory & sales upload + analytics app built with Streamlit and MySQL.
- Structure: repository splits UI, services, repositories and DB layer.

Quickstart (dev)

1. Copy `.env.example` to `.env` and fill values.
2. Build & run with Docker Compose:

```bash
docker compose up --build
```

3. Or run locally in a Python venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
streamlit run app.py
```

Recommended workflow
- Use the provided `requirements-dev.txt` for linters/tests.
- Pre-commit hooks are configured to run formatting and basic checks.
- CI (GitHub Actions) runs linting and tests on PRs.

Important files
- `Dockerfile`, `docker-compose.yml` — local dev with MySQL.
- `.env.example` — environment variables needed by the app.
- `.github/workflows/ci.yml` — CI pipeline for lint/tests.
- `migrations/` — SQL migration stubs and Alembic guidance.

Security & deployment notes
- Do not commit secrets — use environment or secrets manager.
- Back up DB schema before altering enums or destructive operations.
- Consider using managed MySQL and secrets for production.

Next steps
- Add full Alembic migrations and production deployment manifest.
- Add integration tests (DB-backed) and e2e tests for critical flows.

LICENSE
- Please add project license as required by your organization.
=======
# Retailsights
Retailsights
>>>>>>> d11a015f405b5be4ce3390ad12ae11fc1e78978b
