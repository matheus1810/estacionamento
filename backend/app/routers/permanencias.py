from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ..auth import UsuarioDep
from ..config import agora_local
from ..database import SessionDep, obter, salvar
from ..models import Cliente, Cobranca, Permanencia, Vaga, Veiculo
from ..regras_estacionamento import (
    auditar, calcular_horista, criacao, disponibilidade, tarifa_atual,
)
from ..schemas import (
    CobrancaSaida, PagamentoEntrada, PermanenciaCadastroCriar, PermanenciaCriar,
    PermanenciaSaida, PreviaSaida,
)

router = APIRouter(prefix='/permanencias', tags=['Permanências'])


def registrar_entrada(session, usuario, vaga, veiculo, cliente):
    """Regra comum às entradas. O chamador mantém os bloqueios e faz o commit."""
    agora = agora_local()
    if not cliente.ativo:
        raise HTTPException(409, 'Cliente inativo.')
    livre, motivo = disponibilidade(session, vaga, agora.date())
    if not livre:
        raise HTTPException(409, motivo)
    if session.exec(select(Permanencia.id).where(
        Permanencia.veiculo_id == veiculo.id, Permanencia.saida.is_(None))).first():
        raise HTTPException(409, 'Veículo já tem permanência aberta.')
    obj = Permanencia(cliente_id=cliente.id, veiculo_id=veiculo.id, vaga_id=vaga.id,
                      entrada=agora, valor_hora_aplicado=tarifa_atual(session).valor_hora,
                      usuario_entrada_id=usuario.id, **criacao(usuario.id))
    session.add(obj)
    return obj


@router.post('', response_model=PermanenciaSaida, status_code=201)
def entrada(dados: PermanenciaCriar, session: SessionDep, usuario: UsuarioDep):
    vaga = obter(session, Vaga, dados.vaga_id, True)
    veiculo = obter(session, Veiculo, dados.veiculo_id, True)
    cliente = obter(session, Cliente, veiculo.cliente_id, True)
    obj = registrar_entrada(session, usuario, vaga, veiculo, cliente)
    salvar(session)
    return PermanenciaSaida.model_validate(obj)


@router.post('/cadastro-entrada', response_model=PermanenciaSaida, status_code=201)
def cadastro_entrada(dados: PermanenciaCadastroCriar, session: SessionDep, usuario: UsuarioDep):
    # A vaga é sempre o primeiro bloqueio. Os novos registros ficam protegidos
    # pelos próprios INSERTs e só persistem junto com a entrada confirmada.
    vaga = obter(session, Vaga, dados.vaga_id, True)
    if dados.cliente_id is not None:
        cliente = obter(session, Cliente, dados.cliente_id, True)
    else:
        cliente = Cliente(**dados.cliente.model_dump(), **criacao(usuario.id))
        session.add(cliente)
        session.flush()
    veiculo = Veiculo(cliente_id=cliente.id, placa=dados.placa,
                      modelo=dados.modelo, cor=dados.cor, **criacao(usuario.id))
    session.add(veiculo)
    session.flush()
    obj = registrar_entrada(session, usuario, vaga, veiculo, cliente)
    salvar(session)
    return PermanenciaSaida.model_validate(obj)


@router.get('', response_model=list[PermanenciaSaida])
def listar(session: SessionDep, usuario: UsuarioDep, abertas: bool | None = None,
           veiculo_id: int | None = Query(None, gt=0),
           offset: int = Query(0, ge=0), limite: int = Query(50, ge=1, le=100)):
    stmt = select(Permanencia)
    if veiculo_id is not None:
        stmt = stmt.where(Permanencia.veiculo_id == veiculo_id)
    if abertas is not None:
        stmt = stmt.where(Permanencia.saida.is_(None) if abertas else Permanencia.saida.is_not(None))
    return [PermanenciaSaida.model_validate(p) for p in session.exec(
        stmt.order_by(Permanencia.id).offset(offset).limit(limite)).all()]


@router.get('/{permanencia_id}/previa', response_model=PreviaSaida)
def previa(permanencia_id: int, session: SessionDep, usuario: UsuarioDep):
    obj = obter(session, Permanencia, permanencia_id)
    if obj.saida is not None:
        raise HTTPException(409, 'Permanência já encerrada.')
    agora = agora_local()
    blocos, valor = calcular_horista(obj.entrada, agora, obj.valor_hora_aplicado)
    return PreviaSaida(permanencia_id=obj.id, calculado_em=agora, blocos=blocos, valor=valor)


@router.post('/{permanencia_id}/saida', response_model=CobrancaSaida)
def saida(permanencia_id: int, dados: PagamentoEntrada, session: SessionDep, usuario: UsuarioDep):
    ref = obter(session, Permanencia, permanencia_id)
    obter(session, Vaga, ref.vaga_id, True)
    obter(session, Veiculo, ref.veiculo_id, True)
    obj = obter(session, Permanencia, permanencia_id, True)
    if obj.saida is not None:
        raise HTTPException(409, 'Permanência já encerrada e paga.')
    if session.exec(select(Cobranca.id).where(Cobranca.permanencia_id == obj.id)).first():
        raise HTTPException(409, 'Permanência já possui cobrança.')
    agora = agora_local()
    _, valor = calcular_horista(obj.entrada, agora, obj.valor_hora_aplicado)
    obj.saida = agora
    obj.usuario_saida_id = usuario.id
    auditar(obj, usuario.id)
    cobranca = Cobranca(permanencia_id=obj.id, vencimento=agora.date(), valor=valor,
                         pago_em=agora, forma_pagamento=dados.forma_pagamento,
                         usuario_recebimento_id=usuario.id, **criacao(usuario.id))
    session.add(cobranca)
    salvar(session)
    return CobrancaSaida.model_validate(cobranca)
