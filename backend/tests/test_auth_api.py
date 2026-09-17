import uuid


def test_register_then_login_and_fetch_me(client) -> None:
    email = f"{uuid.uuid4().hex[:8]}@example.com"

    created = client.post(
        "/api/v1/auth/register",
        json={"name": "Ana", "email": email, "password": "sup3rsecret"},
    )
    assert created.status_code == 201
    assert created.json()["email"] == email
    assert "password" not in created.text

    tokens = client.post("/api/v1/auth/login", json={"email": email, "password": "sup3rsecret"})
    assert tokens.status_code == 200

    headers = {"Authorization": f"Bearer {tokens.json()['access_token']}"}
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_register_rejects_a_duplicate_email(client) -> None:
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    payload = {"name": "Ana", "email": email, "password": "sup3rsecret"}

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    conflict = client.post("/api/v1/auth/register", json=payload)

    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "conflict"


def test_login_with_a_wrong_password_is_rejected(client) -> None:
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Ana", "email": email, "password": "sup3rsecret"},
    )

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-one"})

    assert response.status_code == 401


def test_login_for_an_unknown_email_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "sup3rsecret"}
    )
    assert response.status_code == 401


def test_protected_endpoints_require_a_token(client) -> None:
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.get("/api/v1/transactions").status_code == 401


def test_refresh_token_cannot_be_used_as_an_access_token(client) -> None:
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Ana", "email": email, "password": "sup3rsecret"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "sup3rsecret"}
    ).json()

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )

    assert response.status_code == 401


def test_register_seeds_the_default_category_tree(client) -> None:
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Ana", "email": email, "password": "sup3rsecret"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "sup3rsecret"}
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    categories = client.get("/api/v1/categories", headers=headers).json()

    names = {category["name"] for category in categories}
    assert {"Moradia", "Alimentação", "Salário"} <= names
    assert all(category["system"] for category in categories)
