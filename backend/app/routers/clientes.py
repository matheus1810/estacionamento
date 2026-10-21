from fastapi import APIRouter, Query
from sqlmodel import select

from ..auth import UsuarioDep
from ..database import SessionDep, obter, salvar
from ..models import Cliente
from ..regras_estacionamento import auditar, criacao
from ..schemas import ClienteCriar, ClienteEditar, ClienteSaida

router = APIRouter(prefix='/clientes', tags=['Clientes'])


@router.post('', response_model=ClienteSaida, status_code=201)
def criar(dados: ClienteCriar, session: SessionDep, usuario: UsuarioDep):
    obj = Cliente(**dados.model_dump(), **criacao(usuario.id))
    session.add(obj)
    salvar(session)
    return ClienteSaida.model_validate(obj)


@router.get('', response_model=list[ClienteSaida])
def listar(session: SessionDep, usuario: UsuarioDep, nome: str | None = None,
           ativo: bool | None = None, offset: int = Query(0, ge=0),
           limite: int = Query(50, ge=1, le=100)):
    stmt = select(Cliente)
    if nome:
        stmt = stmt.where(Cliente.nome.contains(nome, autoescape=True))
    if ativo is not None:
        stmt = stmt.where(Cliente.ativo == ativo)
    return [ClienteSaida.model_validate(c) for c in session.exec(
        stmt.order_by(Cliente.id).offset(offset).limit(limite)).all()]


@router.get('/{cliente_id}', response_model=ClienteSaida)
def buscar(cliente_id: int, session: SessionDep, usuario: UsuarioDep):
    return ClienteSaida.model_validate(obter(session, Cliente, cliente_id))


@router.patch('/{cliente_id}', response_model=ClienteSaida)
def editar(cliente_id: int, dados: ClienteEditar, session: SessionDep, usuario: UsuarioDep):
    obj = obter(session, Cliente, cliente_id, True)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(obj, campo, valor)
    auditar(obj, usuario.id)
    salvar(session)
    return ClienteSaida.model_validate(obj)
