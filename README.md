# API de Produtos com FastAPI, PostgreSQL, Docker e Pytest

Projeto desenvolvido para a atividade avaliativa da disciplina **Desenvolvimento de APIs com FastAPI**. A aplicação gerencia produtos de um pequeno e-commerce e utiliza PostgreSQL real tanto no desenvolvimento quanto nos testes.

## Tecnologias

- FastAPI
- SQLAlchemy ORM
- Pydantic
- PostgreSQL
- Docker e Docker Compose
- Pytest e TestClient

## Estrutura

```text
seu_repositorio/
├── main.py
├── conftest.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── README.md
└── tests/
    ├── __init__.py
    └── test_produtos.py
```

## Modelo de produto

| Campo | Tipo | Regra |
|---|---|---|
| `id` | Integer | Chave primária gerada pelo banco |
| `nome` | String | Obrigatório e não pode ser vazio |
| `preco` | Float | Obrigatório e maior que zero |
| `estoque` | Integer | Padrão `0` e não negativo |
| `ativo` | Boolean | Padrão `true` |

## Endpoints

| Método | Rota | Resposta esperada |
|---|---|---|
| GET | `/produtos` | `200` com a lista de produtos |
| POST | `/produtos` | `201` com o produto criado |
| GET | `/produtos/{id}` | `200` ou `404` |
| DELETE | `/produtos/{id}` | `204` ou `404` |

## 1. Preparar o ambiente

Crie e ative um ambiente virtual.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Subir somente o banco de testes

O serviço `db_test` usa a porta `5433` do computador e não possui volume persistente.

```bash
docker compose up -d db_test
```

Confirme que o container está saudável:

```bash
docker compose ps
```

## 3. Executar os testes

Comando exato recomendado para a entrega:

```bash
pytest --cov=main --cov-report=term-missing -v
```

Também é possível usar o comando final proposto na atividade:

```bash
docker compose up -d db_test && pytest --cov=main -v
```

No PowerShell, execute os comandos separadamente ou use:

```powershell
docker compose up -d db_test; pytest --cov=main -v
```

## Saída esperada do Pytest

A função parametrizada gera sete casos de validação. Por isso, as 12 funções de teste aparecem como **18 testes executados**.

```text
============================= test session starts =============================
collected 18 items

tests/test_produtos.py ..................                               [100%]

============================== 18 passed in ... ==============================
```

A porcentagem exata de cobertura pode variar ligeiramente conforme a versão das bibliotecas, mas o objetivo é permanecer acima de 85%.

## Como funciona o isolamento entre testes

A fixture `client`, localizada em `conftest.py`, é executada novamente para cada função de teste. Antes do teste, ela remove eventuais tabelas antigas e cria as tabelas no PostgreSQL exclusivo da porta `5433` usando `Base.metadata.create_all`.

A dependência original `get_db` é substituída por `app.dependency_overrides`, fazendo a API utilizar `TestingSessionLocal`. Após o `yield`, o override é limpo e as tabelas são destruídas com `Base.metadata.drop_all`. Dessa forma, um teste nunca depende de dados criados por outro e a ordem de execução não altera o resultado.

## Executar a aplicação completa

Para subir a API e o banco de desenvolvimento:

```bash
docker compose up --build -d db api
```

A documentação interativa ficará disponível em:

```text
http://localhost:8000/docs
```

Para encerrar os containers:

```bash
docker compose down
```

Para também apagar o volume do banco de desenvolvimento:

```bash
docker compose down -v
```

## Exemplos de requisições

Criar um produto:

```bash
curl -X POST "http://localhost:8000/produtos" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Notebook","preco":3500.00,"estoque":5,"ativo":true}'
```

Listar produtos:

```bash
curl "http://localhost:8000/produtos"
```

## Histórico Git obrigatório

A entrega deve ser feita por link de um repositório com histórico de commits. Uma sequência possível é:

```bash
git init
git add main.py requirements.txt Dockerfile docker-compose.yml
git commit -m "feat: implementa API e infraestrutura PostgreSQL"

git add conftest.py pytest.ini tests
git commit -m "test: adiciona testes isolados com Pytest"

git add README.md
git commit -m "docs: adiciona instruções de execução"
```

Depois, crie o repositório no GitHub e siga os comandos apresentados pela própria plataforma para adicionar o remoto e enviar a branch.
