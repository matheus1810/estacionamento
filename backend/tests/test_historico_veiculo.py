"""Contrato HTTP e consulta do histórico com sessão simulada, sem banco real."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import mysql

from app.auth import usuario_atual
from app.database import get_session
from app.main import app


@pytest.fixture
def historico_client():
    class Sessao:
        veiculo = SimpleNamespace(id=9, cliente_id=42)
        rows = []
        consultas = []

        def exec(self, consulta):
            self.consultas.append(consulta)
            return SimpleNamespace(first=lambda: self.veiculo, all=lambda: self.rows)

    sessao = Sessao()
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = lambda: sessao
    app.dependency_overrides[usuario_atual] = lambda: SimpleNamespace(id=1)
    try:
        yield TestClient(app), sessao
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_historico_retorna_entrada_aberta_e_saida_paga(historico_client):
    client, sessao = historico_client
    entrada = datetime(2026, 10, 30, 9)
    saida = datetime(2026, 10, 30, 10, 20)
    aberta = SimpleNamespace(
        id=12,
        entrada=saida,
        saida=None,
        cliente_id=42,
        valor_hora_aplicado=Decimal('12.00'),
    )
    encerrada = SimpleNamespace(
        id=11,
        entrada=entrada,
        saida=saida,
        cliente_id=7,
        valor_hora_aplicado=Decimal('10.00'),
    )
    cobranca = SimpleNamespace(
        valor=Decimal('15.00'), pago_em=saida, forma_pagamento='pix'
    )
    sessao.rows = [
        (aberta, 'Cliente atual', 'B-02', 'Ana', None, None),
        (encerrada, 'Cliente da entrada', 'A-01', 'Ana', 'Bruno', cobranca),
    ]
    resposta = client.get('/veiculos/9/historico?offset=10&limite=11')
    assert resposta.status_code == 200, resposta.text
    aberta_json, encerrada_json = resposta.json()
    assert aberta_json['saida'] is None
    assert aberta_json['valor_cobrado'] is None
    assert aberta_json['operador_saida'] is None
    assert encerrada_json['cliente_id'] == 7  # Mantém o cliente da permanência.
    assert encerrada_json['cliente_nome'] == 'Cliente da entrada'
    assert encerrada_json['valor_hora_aplicado'] == '10.00'
    assert encerrada_json['valor_cobrado'] == '15.00'
    assert encerrada_json['forma_pagamento'] == 'pix'
    assert encerrada_json['operador_saida'] == 'Bruno'
    consulta = sessao.consultas[-1].compile(dialect=mysql.dialect())
    sql = str(consulta)
    assert 'WHERE permanencias.veiculo_id = ' in sql
    assert 'ORDER BY permanencias.entrada DESC, permanencias.id DESC' in sql
    assert 'LEFT OUTER JOIN cobrancas' in sql
    assert set(consulta.params.values()) == {9, 10, 11}


def test_historico_vazio_inexistente_e_autenticacao(historico_client):
    client, sessao = historico_client
    assert client.get('/veiculos/9/historico').json() == []
    sessao.veiculo = None
    assert client.get('/veiculos/999/historico').status_code == 404
    app.dependency_overrides.pop(usuario_atual)
    assert client.get('/veiculos/9/historico').status_code == 401


@pytest.mark.parametrize('params', ['offset=-1', 'limite=0', 'limite=101'])
def test_historico_valida_paginacao(historico_client, params):
    client, _ = historico_client
    assert client.get('/veiculos/9/historico?' + params).status_code == 422
