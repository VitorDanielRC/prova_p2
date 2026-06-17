import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from main import Produto


PRODUTO_VALIDO = {
    "nome": "Mouse sem fio",
    "preco": 129.90,
}


def test_listar_produtos_quando_banco_esta_vazio(client: TestClient) -> None:
    resposta = client.get("/produtos")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_criar_produto_retorna_201_e_id(client: TestClient) -> None:
    resposta = client.post("/produtos", json=PRODUTO_VALIDO)
    dados = resposta.json()

    assert resposta.status_code == 201
    assert isinstance(dados["id"], int)
    assert dados["nome"] == "Mouse sem fio"
    assert dados["preco"] == 129.90
    assert dados["estoque"] == 0
    assert dados["ativo"] is True


def test_criar_produto_persiste_no_banco(
    client: TestClient,
    db_session: Session,
) -> None:
    resposta = client.post("/produtos", json=PRODUTO_VALIDO)
    produto_id = resposta.json()["id"]

    produto_salvo = db_session.scalar(
        select(Produto).where(Produto.id == produto_id)
    )

    assert resposta.status_code == 201
    assert produto_salvo is not None
    assert produto_salvo.nome == "Mouse sem fio"
    assert produto_salvo.preco == 129.90


def test_criar_produto_aparece_na_listagem(client: TestClient) -> None:
    criacao = client.post("/produtos", json=PRODUTO_VALIDO)
    produto_criado = criacao.json()

    listagem = client.get("/produtos")

    assert criacao.status_code == 201
    assert listagem.status_code == 200
    assert listagem.json() == [produto_criado]


def test_buscar_produto_por_id_com_sucesso(
    client: TestClient,
    produto_existente: dict,
) -> None:
    resposta = client.get(f"/produtos/{produto_existente['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == produto_existente


def test_buscar_produto_com_id_inexistente_retorna_404(
    client: TestClient,
) -> None:
    resposta = client.get("/produtos/999999")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Produto não encontrado."}


def test_deletar_produto_retorna_204(
    client: TestClient,
    produto_existente: dict,
) -> None:
    resposta = client.delete(f"/produtos/{produto_existente['id']}")

    assert resposta.status_code == 204
    assert resposta.content == b""


def test_deletar_produto_e_confirmar_remocao_com_get(
    client: TestClient,
    produto_existente: dict,
) -> None:
    produto_id = produto_existente["id"]

    exclusao = client.delete(f"/produtos/{produto_id}")
    consulta = client.get(f"/produtos/{produto_id}")

    assert exclusao.status_code == 204
    assert consulta.status_code == 404
    assert consulta.json() == {"detail": "Produto não encontrado."}


def test_deletar_produto_inexistente_retorna_404(client: TestClient) -> None:
    resposta = client.delete("/produtos/999999")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Produto não encontrado."}


@pytest.mark.parametrize(
    "payload_invalido",
    [
        {"preco": 10.0},
        {"nome": "Produto sem preço"},
        {"nome": "", "preco": 10.0},
        {"nome": "   ", "preco": 10.0},
        {"nome": "Preço zero", "preco": 0},
        {"nome": "Preço negativo", "preco": -5.0},
        {"nome": "Estoque negativo", "preco": 10.0, "estoque": -1},
    ],
)
def test_payloads_invalidos_retornam_422(
    client: TestClient,
    payload_invalido: dict,
) -> None:
    resposta = client.post("/produtos", json=payload_invalido)

    assert resposta.status_code == 422
    assert "detail" in resposta.json()


def test_criar_produto_com_todos_os_campos(client: TestClient) -> None:
    payload = {
        "nome": "Monitor 27 polegadas",
        "preco": 1499.99,
        "estoque": 7,
        "ativo": False,
    }

    resposta = client.post("/produtos", json=payload)
    dados = resposta.json()

    assert resposta.status_code == 201
    assert dados["nome"] == payload["nome"]
    assert dados["preco"] == payload["preco"]
    assert dados["estoque"] == payload["estoque"]
    assert dados["ativo"] is False


def test_banco_inicia_vazio_em_cada_teste(client: TestClient) -> None:
    """Comprova que dados de outros testes não permanecem disponíveis."""
    resposta = client.get("/produtos")

    assert resposta.status_code == 200
    assert resposta.json() == []
