# Architecture

Status: proposed (pre-implementation)
Scope: whole product, MVP-first

## 1. Goal

A personal financial management platform that ingests financial documents and manual
entries, turns them into structured transactions, computes deterministic financial
metrics, detects findings with a rule engine, and uses an LLM only to explain those
findings in plain language.

The guiding constraint: **money is computed in Python with `Decimal`, never by the LLM.**

## 2. Shape of the system

A **modular monolith**: one FastAPI application, one PostgreSQL database, one Angular
SPA. No message broker, no workers, no microservices in the MVP.

```
Angular SPA  ──HTTP/JSON──>  FastAPI app  ──SQLAlchemy──>  PostgreSQL
                                  │
                                  ├─> document parsers (pdf / xml / json / image)
                                  └─> LLM provider abstraction ──> OpenAI
```

Why: the product has one database, one deployment target and a single team. Splitting
into services would add operational cost and buy nothing. The module boundaries below
are enforced in code (import direction), so extraction later is mechanical if ever
needed.

### Deferred infrastructure and why

| Component | Deferred until |
| --- | --- |
| Celery / RQ background workers | document processing exceeds ~10 s or concurrency hurts request latency |
| Redis | a real caching or queue need exists |
| Object storage (S3) | deployment stops having a durable local volume |
| LangGraph | the assistant needs multi-step planning beyond one tool-calling loop |
| Vector store / RAG | we need retrieval over unstructured text, which transactions are not |

## 3. Layering

Strict, one-directional:

```
API (routers, request/response schemas, auth dependency)
  ↓ calls
Application services (use cases, transactions/UoW, orchestration)
  ↓ calls
Domain (pure functions + entities: money math, rules, projections)
  ↓ uses
Repositories (SQLAlchemy queries, always user-scoped)
  ↓
PostgreSQL
```

Rules:

- Routers contain no business logic — they validate input, call one service, map output.
- Domain code imports nothing from FastAPI, SQLAlchemy or the AI layer. It takes plain
  dataclasses/Pydantic models and returns results. This is what makes it unit-testable.
- The AI layer never touches repositories or the session. It calls application services
  through a small, explicit tool registry.
- Every repository method takes `user_id` as a required argument. There is no repository
  method that can read another user's rows.

## 4. Backend module map

```
backend/
  app/
    main.py                  # app factory, router registration, middleware
    core/                    # config, security, logging, correlation id, errors, db session
    shared/                  # money helpers, date/period helpers, base schemas, pagination
    auth/                    # register, login, JWT issuing, current-user dependency
    users/
    accounts/
    categories/
    transactions/
    documents/               # upload, storage, document records, confirmation flow
    document_processing/     # classification, parsers, extraction, normalization, dedup
    metrics/                 # deterministic financial metrics (income, expenses, trends)
    rules/                   # rule engine + findings
    ai/                      # provider abstraction, prompts, tools, structured outputs
    analysis/                # analysis modules composed of metrics + rules + AI explanation
    budgets/     (phase 2)
    debts/       (phase 3)
    goals/       (phase 4)
    cashflow/    (phase 2: projections)
    reports/     (phase 4)
  tests/
  alembic/
  pyproject.toml
```

Each module has the same internal shape, so navigation is predictable:

```
<module>/
  router.py        # FastAPI routes
  schemas.py       # Pydantic request/response models
  service.py       # application service
  repository.py    # data access (user-scoped)
  models.py        # SQLAlchemy ORM models
  domain.py        # pure logic, when the module has any
```

Allowed import direction: `router → service → {domain, repository}`. Cross-module calls
go service-to-service, never router-to-repository of another module.

## 5. Frontend module map

```
frontend/src/app/
  core/          # http interceptors (auth, correlation id), guards, api client, error handling
  shared/        # dumb presentational components, pipes (currency, percent), layout
  features/
    auth/
    dashboard/
    transactions/
    documents/
    analysis/
    assistant/
    settings/
```

Rules:

- Feature modules are lazy-loaded standalone Angular routes.
- **No financial calculation in Angular.** The frontend formats and renders values the
  API already computed. A sum shown on a card comes from the API, not from a `reduce`.
- Data access lives in per-feature services; components receive data and emit events.
- Charts (Chart.js) are wrapped in shared components that take already-shaped series.

## 6. Cross-cutting concerns

**Auth.** Email + password, Argon2 hashing, JWT access tokens (short-lived) with refresh
tokens. `get_current_user` dependency resolves the user; every financial router depends
on it.

**Authorization.** There are no roles in the MVP. The only rule is ownership, enforced in
repositories (`WHERE user_id = :user_id`) and verified by dedicated isolation tests: for
each resource, user B requesting user A's id must get 404.

