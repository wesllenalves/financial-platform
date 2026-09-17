import pytest


@pytest.fixture
def account(client, auth_headers) -> dict:
    return client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={"name": "Conta", "type": "checking", "opening_balance": "500.00"},
    ).json()


def add(client, headers, account_id, kind, amount, day, month=9, category_id=None, merchant=None):
    payload = {
        "account_id": account_id,
        "transaction_type": kind,
        "description": f"{kind} {day}/{month}",
        "amount": amount,
        "transaction_date": f"2026-{month:02d}-{day:02d}",
    }
    if category_id:
        payload["category_id"] = category_id
    if merchant:
        payload["merchant"] = merchant
    response = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_summary_matches_hand_computed_values(client, auth_headers, account) -> None:
    add(client, auth_headers, account["id"], "income", "5000.00", 5)
    add(client, auth_headers, account["id"], "expense", "1200.00", 6)
    add(client, auth_headers, account["id"], "expense", "800.50", 7)

    summary = client.get("/api/v1/analysis/summary?period=2026-09", headers=auth_headers).json()

    assert summary["income"] == "5000.00"
    assert summary["expenses"] == "2000.50"
    assert summary["net_cash_flow"] == "2999.50"
    assert summary["savings_rate"] == "0.5999"


def test_dashboard_reports_balance_categories_and_trend(client, auth_headers, account) -> None:
    categories = client.get("/api/v1/categories", headers=auth_headers).json()
    market = next(c["id"] for c in categories if c["name"] == "Mercado")

    add(client, auth_headers, account["id"], "income", "4000.00", 5, month=8)
    add(client, auth_headers, account["id"], "expense", "1000.00", 6, month=8, category_id=market)
    add(client, auth_headers, account["id"], "expense", "600.00", 6, month=9, category_id=market)

    dashboard = client.get("/api/v1/analysis/dashboard?period=2026-09", headers=auth_headers).json()

    assert dashboard["current_balance"] == "2900.00"
    assert dashboard["summary"]["expenses"] == "600.00"
    assert dashboard["previous_summary"]["income"] == "4000.00"
    assert dashboard["by_category"][0]["category_name"] == "Mercado"
    assert dashboard["by_category"][0]["share"] == "1.0000"
    assert [point["period"] for point in dashboard["trend"]][-1] == "2026-09"


def test_recurring_detection_surfaces_a_subscription(client, auth_headers, account) -> None:
    for month in (6, 7, 8, 9):
        add(
            client,
            auth_headers,
            account["id"],
            "expense",
            "55.90",
            10,
            month=month,
            merchant="NETFLIX *1234",
        )

    series = client.get("/api/v1/analysis/recurring", headers=auth_headers).json()

    assert len(series) == 1
    assert series[0]["occurrences"] == 4
    assert series[0]["mean_amount"] == "55.90"


def test_analysis_never_includes_another_users_data(client, auth_headers, account) -> None:
    import uuid

    from tests.conftest import register_and_login

    add(client, auth_headers, account["id"], "income", "9000.00", 5)
    intruder = register_and_login(client, f"other-{uuid.uuid4().hex[:6]}@example.com")

    summary = client.get("/api/v1/analysis/summary?period=2026-09", headers=intruder).json()

    assert summary["income"] == "0.00"


def test_an_invalid_period_is_rejected(client, auth_headers) -> None:
    response = client.get("/api/v1/analysis/summary?period=2026-13", headers=auth_headers)
    assert response.status_code == 422
