from fastapi import APIRouter, HTTPException, Query
from sqlmodel import or_, select

from ..auth import UsuarioDep
from ..config import agora_local
from ..database import SessionDep, obter, salvar
from ..models import Cliente, Cobranca, Contratacao, Vaga
from ..regras_estacionamento import (
    auditar, criacao, fim_cancelamento, gerar_mensalidades, ocupada, reservas, tarifa_atual,
)
from ..schemas import ContratacaoCriar, ContratacaoSaida

router = APIRouter(prefix='/contratacoes', tags=['Contratações'])


@router.post('', response_model=ContratacaoSaida, status_code=201)
def criar(dados: ContratacaoCriar, session: SessionDep, usuario: UsuarioDep):
    # Ordem: vaga -> [veículo em entradas] -> cliente -> contratos -> cobranças.
    vaga = obter(session, Vaga, dados.vaga_id, True)
    cliente = obter(session, Cliente, dados.cliente_id, True)
    hoje = agora_local().date()
    if not vaga.ativa or not cliente.ativo:
        raise HTTPException(409, 'Cliente e vaga precisam estar ativos.')
    if reservas(session, vaga.id, dados.data_inicio, dados.data_fim):
        raise HTTPException(409, 'Já existe reserva sobreposta para esta vaga.')
    if dados.data_inicio <= hoje and (dados.data_fim is None or dados.data_fim >= hoje) and ocupada(session, vaga.id):
        raise HTTPException(409, 'Vaga ocupada por horista.')
    tarifa_atual(session)
    obj = Contratacao(**dados.model_dump(), dia_vencimento=dados.data_inicio.day,
                      **criacao(usuario.id))
    session.add(obj)
    session.flush()
    gerar_mensalidades(session, usuario.id, hoje, cliente.id)
    salvar(session)
    return ContratacaoSaida.model_validate(obj)


@router.get('', response_model=list[ContratacaoSaida])
def listar(session: SessionDep, usuario: UsuarioDep, cliente_id: int | None = None,
           vigentes: bool = False,
           offset: int = Query(0, ge=0), limite: int = Query(50, ge=1, le=100)):
    stmt = select(Contratacao)
    if cliente_id is not None:
        stmt = stmt.where(Contratacao.cliente_id == cliente_id)
    if vigentes:
        hoje = agora_local().date()
        stmt = stmt.where(Contratacao.data_inicio <= hoje,
                          or_(Contratacao.data_fim.is_(None), Contratacao.data_fim >= hoje))
    return [ContratacaoSaida.model_validate(c) for c in session.exec(
        stmt.order_by(Contratacao.id).offset(offset).limit(limite)).all()]


@router.get('/{contratacao_id}', response_model=ContratacaoSaida)
def buscar(contratacao_id: int, session: SessionDep, usuario: UsuarioDep):
    return ContratacaoSaida.model_validate(obter(session, Contratacao, contratacao_id))


@router.post('/{contratacao_id}/cancelar', response_model=ContratacaoSaida)
def cancelar(contratacao_id: int, session: SessionDep, usuario: UsuarioDep):
    ref = obter(session, Contratacao, contratacao_id)
    obter(session, Vaga, ref.vaga_id, True)
    obter(session, Cliente, ref.cliente_id, True)
    hoje = agora_local().date()
    gerar_mensalidades(session, usuario.id, hoje, ref.cliente_id)
    obj = obter(session, Contratacao, contratacao_id, True)
    if obj.data_fim is not None and obj.data_fim < hoje:
        raise HTTPException(409, 'Contratação já encerrada.')
    cobrancas = session.exec(select(Cobranca).where(
        Cobranca.contratacao_mensal_id == obj.id).order_by(Cobranca.id).with_for_update()).all()
    obj.data_fim = fim_cancelamento(obj, cobrancas, hoje)
    auditar(obj, usuario.id)
    salvar(session)
    return ContratacaoSaida.model_validate(obj)