**Money.** `NUMERIC(14, 2)` in PostgreSQL, `Decimal` in Python, string in JSON to avoid
float coercion in JavaScript. Interest and rate math uses `Decimal` with an explicit
quantization step documented in `financial-engine.md`. Floats are banned for money; a
lint/test check guards against `float` in monetary code paths.

**Errors.** One error envelope: `{"error": {"code", "message", "details", "correlation_id"}}`.
Domain errors map to HTTP codes in a single exception handler.

**Logging.** Structured JSON logs, one correlation id per request, propagated to AI calls.
Logged for AI calls: provider, model, latency, token counts, prompt template id, finding
ids. Never logged: raw document content, extracted personal data, credentials.

**Config.** Pydantic `Settings` from environment. No secret in source, `.env.example`
committed with empty values.

## 7. Local development

`docker compose up` starts `postgres`, `backend` (uvicorn with reload), `frontend`
(ng serve). Migrations run on backend start in dev. Seed data is a CLI command
(`python -m app.cli seed`) producing a realistic 12-month financial history so dashboards
and analyses are demonstrable without uploading anything.

The app must start and be usable with `OPENAI_API_KEY` unset: the AI layer falls back to
a `NullProvider` that returns a clear "AI explanation unavailable" response. Deterministic
features keep working. This keeps tests and contributors unblocked.

## 8. Ambiguities in the specification, and how they are resolved

These are the points where the specification is open; each has a decision so work can
start. They are cheap to revisit.

1. **Single or multi currency.** Spec stores `currency` on the user but transactions have
   no currency field. *Decision:* one currency per user in the MVP, stored on the user,
   no conversion. Transaction-level currency is a later migration.
2. **Account balance source of truth.** `Financial Account.current_balance` can drift from
   the sum of transactions. *Decision:* `current_balance` is an opening balance set by the
   user; the displayed balance is opening balance plus the transaction sum, computed on
   read. No stored running balance in the MVP.
3. **Credit card modelling.** A card purchase is an expense, but the cash leaves on the
   bill due date. *Decision:* MVP treats a credit card as an account and each purchase as
   an expense on its own date; the bill itself is not modelled. Cash-flow projection
   (phase 2) introduces a `credit_card_bill` aggregation. Flagged as the largest known
   modelling gap.
4. **Installments.** Spec has `installment_number`/`installment_count` but no parent link.
   *Decision:* add `installment_group_id` so installments of one purchase are queryable
   together.
5. **"Committed expenses" and "available cash"** are undefined in the spec. *Decision:*
   committed = future-dated unpaid expenses with a known due date inside the period;
   available = current balance minus committed. Definitions live in `financial-engine.md`
   and are shown in the UI as tooltips.
6. **Budget `period`.** *Decision:* calendar month, stored as `DATE` at the first of the
   month. No custom periods in the MVP.
7. **Confidence score semantics.** Spec uses it on both documents and transactions.
   *Decision:* it is a per-extraction number in `[0, 1]` produced by the extraction
   pipeline, recorded on the document and copied to a transaction created from it; it is
   never used in financial math, only to drive the confirmation UI.
8. **Categorization of extracted transactions.** *Decision:* deterministic merchant-rule
   matching first; LLM categorization only for what the rules do not match, and only as a
   *suggestion* the user confirms.
9. **OCR engine.** Spec says "OCR abstraction" without naming one. *Decision:* define the
   `OcrEngine` interface in the MVP with a Tesseract implementation, and allow an
   LLM-vision implementation behind the same interface. Image support ships after PDF.
10. **Financial health score.** Spec warns against opaque scores. *Decision:* no single
    score. Show the individual indicators with their formula and inputs visible.
11. **Recommendation actions** ("Accept", "Create Goal"). *Decision:* phase 2; the MVP
    stores recommendation state (`new` / `dismissed`) only, and no AI-initiated write ever
    happens without an explicit user action.
12. **Multi-tenancy / sharing** (household accounts). Not in the spec's scope. Not built.

## 9. Architectural decisions worth recording

| Decision | Reasoning |
| --- | --- |
| Modular monolith | one team, one database, no independent scaling need |
| Rule engine separate from LLM | findings must be reproducible and testable; the LLM only phrases them |
| Provider interface for LLMs | swapping OpenAI for Anthropic/Gemini/Ollama must not touch financial code |
| `Decimal` + `NUMERIC`, money as JSON strings | float rounding is unacceptable in financial data, and JS numbers are floats |
| Synchronous document processing in the MVP | avoids a broker; revisit when parsing exceeds ~10 s |
| Confirmation step before persisting extractions | required by the spec's critical document rule; also the safest default |
| User-scoped repositories | makes cross-user leakage a compile-time-ish concern rather than a review concern |
