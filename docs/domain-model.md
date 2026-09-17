# Domain Model and Database Schema

Status: proposed
Conventions: all ids are `UUID` (v4, generated in the application); all timestamps are
`TIMESTAMPTZ`; all monetary columns are `NUMERIC(14, 2)`; all rate columns are
`NUMERIC(9, 6)` (a rate of 2.5% is stored as `0.025000`).

Every table that holds user data carries `user_id` with a foreign key to `users` and an
index whose first column is `user_id`, because every query is user-scoped.

## Entity overview

```
users ──< accounts ──< transactions >── categories (self-referencing tree)
  │                        │
  │                        └── documents (nullable: manual transactions have none)
  ├──< documents ──< extracted_items
  ├──< budgets
  ├──< debts ──< debt_payments        (phase 3)
  ├──< goals                          (phase 4)
  ├──< findings ──< recommendations
  └──< ai_interactions
```

## users

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| name | TEXT NOT NULL | |
| email | CITEXT NOT NULL UNIQUE | case-insensitive uniqueness |
| password_hash | TEXT NOT NULL | Argon2id |
| currency | CHAR(3) NOT NULL DEFAULT 'BRL' | ISO 4217 |
| locale | TEXT NOT NULL DEFAULT 'pt-BR' | |
| timezone | TEXT NOT NULL DEFAULT 'America/Sao_Paulo' | |
| created_at / updated_at | TIMESTAMPTZ NOT NULL | |

## accounts

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK → users ON DELETE CASCADE | |
| name | TEXT NOT NULL | |
| type | ENUM(`checking`,`savings`,`cash`,`credit_card`,`investment`) NOT NULL | |
| opening_balance | NUMERIC(14,2) NOT NULL DEFAULT 0 | see architecture decision 2 |
| institution | TEXT NULL | |
| active | BOOLEAN NOT NULL DEFAULT true | |
| created_at / updated_at | TIMESTAMPTZ | |

Unique: `(user_id, name)`.

## categories

Hierarchical, one level of nesting in the UI but the model allows arbitrary depth.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK NULL | `NULL` = system default category, visible to everyone |
| parent_id | UUID FK → categories NULL | |
| name | TEXT NOT NULL | |
| kind | ENUM(`income`,`expense`) NOT NULL | a category belongs to one side |
| essentiality | ENUM(`essential`,`important`,`flexible`,`optional`) NULL | default for contingency planning, overridable per transaction |
| system | BOOLEAN NOT NULL DEFAULT false | seeded defaults cannot be deleted |
| archived | BOOLEAN NOT NULL DEFAULT false | never hard-delete a used category |

Unique: `(user_id, parent_id, name)`. Index on `(user_id, parent_id)`.

Seeded tree (from the spec): Housing (Rent, Condominium, Electricity, Internet), Food
(Groceries, Restaurants, Delivery), Transportation (Fuel, Maintenance, Insurance), plus
Health, Education, Subscriptions, Debt & Fees, Other; income side: Salary, Freelance,
Investments, Other Income.

## transactions

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK NOT NULL | |
| account_id | UUID FK → accounts NOT NULL | |
| document_id | UUID FK → documents NULL | provenance |
| transaction_type | ENUM(`income`,`expense`,`transfer`) NOT NULL | |
| description | TEXT NOT NULL | |
| amount | NUMERIC(14,2) NOT NULL CHECK (amount > 0) | sign is carried by `transaction_type`, never by the number |
| transaction_date | DATE NOT NULL | when it economically happened |
| due_date | DATE NULL | |
| payment_date | DATE NULL | set when `status = paid` |
| category_id | UUID FK → categories NULL | |
| merchant | TEXT NULL | |
| merchant_normalized | TEXT NULL | lowercased, stripped — used for recurrence and dedup |
| payment_method | ENUM(`cash`,`debit`,`credit`,`pix`,`boleto`,`transfer`,`other`) NULL | |
| installment_number | SMALLINT NULL | |
| installment_count | SMALLINT NULL | |
| installment_group_id | UUID NULL | links installments of one purchase |
| recurring | BOOLEAN NOT NULL DEFAULT false | user-confirmed recurrence |
| recurrence_group_id | UUID NULL | set by recurrence detection |
| status | ENUM(`pending`,`paid`,`overdue`,`canceled`) NOT NULL DEFAULT `paid` | |
| source | ENUM(`manual`,`pdf`,`xml`,`json`,`image`,`ai_extraction`) NOT NULL | |
| confidence_score | NUMERIC(4,3) NULL | extraction confidence, never used in math |
| transfer_peer_id | UUID FK → transactions NULL | the other leg of a transfer |
| notes | TEXT NULL | |
| created_at / updated_at | TIMESTAMPTZ | |

Indexes:

- `(user_id, transaction_date DESC)` — the dashboard's main access path
- `(user_id, category_id, transaction_date)` — category breakdowns
- `(user_id, account_id, transaction_date)`
- `(user_id, due_date) WHERE status IN ('pending','overdue')` — upcoming bills
- `(user_id, merchant_normalized, amount, transaction_date)` — duplicate detection

Constraints:

- `installment_number <= installment_count`
- `payment_date IS NOT NULL` when `status = 'paid'` (enforced in the service, not the DB,
  because backfilled data may be incomplete)

