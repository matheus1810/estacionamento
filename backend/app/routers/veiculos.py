from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ..auth import UsuarioDep
from ..database import SessionDep, obter, salvar
from ..models import Cliente, Veiculo
from ..regras_estacionamento import auditar, criacao
from ..schemas import VeiculoCriar, VeiculoEditar, VeiculoSaida, normalizar_placa

router = APIRouter(prefix='/veiculos', tags=['Veículos'])


@router.post('', response_model=VeiculoSaida, status_code=201)
def criar(dados: VeiculoCriar, session: SessionDep, usuario: UsuarioDep):
    obter(session, Cliente, dados.cliente_id)
    obj = Veiculo(**dados.model_dump(), **criacao(usuario.id))
    session.add(obj)
    salvar(session)
    return VeiculoSaida.model_validate(obj)


@router.get('', response_model=list[VeiculoSaida])
def listar(session: SessionDep, usuario: UsuarioDep, cliente_id: int | None = None,
           offset: int = Query(0, ge=0), limite: int = Query(50, ge=1, le=100)):
    stmt = select(Veiculo)
    if cliente_id is not None:
        stmt = stmt.where(Veiculo.cliente_id == cliente_id)
    return [VeiculoSaida.model_validate(v) for v in session.exec(
        stmt.order_by(Veiculo.id).offset(offset).limit(limite)).all()]


@router.get('/placa/{placa}', response_model=VeiculoSaida)
def buscar(placa: str, session: SessionDep, usuario: UsuarioDep):
    try:
        placa = normalizar_placa(placa)
    except ValueError:
        raise HTTPException(422, 'Placa brasileira inválida.') from None
    obj = session.exec(select(Veiculo).where(Veiculo.placa == placa)).first()
    if obj is None:
        raise HTTPException(404, 'Veículo não encontrado.')
    return VeiculoSaida.model_validate(obj)


@router.patch('/{veiculo_id}', response_model=VeiculoSaida)
def editar(veiculo_id: int, dados: VeiculoEditar, session: SessionDep, usuario: UsuarioDep):
    # Entrada também bloqueia veículo antes do cliente; edição segue essa ordem.
    obj = obter(session, Veiculo, veiculo_id, True)
    if dados.cliente_id is not None:
        obter(session, Cliente, dados.cliente_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(obj, campo, valor)
    auditar(obj, usuario.id)
    salvar(session)
    return VeiculoSaida.model_validate(obj)
