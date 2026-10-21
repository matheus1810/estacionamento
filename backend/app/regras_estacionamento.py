from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from fastapi import HTTPException
from sqlmodel import or_, select

from .config import agora_local
from .models import Cobranca, Contratacao, Permanencia, Tarifa


def criacao(usuario_id):
    return dict(criado_em=agora_local(), criado_por=usuario_id)


def auditar(obj, usuario_id):
    obj.atualizado_em = agora_local()
    obj.atualizado_por = usuario_id


def calcular_horista(entrada, saida, valor_hora):
    delta = saida - entrada
    if delta < timedelta(0):
        raise HTTPException(409, 'Horário de saída anterior à entrada.')
    micros = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    blocos = max(1, int((Decimal(micros) / Decimal(1800000000)).to_integral_value(
        rounding=ROUND_CEILING)))
    valor = (Decimal(blocos) * valor_hora / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if valor > Decimal('99999999.99'):
        raise HTTPException(409, 'Valor excede o limite monetário do banco.')
    return blocos, valor


def vencimento(inicio: date, indice: int):
    mes_absoluto = inicio.year * 12 + inicio.month - 1 + indice
    ano, mes = divmod(mes_absoluto, 12)
    mes += 1
    return date(ano, mes, min(inicio.day, monthrange(ano, mes)[1]))


def periodo(inicio: date, indice: int):
    primeiro = vencimento(inicio, indice)
    return primeiro, vencimento(inicio, indice + 1) - timedelta(days=1)


def fim_periodo(inicio: date, vencimento_cobranca: date):
    indice = (vencimento_cobranca.year - inicio.year) * 12 + vencimento_cobranca.month - inicio.month
    return periodo(inicio, indice)[1]


def atrasada(cobranca, hoje):
    return cobranca.pago_em is None and cobranca.vencimento < hoje


def ocupada(session, vaga_id):
    return session.exec(select(Permanencia.id).where(
        Permanencia.vaga_id == vaga_id, Permanencia.saida.is_(None))).first() is not None


def reservas(session, vaga_id, inicio, fim=None):
    stmt = select(Contratacao).where(
        Contratacao.vaga_id == vaga_id,
        or_(Contratacao.data_fim.is_(None), Contratacao.data_fim >= inicio))
    if fim is not None:
        stmt = stmt.where(Contratacao.data_inicio <= fim)
    return session.exec(stmt).all()


def disponibilidade(session, vaga, hoje):
    if not vaga.ativa:
        return False, 'Vaga inativa.'
    if ocupada(session, vaga.id):
        return False, 'Vaga ocupada por horista.'
    if reservas(session, vaga.id, hoje, hoje):
        return False, 'Vaga reservada para mensalista.'
    return True, 'Vaga disponível.'


def tarifa_atual(session):
    tarifa = session.get(Tarifa, 1)
    if not tarifa:
        raise HTTPException(409, 'Cadastre as tarifas antes desta operação.')
    return tarifa


def gerar_mensalidades(session, usuario_id, hoje, cliente_id=None):
    """Bloqueia contratos por id; nunca faz commit. A tarifa é copiada só na criação.

    O chamador bloqueia cliente/vaga antes dos contratos quando necessário.
    Inclui encerrados para recuperar períodos faltantes anteriores ao encerramento.
    """
    stmt = select(Contratacao).where(Contratacao.data_inicio <= hoje)
    if cliente_id is not None:
        stmt = stmt.where(Contratacao.cliente_id == cliente_id)
    contratos = session.exec(stmt.order_by(Contratacao.id).with_for_update()
                             .execution_options(populate_existing=True)).all()
    geradas = 0
    for contrato in contratos:
        existentes = set(session.exec(select(Cobranca.competencia).where(
            Cobranca.contratacao_mensal_id == contrato.id)).all())
        limite = min(hoje, contrato.data_fim) if contrato.data_fim else hoje
        indice = 0
        while vencimento(contrato.data_inicio, indice) <= limite:
            inicio = vencimento(contrato.data_inicio, indice)
            competencia = inicio.replace(day=1)
            if competencia not in existentes:
                session.add(Cobranca(contratacao_mensal_id=contrato.id,
                    competencia=competencia, vencimento=inicio,
                    valor=tarifa_atual(session).valor_mensal_vaga, **criacao(usuario_id)))
                existentes.add(competencia)
                geradas += 1
            indice += 1
    session.flush()
    return geradas


def fim_cancelamento(contrato, cobrancas, hoje):
    if contrato.data_inicio > hoje:
        raise HTTPException(409, 'Contratação ainda não iniciada. Cancelamento antecipado não definido.')
    if not cobrancas:
        raise HTTPException(409, 'Atualize as mensalidades antes de cancelar.')
    # Decisão aprovada: havendo dívida, encerra no fim do último período iniciado,
    # preserva todas as cobranças e não renova depois dessa data.
    fim = max(fim_periodo(contrato.data_inicio, c.vencimento) for c in cobrancas
              if c.vencimento <= hoje)
    # Períodos futuros não são criados nem pagos por esta API.
    if fim < hoje:
        raise HTTPException(409, 'Atualize as mensalidades antes de cancelar.')
    return min(fim, contrato.data_fim) if contrato.data_fim else fim