**Transfers** are stored as two rows (one outgoing, one incoming) linked by
`transfer_peer_id`, and are excluded from income and expense metrics. This keeps the
income/expense aggregation a plain `WHERE transaction_type = ...` and avoids double
counting.

## documents

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK NOT NULL | |
| filename | TEXT NOT NULL | original name, sanitized |
| file_type | ENUM(`pdf`,`xml`,`json`,`png`,`jpeg`) NOT NULL | from sniffed content, not the extension |
| content_hash | CHAR(64) NOT NULL | SHA-256 of the bytes |
| size_bytes | INTEGER NOT NULL | |
| storage_path | TEXT NOT NULL | opaque path, never user-controlled |
| processing_status | ENUM(`uploaded`,`processing`,`awaiting_confirmation`,`confirmed`,`failed`,`rejected`) NOT NULL | |
| error_message | TEXT NULL | |
| extraction_metadata | JSONB NULL | parser used, page count, OCR engine, model, durations |
| extraction_confidence | NUMERIC(4,3) NULL | |
| uploaded_at / processed_at | TIMESTAMPTZ | |

Unique: `(user_id, content_hash)` — re-uploading identical bytes is rejected with a clear
message rather than silently creating a second document.

## extracted_items

One row per candidate transaction found in a document. This is the staging area that
makes the spec's "never silently create a transaction" rule structural: nothing reaches
`transactions` without a user confirming an `extracted_item`.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| document_id | UUID FK → documents ON DELETE CASCADE | |
| user_id | UUID FK NOT NULL | denormalized for scoping |
| raw_payload | JSONB NOT NULL | exactly what the parser/LLM produced |
| normalized_payload | JSONB NOT NULL | after normalization: amounts, dates, merchant |
| field_confidence | JSONB NOT NULL | per-field confidence |
| duplicate_of_transaction_id | UUID FK NULL | suspected duplicate, warning only |
| duplicate_reason | TEXT NULL | |
| status | ENUM(`pending`,`confirmed`,`rejected`,`edited_confirmed`) NOT NULL | |
| created_transaction_id | UUID FK → transactions NULL | set on confirmation |

## budgets (phase 2)

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK | |
| period | DATE NOT NULL | first day of the month |
| category_id | UUID FK NOT NULL | |
| planned_amount | NUMERIC(14,2) NOT NULL | |

Unique: `(user_id, period, category_id)`. `actual_amount` is **not stored** — it is
computed from transactions, so it can never go stale.

## debts (phase 3)

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK | |
| creditor | TEXT NOT NULL | |
| original_balance / outstanding_balance | NUMERIC(14,2) NOT NULL | |
| interest_rate_monthly | NUMERIC(9,6) NOT NULL | effective monthly rate; the API also accepts an annual rate and converts |
| monthly_payment / minimum_payment | NUMERIC(14,2) NULL | |
| due_day | SMALLINT NULL | day of month (1–31), clearer than a single date |
| number_of_installments / remaining_installments | SMALLINT NULL | |
| priority | SMALLINT NULL | user-set ordering |
| status | ENUM(`active`,`paid_off`,`renegotiated`,`defaulted`) NOT NULL | |

## goals (phase 4)

`id, user_id, name, target_amount, current_amount, target_date, priority, status`.

## findings

Output of the deterministic rule engine. Persisted so explanations, recommendations and
the UI all reference the same immutable object.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK | |
| rule_id | TEXT NOT NULL | e.g. `expense_category_growth` |
| period | DATE NOT NULL | analysis period |
| severity | ENUM(`critical`,`high`,`medium`,`low`) NOT NULL | derived from financial impact, not judgement |
| title | TEXT NOT NULL | deterministic, template-generated |
| evidence | JSONB NOT NULL | the numbers and transaction ids behind the finding |
| estimated_monthly_impact | NUMERIC(14,2) NULL | |
| created_at | TIMESTAMPTZ | |

Unique: `(user_id, rule_id, period, evidence_key)` where `evidence_key` is a stable hash
stored as a generated column, so re-running an analysis updates instead of duplicating.

## recommendations

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID PK | |
| user_id | UUID FK | |
| finding_id | UUID FK → findings | a recommendation always points at evidence |
| explanation | TEXT NOT NULL | LLM-generated wording |
| suggested_action | TEXT NOT NULL | |
| estimated_monthly_savings | NUMERIC(14,2) NULL | computed, not invented by the LLM |
| status | ENUM(`new`,`accepted`,`dismissed`,`snoozed`) NOT NULL DEFAULT `new` | |
| snoozed_until | DATE NULL | |

## ai_interactions

Audit and cost tracking. `id, user_id, correlation_id, provider, model, purpose,
prompt_template_id, input_tokens, output_tokens, latency_ms, status, error_code,
created_at`. **No prompt or response text is stored** — financial content stays out of
the log.

## audit_log

Sensitive operations: login, failed login, document upload, extraction confirmation,
transaction delete, data export. `id, user_id, action, resource_type, resource_id,
correlation_id, ip_hash, created_at, metadata JSONB`.

## Deletion policy

Transactions and documents are soft-deleted (`deleted_at`) for 30 days so a mis-click is
recoverable; the spec forbids silently overwriting financial data. Every query filters
`deleted_at IS NULL`. A user deleting their account cascades everything.

## Migrations

Alembic, one migration per logical change, always with a working `downgrade`. Migration
tests assert `upgrade head` then `downgrade base` runs clean on an empty database.
