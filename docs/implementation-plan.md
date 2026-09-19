# Implementation Plan

Status: living document — update as milestones complete.
Last updated: 2026-09-17

Each milestone is a vertical slice: database → backend → API → frontend → tests. A
milestone is done when the feature is usable in the browser and the checks below pass.

Definition of done for every milestone:

1. relevant backend tests pass (`pytest`)
2. relevant frontend tests pass (`ng test`)
3. migrations apply and roll back cleanly
4. `docker compose up` starts the app and the feature works end to end
5. documentation updated
6. known limitations recorded here

---

## M0 — Foundations

- [x] Repository skeleton (`backend/`, `frontend/`, `docs/`, `docker-compose.yml`, `.env.example`)
- [x] `docker compose up` brings up postgres + backend + frontend
- [x] FastAPI app factory, settings, structured logging, correlation-id middleware, error envelope
- [x] Alembic wired, first empty migration, health endpoint
- [x] Tooling: ruff, mypy, pytest with coverage; Angular lint; CI running all of it

Deliverable: an empty but running, linted, tested, containerized app.

## M1 — Auth and user isolation

- [x] `users` table and migration
- [x] Register, login, refresh, `GET /api/v1/users/me`
- [x] Argon2 hashing, JWT access + refresh, `get_current_user` dependency
- [x] Angular shell: layout, navigation, login/register pages, auth interceptor, route guards
- [x] Tests: auth happy path, wrong password, expired token, and the first user-isolation test

Deliverable: a user can register, log in, and see an empty authenticated app.

## M2 — Accounts, categories, transactions

- [x] `accounts`, `categories`, `transactions` tables and migrations; seeded default category tree
- [x] Transaction CRUD with filtering (period, category, account, type, search) and pagination
- [x] Transfers as linked pairs, excluded from income/expense metrics
- [x] Angular: transaction list, create/edit dialog, category picker, account management
- [x] Tests: CRUD, validation, `Decimal` round-trip, user isolation per endpoint

Deliverable: manual financial tracking works end to end. **First genuinely useful version.**

## M3 — Financial metrics and dashboard

- [x] Metrics package (income, expenses, balance, savings rate, category distribution, trend)
- [x] Recurrence detection
- [x] `GET /api/v1/analysis/summary`, `/by-category`, `/trend`, `/recurring`
- [x] Angular dashboard: summary cards, income-vs-expense chart, category donut, trend line, upcoming bills
- [x] Seed command producing 12 months of realistic data
- [x] Tests: hand-computed metric expectations, golden-file snapshot over the seed data

Deliverable: the dashboard answers the spec's eight questions.

## M4 — Document ingestion

- [x] `documents` and `extracted_items` tables and migrations
- [x] Upload endpoint with validation (size, magic bytes, hash dedup) and safe storage
- [x] Pipeline skeleton with stage interfaces; parser registry
- [x] PDF parser, XML parser (generic + NF-e profile), JSON importer
- [x] Normalization (BRL amounts, day-first dates, merchant normalization) and field confidence
- [x] Duplicate detection producing warnings
- [x] Confirmation endpoints: confirm / edit-and-confirm / reject
- [x] Angular: upload with progress, extraction review screen with confidence highlighting and duplicate warnings
- [x] Tests: golden files per format, security negatives (XXE, bombs, oversized, wrong magic bytes), end-to-end confirm

Deliverable: a user uploads a boleto or NF-e and confirms it into a transaction.

## M5 — Image/OCR

- [x] `OcrEngine` interface, Tesseract implementation, image pre-processing
- [x] Scanned-PDF routing to the image path
- [x] Tests with synthetic receipt images

Deliverable: photographed receipts are importable. Split from M4 so M4 can ship sooner.

## M6 — Rule engine and findings

- [x] `findings` table, rule interface, `FinancialContext` builder
- [x] The twelve initial rules with computed severity
- [x] `POST /api/v1/analysis/run`, `GET /api/v1/findings`
- [x] Angular: findings list with evidence expansion
- [x] Tests: table-driven per rule, severity thresholds, idempotent re-runs

Deliverable: deterministic findings, with evidence, and no AI involved.

## M7 — AI layer

- [ ] `LLMProvider` protocol, `OpenAIProvider`, `NullProvider`, `FakeProvider`, registry
- [ ] Versioned prompt templates; `ai_interactions` logging
- [ ] Structured-output explanation of findings with the "no invented numbers" validator
- [ ] Angular: plain-language explanation on each finding, with a visible fallback
- [ ] Tests: provider contract suite, hostile structured-output fixtures, degradation with no API key

Deliverable: findings explained in plain language, grounded in real numbers.

## M8 — Assistant

- [ ] Tool registry over application services with server-injected `user_id`
- [ ] Tool-calling loop with call and time budgets
- [ ] `POST /api/v1/ai/ask` returning answer plus the tool outputs used
- [ ] Angular assistant panel showing the data behind each answer
- [ ] Tests: tool argument validation, loop limits, isolation (a tool can never read another user)

Deliverable: **the MVP definition of done from spec §45 is met.**

## M9 — Hardening before phase 2

- [ ] Rate limiting on auth and upload; audit log on sensitive operations
- [ ] Full user-isolation test matrix across every endpoint
- [ ] Performance pass with 50k transactions (index verification, query counts)
- [ ] Accessibility and responsive pass; error and empty states
- [ ] README, setup guide, and architecture docs refreshed

---

## Phase 2 (spec §35)

Budgets and budget tracking · recurring transaction management · bills · alerts ·
money-leak detector · financial audit report · anomaly detection · 30/60/90-day cash-flow
projection · recommendations with accept/dismiss/snooze.

## Phase 3 (spec §36)

Debt registry · avalanche / snowball / cash-flow strategies · payoff projections and
simulations · contingency scenarios · emergency-fund planner.

## Phase 4 (spec §37)

Wealth planning and long-term projections · financial goals · scenario simulation ·
advanced assistant · reports with PDF/spreadsheet export.

---

## Explicitly out of MVP scope

Bank/Open Finance connections · mobile apps · multi-currency · shared/household accounts
· investment portfolio tracking · tax reporting · notifications (email/push) ·
report export · background job infrastructure.

## Known limitations (update as they are discovered)

- Credit card bills are not modelled in the MVP; card purchases are expenses on their own
  date, so short-horizon cash flow will be optimistic for heavy card users.
- Document processing is synchronous; large scanned PDFs will make the upload request
  slow before a worker is introduced.
- OCR quality on photographed receipts is unverified until M5 runs against real-world
  samples.
- Recurrence detection needs ~3 months of history to be useful, so a new user sees fewer
  findings.

## Checklist discipline

Tick boxes only when the milestone's definition of done is satisfied. When a milestone
finishes, record: what shipped, test results, migrations added, and any new limitation.
