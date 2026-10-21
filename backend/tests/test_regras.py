from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.regras_estacionamento import atrasada, calcular_horista, fim_cancelamento, periodo, vencimento
from app.schemas import ClienteCriar, UsuarioCriar, VeiculoCriar


@pytest.mark.parametrize('segundos,blocos', [(0, 1), (1800, 1), (1801, 2), (4800, 3), (5400, 3)])
def test_blocos_horistas(segundos, blocos):
    entrada = datetime(2026, 10, 16, 10)
    assert calcular_horista(entrada, entrada + timedelta(seconds=segundos), Decimal('10')) == (
        blocos, Decimal(blocos * 5))


def test_fracao_de_segundo_e_arredondamento():
    entrada = datetime(2026, 10, 16, 10)
    assert calcular_horista(entrada, entrada + timedelta(minutes=30, microseconds=1), Decimal('10'))[0] == 2
    assert calcular_horista(entrada, entrada, Decimal('0.01'))[1] == Decimal('0.01')


@pytest.mark.parametrize('ano,fevereiro', [(2023, 28), (2024, 29)])
def test_vencimento_31_preserva_ancora(ano, fevereiro):
    inicio = date(ano, 1, 31)
    assert vencimento(inicio, 1) == date(ano, 2, fevereiro)
    assert vencimento(inicio, 2) == date(ano, 3, 31)
    assert periodo(inicio, 1) == (date(ano, 2, fevereiro), date(ano, 3, 30))


def test_periodo_e_competencia():
    inicio, fim = periodo(date(2026, 10, 16), 0)
    assert (inicio, fim) == (date(2026, 10, 16), date(2026, 11, 15))
    assert inicio.replace(day=1) == date(2026, 10, 1)


@pytest.mark.parametrize('pago', [False, True])
def test_cancelamento_preserva_periodo_e_divida(pago):
    contrato = SimpleNamespace(data_inicio=date(2026, 10, 16), data_fim=None)
    cobranca = SimpleNamespace(vencimento=date(2026, 10, 16), pago_em=datetime(2026, 10, 16) if pago else None)
    assert fim_cancelamento(contrato, [cobranca], date(2026, 10, 30)) == date(2026, 11, 15)
    assert (cobranca.pago_em is not None) == pago


def test_atraso_so_depois_do_vencimento():
    hoje = date(2026, 10, 20)
    assert not atrasada(SimpleNamespace(pago_em=None, vencimento=hoje), hoje)
    assert atrasada(SimpleNamespace(pago_em=None, vencimento=hoje - timedelta(days=1)), hoje)
    assert not atrasada(SimpleNamespace(pago_em=datetime(2026, 10, 20), vencimento=date(2026, 10, 19)), hoje)


def test_validacao_texto_placa_auditoria():
    with pytest.raises(ValidationError):
        ClienteCriar(nome='  ', telefone='123')
    with pytest.raises(ValidationError):
        ClienteCriar(nome='Ana', telefone='123', criado_por=7)
    with pytest.raises(ValidationError):
        UsuarioCriar(nome='Ana', login='ana', senha='        ')
    dados = VeiculoCriar(cliente_id=1, placa='abc-1d23', modelo='Uno', cor='azul')
    assert dados.placa == 'ABC1D23'
    assert VeiculoCriar(cliente_id=1, placa='abc 1234', modelo='Uno', cor='azul').placa == 'ABC1234'
    with pytest.raises(ValidationError):
        VeiculoCriar(cliente_id=1, placa='1234567', modelo='Uno', cor='azul')


def test_url_aceita_senha_com_caracteres_especiais():
    settings = Settings(_env_file=None, db_name='exemplo', db_user='operador',
                        db_password='a@b:/?#', jwt_secret='x' * 32)
    assert settings.database_url.password == 'a@b:/?#'
