import uuid
from decimal import Decimal

import pytest

from tests.conftest import register_and_login


@pytest.fixture
def account(client, auth_headers) -> dict:
    response = client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={"name": "Conta Corrente", "type": "checking", "opening_balance": "1000.00"},
    )
    assert response.status_code == 201
    return response.json()


def expense_category(client, headers) -> str:
    categories = client.get("/api/v1/categories", headers=headers).json()
    return next(category["id"] for category in categories if category["name"] == "Mercado")


def test_create_and_list_a_transaction(client, auth_headers, account) -> None:
    created = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Compra do mês",
            "amount": "345.67",
            "transaction_date": "2026-09-05",
            "category_id": expense_category(client, auth_headers),
            "merchant": "Supermercado Bom Preço LTDA",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["amount"] == "345.67"

    listing = client.get("/api/v1/transactions", headers=auth_headers).json()
    assert listing["total"] == 1
    assert listing["items"][0]["description"] == "Compra do mês"


def test_amount_keeps_its_cents_through_the_database(client, auth_headers, account) -> None:
    created = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Boleto",
            "amount": "1234.56",
            "transaction_date": "2026-09-05",
        },
    ).json()

    fetched = client.get(f"/api/v1/transactions/{created['id']}", headers=auth_headers).json()

    assert Decimal(fetched["amount"]) == Decimal("1234.56")


def test_a_negative_amount_is_rejected(client, auth_headers, account) -> None:
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Inválido",
            "amount": "-10.00",
            "transaction_date": "2026-09-05",
        },
    )
    assert response.status_code == 422


def test_a_category_of_the_wrong_kind_is_rejected(client, auth_headers, account) -> None:
    categories = client.get("/api/v1/categories", headers=auth_headers).json()
    income_category = next(c["id"] for c in categories if c["name"] == "Salário")

    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Errado",
            "amount": "10.00",
            "transaction_date": "2026-09-05",
            "category_id": income_category,
        },
    )

    assert response.status_code == 422


def test_update_and_soft_delete(client, auth_headers, account) -> None:
    created = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Almoço",
            "amount": "40.00",
            "transaction_date": "2026-09-05",
        },
    ).json()

    updated = client.patch(
        f"/api/v1/transactions/{created['id']}",
        headers=auth_headers,
        json={"amount": "45.50", "description": "Almoço com cliente"},
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "45.50"

    assert (
        client.delete(f"/api/v1/transactions/{created['id']}", headers=auth_headers).status_code
        == 204
    )
    assert (
        client.get(f"/api/v1/transactions/{created['id']}", headers=auth_headers).status_code == 404
    )
    assert client.get("/api/v1/transactions", headers=auth_headers).json()["total"] == 0


def test_transfers_move_money_without_touching_income_or_expenses(
    client, auth_headers, account
) -> None:
    savings = client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={"name": "Poupança", "type": "savings", "opening_balance": "0.00"},
    ).json()

    response = client.post(
        "/api/v1/transactions/transfers",
        headers=auth_headers,
        json={
            "from_account_id": account["id"],
            "to_account_id": savings["id"],
            "amount": "250.00",
            "transaction_date": "2026-09-10",
        },
    )
    assert response.status_code == 201
    assert len(response.json()) == 2

    summary = client.get("/api/v1/analysis/summary?period=2026-09", headers=auth_headers).json()
    assert summary["income"] == "0.00"
    assert summary["expenses"] == "0.00"

    balances = {
        item["name"]: item["current_balance"]
        for item in client.get("/api/v1/accounts", headers=auth_headers).json()
    }
    assert balances["Conta Corrente"] == "750.00"
    assert balances["Poupança"] == "250.00"


def test_a_transfer_needs_two_different_accounts(client, auth_headers, account) -> None:
    response = client.post(
        "/api/v1/transactions/transfers",
        headers=auth_headers,
        json={
            "from_account_id": account["id"],
            "to_account_id": account["id"],
            "amount": "10.00",
            "transaction_date": "2026-09-10",
        },
    )
    assert response.status_code == 422


def test_filters_narrow_the_listing(client, auth_headers, account) -> None:
    for day, amount in ((3, "10.00"), (20, "20.00")):
        client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json={
                "account_id": account["id"],
                "transaction_type": "expense",
                "description": f"Gasto {day}",
                "amount": amount,
                "transaction_date": f"2026-09-{day:02d}",
            },
        )

    filtered = client.get(
        "/api/v1/transactions?date_from=2026-09-10&date_to=2026-09-30", headers=auth_headers
    ).json()

    assert filtered["total"] == 1
    assert filtered["items"][0]["description"] == "Gasto 20"


def test_a_user_cannot_read_or_change_another_users_transaction(
    client, auth_headers, account
) -> None:
    mine = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Privado",
            "amount": "99.00",
            "transaction_date": "2026-09-05",
        },
    ).json()

    intruder = register_and_login(client, f"intruder-{uuid.uuid4().hex[:6]}@example.com")

    assert client.get(f"/api/v1/transactions/{mine['id']}", headers=intruder).status_code == 404
    assert (
        client.patch(
            f"/api/v1/transactions/{mine['id']}", headers=intruder, json={"amount": "1.00"}
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/transactions/{mine['id']}", headers=intruder).status_code == 404
    assert client.get("/api/v1/transactions", headers=intruder).json()["total"] == 0


def test_a_user_cannot_post_into_another_users_account(client, auth_headers, account) -> None:
    intruder = register_and_login(client, f"intruder-{uuid.uuid4().hex[:6]}@example.com")

    response = client.post(
        "/api/v1/transactions",
        headers=intruder,
        json={
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Invasão",
            "amount": "10.00",
            "transaction_date": "2026-09-05",
        },
    )

    assert response.status_code == 404
