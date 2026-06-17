import os
from contextlib import asynccontextmanager
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Boolean, Float, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/produtos_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Classe-base dos modelos SQLAlchemy."""


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    preco: Mapped[float] = mapped_column(Float, nullable=False)
    estoque: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProdutoEntrada(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    preco: float = Field(..., gt=0)
    estoque: int = Field(default=0, ge=0)
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        nome_limpo = valor.strip()
        if not nome_limpo:
            raise ValueError("O nome do produto não pode ser vazio.")
        return nome_limpo


class ProdutoSaida(ProdutoEntrada):
    id: int

    model_config = ConfigDict(from_attributes=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Produtos",
    description="API REST para gerenciamento de produtos de um pequeno e-commerce.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/produtos", response_model=list[ProdutoSaida], status_code=status.HTTP_200_OK)
def listar_produtos(db: Session = Depends(get_db)) -> list[Produto]:
    return list(db.scalars(select(Produto).order_by(Produto.id)).all())


@app.post("/produtos", response_model=ProdutoSaida, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoEntrada, db: Session = Depends(get_db)) -> Produto:
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@app.get(
    "/produtos/{produto_id}",
    response_model=ProdutoSaida,
    status_code=status.HTTP_200_OK,
)
def buscar_produto(produto_id: int, db: Session = Depends(get_db)) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )
    return produto


@app.delete("/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(produto_id: int, db: Session = Depends(get_db)) -> Response:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    db.delete(produto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
