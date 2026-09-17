import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")

ADMIN_URL = os.environ.get(
    "TEST_ADMIN_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)


@pytest.fixture(scope="session")
def database_url() -> str:
    """Create a throwaway database for the test session."""
    name = f"finplat_test_{uuid.uuid4().hex[:8]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = ADMIN_URL.rsplit("/", 1)[0] + f"/{name}"
    os.environ["DATABASE_URL"] = url
    yield url
    with admin.connect() as connection:
        connection.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{name}' AND pid <> pg_backend_pid()"
            )
        )
        connection.execute(text(f'DROP DATABASE "{name}"'))


@pytest.fixture(scope="session")
def app_module(database_url):
    from app.core.config import get_settings

    get_settings.cache_clear()

    import app.core.db as db_module

    engine = create_engine(database_url, future=True)
    db_module.engine = engine
    db_module.SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    import app.models  # noqa: F401
    from app.core.db import Base

    Base.metadata.create_all(engine)

    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app_module):
    with TestClient(app_module) as test_client:
        yield test_client


@pytest.fixture
def db_session(database_url):
    from app.core.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def register_and_login(
    client, email: str = "user@example.com", password: str = "sup3rsecret"
) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": password},
    )
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client) -> dict:
    return register_and_login(client, f"user-{uuid.uuid4().hex[:8]}@example.com")
