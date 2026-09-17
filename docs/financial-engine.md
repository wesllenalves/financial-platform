# Financial Engine

Status: proposed

The financial engine is pure Python: functions from explicit inputs to explicit outputs,
no database, no HTTP, no LLM. Everything a user sees as a number is produced here and is
unit-tested with hand-checked expected values.

## 1. Money rules

- `Decimal` everywhere; `float` is banned in this package (enforced by a test that
  inspects annotations and by review).
- Storage and display precision: 2 decimal places, `ROUND_HALF_UP`.
- Intermediate computations keep full precision and quantize **once**, at the boundary
  where a value becomes a result.
- Rates are `Decimal` with 6 decimals. Annual → monthly uses the effective conversion
  `(1 + annual) ** (1/12) - 1`, not division by 12, and the choice is stated wherever a
  rate is shown.
- Division guards: any ratio with a zero or negative denominator returns `None`, never
  `0` and never an exception. `None` renders as "—" with an explanation, because a
  fabricated zero is worse than a gap.
- Amounts are stored positive; direction comes from `transaction_type`.

## 2. Metric definitions

Every metric has one definition, stated here, implemented once, and shown in the UI via
tooltip. Ambiguous ones are called out.

| Metric | Definition |
| --- | --- |
| Monthly income | sum of `income` transactions with `transaction_date` in the month, excluding transfers |
| Monthly expenses | sum of `expense` transactions in the month, excluding transfers |
| Net cash flow | income − expenses for the month |
| Current balance | Σ account opening balances + Σ income − Σ expenses, up to today |
| Savings rate | (income − expenses) / income; `None` when income is 0 |
| Expenses by category | expense sums grouped by top-level category, with each category's share of total expenses |
| Expense trend | monthly expense totals for the last N months (default 6) |
| 3-month average | mean of the three complete months before the current one; a partial month is never averaged in |
| Fixed expense ratio | recurring expenses / income |
| Committed expenses | `pending` expenses with a due date inside the period |
| Available cash | current balance − committed expenses |
| Debt-to-income | total monthly debt payments / monthly income |
| Emergency reserve months | liquid balance / average monthly essential expenses (3 months) |

**Period convention.** Periods are calendar months in the user's timezone. The current
month is always marked partial, and comparisons against it are labelled
"month to date vs. the same days of previous months" — comparing 12 days against 31 is
the most common way a financial dashboard lies.

## 3. Recurrence detection

Deterministic, no AI:

1. Group expenses by `merchant_normalized` (fallback: normalized description).
2. Within a group, find occurrences in ≥ 3 of the last 6 months.
3. Require amount stability: standard deviation ≤ 15% of the mean, or exactly equal
   amounts for subscriptions.
4. Require interval stability: median gap between 26 and 35 days (monthly), or 6–8 days
   (weekly), or 88–96 (quarterly).
5. Emit a `RecurringSeries`: merchant, cadence, mean amount, first seen, last seen,
   expected next date, occurrence count.

A series that stops appearing for 2 expected cycles becomes `inactive` — that is exactly
the signal used for "unused subscription" findings (an active charge with no matching
usage is out of scope; a *cancelled-looking* series is not a leak).

## 4. Cash-flow projection (phase 2)

Deterministic, day-by-day, over a configurable horizon (30/60/90/180/365 days):

```
balance[d] = balance[d-1]
           + scheduled income on d
           + recurring income expected on d
           - scheduled expenses due on d
           - recurring expenses expected on d
           - installments due on d
           - debt payments due on d
```

- Known items (pending transactions with due dates, installments, debts) are certain.
- Recurring items are projected at their mean amount and expected date, and are flagged
  as *estimated* in the output so the UI can distinguish them.
- Output is a daily series plus the list of days where the projected balance goes
  negative, each with the events that caused it. The point of the feature is naming the
  day and the cause before it happens, not producing a single number.
- Assumptions (which items are estimates, what rate, what horizon) are returned with the
  projection, never hidden.

## 5. Debt strategies (phase 3)

Monthly amortization loop, fully deterministic:

