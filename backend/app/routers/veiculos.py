from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from sqlalchemy.orm import aliased

from ..auth import UsuarioDep
from ..database import SessionDep, obter, salvar
from ..models import Cliente, Cobranca, Permanencia, Usuario, Vaga, Veiculo
from ..regras_estacionamento import auditar, criacao
from ..schemas import (
    MovimentacaoVeiculoSaida,
    VeiculoCriar,
    VeiculoEditar,
    VeiculoSaida,
    normalizar_placa,
)

router = APIRouter(prefix='/veiculos', tags=['Veículos'])


@router.post('', response_model=VeiculoSaida, status_code=201)
def criar(dados: VeiculoCriar, session: SessionDep, usuario: UsuarioDep):
    obter(session, Cliente, dados.cliente_id)
    obj = Veiculo(**dados.model_dump(), **criacao(usuario.id))
    session.add(obj)
    salvar(session)
    return VeiculoSaida.model_validate(obj)


@router.get('', response_model=list[VeiculoSaida])
def listar(
    session: SessionDep,
    usuario: UsuarioDep,
    cliente_id: int | None = None,
    offset: int = Query(0, ge=0),
    limite: int = Query(50, ge=1, le=100),
):
    stmt = select(Veiculo)
    if cliente_id is not None:
        stmt = stmt.where(Veiculo.cliente_id == cliente_id)
    return [
        VeiculoSaida.model_validate(v)
        for v in session.exec(
            stmt.order_by(Veiculo.id).offset(offset).limit(limite)
        ).all()
    ]


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


@router.get('/{veiculo_id}/historico', response_model=list[MovimentacaoVeiculoSaida])
def historico(
    veiculo_id: int,
    session: SessionDep,
    usuario: UsuarioDep,
    offset: int = Query(0, ge=0),
    limite: int = Query(20, ge=1, le=100),
):
    """Consulta sem gravações; o cliente é o responsável registrado na entrada."""
    obter(session, Veiculo, veiculo_id)
    entrada_por = aliased(Usuario)
    saida_por = aliased(Usuario)
    consulta = (
        select(
            Permanencia,
            Cliente.nome,
            Vaga.numero,
            entrada_por.nome,
            saida_por.nome,
            Cobranca,
        )
        .select_from(Permanencia)
        .join(Cliente, Cliente.id == Permanencia.cliente_id)
        .join(Vaga, Vaga.id == Permanencia.vaga_id)
        .join(entrada_por, entrada_por.id == Permanencia.usuario_entrada_id)
        .outerjoin(saida_por, saida_por.id == Permanencia.usuario_saida_id)
        .outerjoin(Cobranca, Cobranca.permanencia_id == Permanencia.id)
        .where(Permanencia.veiculo_id == veiculo_id)
        .order_by(Permanencia.entrada.desc(), Permanencia.id.desc())
        .offset(offset)
        .limit(limite)
    )
    return [
        MovimentacaoVeiculoSaida(
            permanencia_id=p.id,
            entrada=p.entrada,
            saida=p.saida,
            cliente_id=p.cliente_id,
            cliente_nome=cliente,
            vaga_numero=vaga,
            operador_entrada=operador_entrada,
            operador_saida=operador_saida,
            valor_hora_aplicado=p.valor_hora_aplicado,
            valor_cobrado=cobranca.valor if cobranca else None,
            pago_em=cobranca.pago_em if cobranca else None,
            forma_pagamento=cobranca.forma_pagamento if cobranca else None,
        )
        for p, cliente, vaga, operador_entrada, operador_saida, cobranca in session.exec(
            consulta
        ).all()
    ]


@router.patch('/{veiculo_id}', response_model=VeiculoSaida)
def editar(
    veiculo_id: int, dados: VeiculoEditar, session: SessionDep, usuario: UsuarioDep
):
    # Entrada também bloqueia veículo antes do cliente; edição segue essa ordem.
    obj = obter(session, Veiculo, veiculo_id, True)
    if dados.cliente_id is not None:
        obter(session, Cliente, dados.cliente_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(obj, campo, valor)
    auditar(obj, usuario.id)
    salvar(session)
    return VeiculoSaida.model_validate(obj)
