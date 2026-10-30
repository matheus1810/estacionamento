"""Registro do pedido de nota fiscal na mesma transação do pagamento."""

from sqlmodel import select

from .config import agora_local
from .models import SolicitacaoNotaFiscal
from .schemas import CobrancaSaida


def registrar_solicitacao(session, cobranca, dados, usuario_id):
    if dados is None:
        return
    # A saída horista cria a cobrança nesta transação; obtém o ID sem commit.
    session.flush()
    session.add(
        SolicitacaoNotaFiscal(
            cobranca_id=cobranca.id,
            **dados.model_dump(),
            criado_em=agora_local(),
            criado_por=usuario_id,
        )
    )


def listar_cobrancas_com_solicitacao(session, cobrancas):
    if not cobrancas:
        return []
    ids = set(
        session.exec(
            select(SolicitacaoNotaFiscal.cobranca_id).where(
                SolicitacaoNotaFiscal.cobranca_id.in_([c.id for c in cobrancas])
            )
        ).all()
    )
    result = []
    for cobranca in cobrancas:
        response = CobrancaSaida.model_validate(cobranca)
        response.nota_fiscal_solicitada = cobranca.id in ids
        result.append(response)
    return result