```
for each month:
    for each debt:
        interest = outstanding * monthly_rate
        outstanding += interest
        payment = minimum_payment (+ surplus, for the prioritized debt)
        outstanding -= payment
```

Strategy differs only in who receives the surplus:

- **Avalanche** — highest effective monthly rate first.
- **Snowball** — smallest outstanding balance first.
- **Cash-flow priority** — highest `minimum_payment / outstanding` ratio first, i.e. the
  debt whose elimination frees the most monthly cash the soonest.

Output per strategy: payoff date, total interest paid, total paid, monthly payment
required, and the month-by-month schedule. The three are presented side by side; the app
states the trade-off (avalanche usually costs less interest, snowball usually frees a
debt sooner) and never declares one universally correct.

Simulations (`+R$100/month`, a one-off bonus) re-run the same function with modified
inputs — no separate code path, so a simulation can never disagree with the plan.

Guards: a payment plan that never amortizes (payment ≤ interest) returns an explicit
"this debt does not amortize at this payment level" result instead of looping; the loop
is capped at 600 months.

## 6. Wealth projection (phase 4)

Future value with monthly contributions:

```
FV = current * (1 + r)^n + contribution * (((1 + r)^n - 1) / r)
```

Three named scenarios (conservative / base / optimistic) whose rates are **configuration,
displayed with the result**, plus a stated inflation assumption and both nominal and real
values. No guarantee language anywhere; the output object carries an `assumptions` field
that the UI is required to render.

## 7. Rule engine

Rules are the deterministic layer that produces findings. Each rule is a class:

```python
class Rule(Protocol):
    id: str
    def evaluate(self, ctx: FinancialContext) -> list[Finding]: ...
```

`FinancialContext` is a pre-computed bundle (metrics, category totals, recurring series,
budgets, debts) so rules do no I/O and stay fast and testable.

Initial rules:

| Rule id | Fires when | Evidence |
| --- | --- | --- |
| `expense_category_growth` | category total > 3-month average × 1.25 and delta ≥ R$50 | category, current, average, delta, % |
| `high_fixed_expense_ratio` | fixed expenses / income > 0.60 | ratio, components |
| `negative_projected_cashflow` | projection dips below 0 in the horizon | date, balance, causing events |
| `subscription_growth` | active recurring series count or total up vs. 3 months ago | series list, delta |
| `repeated_bank_fee` | ≥ 2 fee-category transactions in a month | transactions, total |
| `duplicate_charge` | duplicate-detection strong match among existing transactions | both transaction ids |
| `budget_exceeded` | actual > planned for a category | planned, actual, delta |
| `unusual_transaction` | amount > mean + 3σ of the category's last 6 months, min 5 samples | transaction, threshold |
| `late_payment_fee` | interest/fee-category transactions present | transactions, total |
| `low_savings_rate` | savings rate < 0.10 for 2 consecutive months | rates |
| `debt_ratio_growth` | debt-to-income up ≥ 5 pp vs. 3 months ago | ratios |
| `small_repeated_purchases` | ≥ 8 transactions ≤ R$30 with the same merchant in a month | count, total |

**Severity is computed, not judged**: based on estimated monthly impact as a share of
income — critical ≥ 15%, high ≥ 8%, medium ≥ 3%, low below. The thresholds are in one
config module, documented, and visible to the user on request.

Every finding carries the transaction ids and numbers behind it. The LLM then phrases the
finding; it cannot change severity, impact or evidence.

## 8. Testing strategy for the engine

- Every metric and rule has table-driven unit tests with hand-computed expectations.
- Property tests: amounts never lose cents across aggregation; a projection with no
  events equals the starting balance; avalanche never pays more total interest than
  snowball for the same inputs (a real invariant, and a good bug detector).
- Golden-file tests over the seed dataset: the full metrics + findings output is
  snapshotted, so any accidental change in a financial number shows up as a diff in
  review.
- Edge cases that must have explicit tests: zero income, no transactions, single
  transaction, month boundaries and timezones, leap years, a 31st-of-month due date in
  February, negative balances, and a debt whose payment does not cover interest.
