import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5433/produtos_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from main import Base, Produto, app, get_db  # noqa: E402


test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
  
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(client: TestClient) -> Generator[Session, None, None]:
    """Sessão auxiliar para confirmar dados diretamente no PostgreSQL de teste."""
    del client  # A dependência garante que as tabelas já foram criadas.
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def produto_existente(client: TestClient) -> dict:
    resposta = client.post(
        "/produtos",
        json={
            "nome": "Teclado mecânico",
            "preco": 249.90,
            "estoque": 12,
            "ativo": True,
        },
    )
    assert resposta.status_code == 201
    return resposta.json()
