# AI Architecture

Status: proposed

## 1. The one rule

The LLM **explains**; Python **computes**. Every number a user sees originates in a
deterministic service. The LLM receives already-computed numbers and turns them into
sentences, or it selects which computation to run — it never performs arithmetic that the
user will rely on.

Consequences:

- Balances, totals, ratios, interest, amortization, projections: Python.
- Wording, grouping, prioritization narrative, answering "why": LLM.
- If the LLM is unavailable, every deterministic feature still works and the UI shows the
  findings without prose.

## 2. Provider abstraction

```python
class LLMProvider(Protocol):
    name: str

    def generate(self, messages: list[Message], *, options: LLMOptions) -> LLMResponse: ...
    def stream(self, messages: list[Message], *, options: LLMOptions) -> Iterator[str]: ...
    def structured_output(
        self, messages: list[Message], schema: type[BaseModelT], *, options: LLMOptions
    ) -> BaseModelT: ...
    def supports(self, capability: Capability) -> bool: ...
```

- `LLMOptions`: model, temperature, max tokens, timeout, tool definitions, seed.
- `LLMResponse`: text, tool calls, usage, model, provider, latency.
- `Capability`: `tools`, `vision`, `json_schema`, `streaming`. Callers check capability
  instead of branching on provider names.

Implementations: `OpenAIProvider` now; `AnthropicProvider`, `GeminiProvider`,
`AzureOpenAIProvider`, `OllamaProvider` later. Plus two that exist from day one:

- `NullProvider` — returns a typed "explanation unavailable" result when no API key is
  configured, so local development and CI never require a key.
- `FakeProvider` — returns fixtures in tests, making AI-dependent tests deterministic.

Selection is config-driven (`LLM_PROVIDER`, `LLM_MODEL`) through a registry. Nothing
outside `app/ai/providers/` imports an SDK.

**Retries and failure.** Timeouts, one retry with jitter on transient errors, then a
typed `AIUnavailable` error. Callers degrade gracefully; an AI failure never fails a
financial request.

## 3. Structured output

Analytical responses are Pydantic-validated:

```python
class AnalysisResponse(BaseModel):
    summary: str
    findings: list[FindingExplanation]
    risks: list[str]
    opportunities: list[str]
    recommendations: list[Recommendation]
    estimated_monthly_savings: Decimal
    confidence: float
```

Validation rules that matter:

- `estimated_monthly_savings` and every monetary field in the response must **equal a
  value present in the input findings**. A validator rejects numbers the model invented.
  On rejection: one repair attempt with the validation error, then fall back to rendering
  the finding without prose.
- Every `FindingExplanation` carries the `finding_id` it explains. An explanation without
  a matching finding is dropped.

This is the concrete mechanism behind the spec's "never present assumptions as facts".

## 4. The assistant: controlled tools only

The assistant is a single tool-calling loop (plain LangChain tool calling; no graph until
a real branching need appears). The model has **no database access**. It can only call
registered tools, each of which is a thin wrapper over an application service with the
authenticated `user_id` injected server-side — the model cannot pass a user id.

Initial tool set:

| Tool | Returns |
| --- | --- |
| `get_monthly_income(period)` | total income for a month |
| `get_monthly_expenses(period)` | total expenses for a month |
| `get_expenses_by_category(period, depth)` | category totals and shares |
| `compare_periods(period_a, period_b)` | deltas by category |
| `get_recurring_expenses()` | detected recurring series |
| `get_upcoming_bills(days)` | pending items by due date |
| `calculate_savings_rate(period)` | income, expenses, rate |
| `detect_spending_anomalies(period)` | rule-engine findings |
| `get_cashflow_projection(days)` | phase 2 |
| `get_debt_summary()` / `simulate_debt_strategy(...)` | phase 3 |
| `get_financial_goals()` | phase 4 |

Tool contract:

- Arguments are Pydantic models; anything unparseable is rejected before execution.
- Returns are Pydantic models serialized with money as strings.
- Read-only. No tool writes. Actions (create budget, create goal, dismiss recommendation)
  are UI affordances the user clicks, never model side effects.
- Loop limits: max 6 tool calls and a wall-clock budget per question; exceeding either
  ends the turn with a partial answer rather than looping.

**Grounding.** The final answer is generated from tool outputs that are also returned to
the client, so the UI can show "based on: October expenses by category" next to the
answer. An answer with no tool call is labelled as general information, not personal
advice.

## 5. Where AI is used, precisely

| Use | Type | Fallback |
| --- | --- | --- |
| Explain rule-engine findings | structured output | show the finding's template text |
| Categorize transactions the rules did not match | structured output, batched | leave uncategorized |
| Extract fields from documents when parsers are insufficient | structured output (vision for images) | manual entry |
| Answer questions about finances | tool calling | none; feature unavailable |
| Summarize an analysis run | structured output | show metrics only |

Not used for: any arithmetic, choosing a debt strategy, deciding severity, computing
savings estimates, or writing to the database.

## 6. Prompts

Prompt templates live in `app/ai/prompts/` as versioned files (`explain_findings.v1.md`),
referenced by id, and the id is logged with each call. Changing a prompt means a new
version, which makes regressions attributable.

System prompts state the invariants explicitly: use only the provided numbers, never
compute new ones, say "I don't have that data" when a tool returned nothing, never give
regulated investment advice, and answer in the user's locale.

## 7. Cost, privacy and observability

- Per-user daily token budget; when exceeded, deterministic features continue and AI
  features return a clear message.
- Logged per call: provider, model, purpose, prompt id, tokens, latency, correlation id.
  Never logged: prompt text, response text, document content, merchant-level data.
- Documents are sent to the LLM only when the user uploaded them for extraction and only
  for the fields needed. A setting can disable LLM-based extraction entirely.
- No training on user data: the provider client sets the relevant opt-out flags.

## 8. Testing

- Contract tests run every provider implementation against the same suite using recorded
  responses.
- `FakeProvider` fixtures make explanation and assistant tests deterministic.
- Structured-output validation is tested with hostile fixtures: invented numbers, missing
  finding ids, wrong types, prose instead of JSON.
- A test asserts that no module outside `app/ai/` imports an LLM SDK, and that no AI tool
  imports a repository.
