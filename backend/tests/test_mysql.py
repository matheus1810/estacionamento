from datetime import timedelta

import pytest
from sqlmodel import select

from app.config import agora_local
from app.models import Cobranca

pytestmark = pytest.mark.mysql


def criar(client, path, body):
    response = client.post(path,json=body)
    assert response.status_code == 201, response.text
    return response.json()


def cadastros(client):
    from uuid import uuid4
    suffix = uuid4().hex[:7]
    # Fixture exige banco dedicado com tarifas ainda não cadastradas ou existentes.
    tarifa = client.get('/tarifas')
    if tarifa.status_code == 404:
        criar(client,'/tarifas',{'valor_hora':'10.00','valor_mensal_vaga':'300.00'})
    else:
        assert client.put('/tarifas',json={'valor_hora':'10.00','valor_mensal_vaga':'300.00'}).status_code == 200
    cliente = criar(client,'/clientes',{'nome':'Cliente '+suffix,'telefone':'11999999999'})
    veiculo = criar(client,'/veiculos',{'cliente_id':cliente['id'],'placa':'TST1A23','modelo':'Uno','cor':'azul'})
    vaga = criar(client,'/vagas',{'numero':suffix})
    return cliente,veiculo,vaga


def test_entrada_ocupada_saida_repetida_e_historico(mysql_client):
    client,session = mysql_client
    cliente,veiculo,vaga = cadastros(client)
    dados = {'veiculo_id':veiculo['id'],'vaga_id':vaga['id']}
    permanencia = criar(client,'/permanencias',dados)
    assert permanencia['cliente_id'] == cliente['id']
    assert permanencia['valor_hora_aplicado'] == '10.00'
    outro = criar(client,'/veiculos',{'cliente_id':cliente['id'],'placa':'TST1A24','modelo':'Gol','cor':'preto'})
    assert client.post('/permanencias',json={**dados,'veiculo_id':outro['id']}).status_code == 409
    assert client.patch('/vagas/'+str(vaga['id']),json={'ativa':False}).status_code == 409
    assert client.get(f"/permanencias/{permanencia['id']}/previa").json()['valor'] == '5.00'
    novo = criar(client,'/clientes',{'nome':'Novo responsável','telefone':'11988888888'})
    assert client.patch('/veiculos/'+str(veiculo['id']),json={'cliente_id':novo['id']}).status_code == 200
    assert client.get('/permanencias').json()[0]['cliente_id'] == cliente['id']
    saida = client.post(f"/permanencias/{permanencia['id']}/saida",json={'forma_pagamento':'pix'})
    assert saida.status_code == 200
    assert saida.json()['pago_em'] is not None
    assert client.post(f"/permanencias/{permanencia['id']}/saida",json={'forma_pagamento':'pix'}).status_code == 409
    assert client.post(f"/cobrancas/{saida.json()['id']}/pagar",json={'forma_pagamento':'pix'}).status_code == 409
    assert len(session.exec(select(Cobranca).where(Cobranca.permanencia_id==permanencia['id'])).all()) == 1


def test_reserva_mensalidade_unica_acesso_pagamento_e_cancelamento(mysql_client):
    client,session = mysql_client
    cliente,veiculo,vaga = cadastros(client)
    hoje = agora_local().date()
    contrato = criar(client,'/contratacoes',{'cliente_id':cliente['id'],'vaga_id':vaga['id'],'data_inicio':hoje.isoformat()})
    assert client.post('/permanencias',json={'veiculo_id':veiculo['id'],'vaga_id':vaga['id']}).status_code == 409
    assert client.post('/contratacoes',json={'cliente_id':cliente['id'],'vaga_id':vaga['id'],'data_inicio':hoje.isoformat()}).status_code == 409
    assert client.post('/cobrancas/atualizar-mensalidades').status_code == 200
    assert client.post('/cobrancas/atualizar-mensalidades').status_code == 200
    cobrancas = session.exec(select(Cobranca).where(Cobranca.contratacao_mensal_id==contrato['id'])).all()
    assert len(cobrancas) == 1
    assert cobrancas[0].competencia == hoje.replace(day=1)
    assert client.post('/cobrancas/consultar-acesso',json={'placa':veiculo['placa']}).json()['liberado'] is True
    cobrancas[0].vencimento = hoje - timedelta(days=1)
    session.commit()
    assert client.post('/cobrancas/consultar-acesso',json={'placa':veiculo['placa']}).json()['liberado'] is False
    cobrancas[0].vencimento = hoje
    session.commit()
    pagamento = f'/cobrancas/{cobrancas[0].id}/pagar'
    assert client.post(pagamento,json={'forma_pagamento':'cartao'}).status_code == 200
    assert client.post(pagamento,json={'forma_pagamento':'dinheiro'}).status_code == 409
    cancelamento = client.post(f"/contratacoes/{contrato['id']}/cancelar")
    assert cancelamento.status_code == 200
    assert cancelamento.json()['data_fim'] >= hoje.isoformat()
    assert client.get('/contratacoes').status_code == 200


def test_cancelar_com_divida_preserva_cobrancas(mysql_client):
    client,session = mysql_client
    cliente,veiculo,vaga = cadastros(client)
    contrato = criar(client,'/contratacoes',{'cliente_id':cliente['id'],'vaga_id':vaga['id'],'data_inicio':agora_local().date().isoformat()})
    assert client.post(f"/contratacoes/{contrato['id']}/cancelar").status_code == 200
    cobrancas = session.exec(select(Cobranca).where(Cobranca.contratacao_mensal_id==contrato['id'])).all()
    assert len(cobrancas) == 1 and cobrancas[0].pago_em is None
