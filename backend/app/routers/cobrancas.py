from fastapi import APIRouter, HTTPException, Query
from sqlmodel import or_, select

from ..auth import UsuarioDep
from ..config import agora_local
from ..database import SessionDep, obter, salvar
from ..models import Cliente, Cobranca, Contratacao, Vaga, Veiculo
from ..regras_estacionamento import auditar, gerar_mensalidades
from ..schemas import (
    AcessoEntrada, AcessoSaida, CobrancaSaida, GeracaoSaida, PagamentoEntrada,
)

router = APIRouter(prefix='/cobrancas', tags=['Cobranças'])


@router.post('/atualizar-mensalidades', response_model=GeracaoSaida)
def atualizar(session: SessionDep, usuario: UsuarioDep):
    geradas = gerar_mensalidades(session, usuario.id, agora_local().date())
    salvar(session)
    return GeracaoSaida(geradas=geradas)


@router.get('', response_model=list[CobrancaSaida])
def listar(session: SessionDep, usuario: UsuarioDep, pendentes: bool | None = None,
           contratacao_id: int | None = None, offset: int = Query(0, ge=0),
           limite: int = Query(50, ge=1, le=100)):
    stmt = select(Cobranca)
    if pendentes is not None:
        stmt = stmt.where(Cobranca.pago_em.is_(None) if pendentes else Cobranca.pago_em.is_not(None))
    if contratacao_id is not None:
        stmt = stmt.where(Cobranca.contratacao_mensal_id == contratacao_id)
    return [CobrancaSaida.model_validate(c) for c in session.exec(
        stmt.order_by(Cobranca.id).offset(offset).limit(limite)).all()]


@router.post('/{cobranca_id}/pagar', response_model=CobrancaSaida)
def pagar(cobranca_id: int, dados: PagamentoEntrada, session: SessionDep, usuario: UsuarioDep):
    obj = obter(session, Cobranca, cobranca_id, True)
    if obj.contratacao_mensal_id is None:
        raise HTTPException(409, 'Horistas devem pagar no endpoint de saída.')
    if obj.pago_em is not None:
        raise HTTPException(409, 'Cobrança já paga.')
    obj.pago_em = agora_local()
    obj.forma_pagamento = dados.forma_pagamento
    obj.usuario_recebimento_id = usuario.id
    auditar(obj, usuario.id)
    salvar(session)
    return CobrancaSaida.model_validate(obj)


@router.post('/consultar-acesso', response_model=AcessoSaida)
def acesso(dados: AcessoEntrada, session: SessionDep, usuario: UsuarioDep):
    veiculo = session.exec(select(Veiculo).where(Veiculo.placa == dados.placa)
                          .with_for_update()).first()
    if veiculo is None:
        raise HTTPException(404, 'Veículo não encontrado.')
    cliente = obter(session, Cliente, veiculo.cliente_id, True)
    if not cliente.ativo:
        return AcessoSaida(liberado=False, motivo='Cliente inativo.')
    hoje = agora_local().date()
    vigentes = session.exec(select(Contratacao).join(Vaga, Vaga.id == Contratacao.vaga_id).where(
        Contratacao.cliente_id == cliente.id, Vaga.ativa.is_(True),
        Contratacao.data_inicio <= hoje,
        or_(Contratacao.data_fim.is_(None), Contratacao.data_fim >= hoje))).all()
    if not vigentes:
        return AcessoSaida(liberado=False, motivo='Sem contratação vigente em vaga ativa.')
    gerar_mensalidades(session, usuario.id, hoje, cliente.id)
    vencida = session.exec(select(Cobranca.id).join(
        Contratacao, Contratacao.id == Cobranca.contratacao_mensal_id).where(
        Contratacao.cliente_id == cliente.id, Cobranca.pago_em.is_(None),
        Cobranca.vencimento < hoje)).first()
    salvar(session)  # Geração persiste também quando o acesso é bloqueado por dívida.
    if vencida:
        return AcessoSaida(liberado=False, motivo='Cliente possui mensalidade vencida e não paga.')
    return AcessoSaida(liberado=True, motivo='Acesso liberado. Presença controlada manualmente.',
                       vagas=[c.vaga_id for c in vigentes])
