import pytest
from app.rules.models import FindingSeverity


@pytest.fixture
def account(client, auth_headers) -> dict:
    return client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={"name": "Rule Account", "type": "checking", "opening_balance": "0.00"},
    ).json()


def test_rule_engine_high_expense_growth(client, auth_headers, account):
    # Add a massive expense to trigger HighExpenseGrowthRule
    payload = {
        "account_id": account["id"],
        "transaction_type": "expense",
        "description": "Massive Expense",
        "amount": "6000.00",
        "transaction_date": "2026-09-05",
    }
    client.post("/api/v1/transactions", headers=auth_headers, json=payload)

    # Run analysis
    res = client.post("/api/v1/analysis/run?period=2026-09", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["findings_count"] > 0

    # Fetch findings
    res = client.get("/api/v1/findings", headers=auth_headers)
    assert res.status_code == 200
    findings = res.json()
    assert len(findings) > 0

    # Find the specific rule
    expense_finding = next((f for f in findings if f["rule_id"] == "high_expense_growth"), None)
    assert expense_finding is not None
    assert expense_finding["severity"] == FindingSeverity.medium.value
    assert float(expense_finding["estimated_monthly_impact"]) == 1000.00

def test_rule_engine_idempotent_re_runs(client, auth_headers, account):
    # This test assumes the previous test added data.
    # We trigger the low balance rule
    res1 = client.post("/api/v1/analysis/run?period=2026-09", headers=auth_headers)
    assert res1.status_code == 200

    # Second run should succeed and update
    res2 = client.post("/api/v1/analysis/run?period=2026-09", headers=auth_headers)
    assert res2.status_code == 200

    res_list = client.get("/api/v1/findings", headers=auth_headers)
    findings = res_list.json()

    # Deduplication check: We should not have duplicated findings for the same period
    rule_ids = [f["rule_id"] for f in findings]
    assert len(rule_ids) == len(set(rule_ids)), "Findings were duplicated instead of updated."
