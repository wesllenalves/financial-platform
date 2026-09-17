# Financial Platform

AI-assisted personal financial management: import financial documents, turn them into
structured transactions, compute financial metrics deterministically, detect problems
with a rule engine, and use an LLM only to explain the results in plain language.

**Design principle:** every number is computed in Python with `Decimal`. The LLM explains,
it never calculates.

## Status

Phase 1 (MVP foundation) is running: registration and login, accounts, hierarchical
categories, manual income/expense/transfer entry, deterministic monthly metrics, category
breakdown, monthly trend, recurring-expense detection, and an Angular dashboard.

Document ingestion, the findings rule engine, and the AI assistant are specified in the
docs and not implemented yet. See
[docs/implementation-plan.md](docs/implementation-plan.md) for the milestone checklist.

## Documentation

| Document | Contents |
| --- | --- |
| [architecture.md](docs/architecture.md) | system shape, layering, module boundaries, resolved ambiguities |
| [domain-model.md](docs/domain-model.md) | entities, PostgreSQL schema, indexes, constraints |
| [document-processing.md](docs/document-processing.md) | ingestion pipeline, parsers, OCR, normalization, duplicate detection |
| [financial-engine.md](docs/financial-engine.md) | metric definitions, projections, debt strategies, rule engine |
| [ai-architecture.md](docs/ai-architecture.md) | provider abstraction, structured output, assistant tools, guardrails |
| [implementation-plan.md](docs/implementation-plan.md) | milestones, scope boundaries, known limitations |

## Stack

Angular + TypeScript · FastAPI + Pydantic + SQLAlchemy + Alembic · PostgreSQL ·
OpenAI behind a provider abstraction · Docker Compose for local development.

## Local development

```bash
cp .env.example .env
docker compose up
```

Frontend on `http://localhost:4200`, API and Swagger UI on `http://localhost:8000/docs`.

Without Docker:

```bash
cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/python -m app.cli.seed          # demo@example.com / demo12345
.venv/bin/uvicorn app.main:app --reload

cd ../frontend && npm install && npm start
```

## Tests

```bash
cd backend && .venv/bin/pytest          # needs a local PostgreSQL; creates a scratch database
cd backend && .venv/bin/ruff check . && .venv/bin/mypy app
cd frontend && npm test
```

The application runs without `OPENAI_API_KEY`: AI features return an "unavailable"
response and every deterministic feature keeps working.
