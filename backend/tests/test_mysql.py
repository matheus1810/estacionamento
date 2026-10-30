from datetime import timedelta

import pytest
from sqlmodel import select

from app.config import agora_local
from app.models import Cliente, Cobranca, Permanencia, SolicitacaoNotaFiscal, Veiculo

pytestmark = pytest.mark.mysql


def test_solicitacao_nf_horista_e_mensalista_persistem_no_pagamento(mysql_client):
    client, session = mysql_client
    cliente, veiculo, vaga = cadastros(client)
    permanencia = criar(client, '/permanencias', {
        'veiculo_id': veiculo['id'], 'vaga_id': vaga['id'],
    })
    fiscal = {'nome': 'Cliente Fiscal', 'documento': '529.982.247-25',
              'email': 'cliente@example.com', 'endereco': 'Rua A, 10'}
    pagamento = {'forma_pagamento': 'pix', 'nota_fiscal': fiscal}
    path = f"/permanencias/{permanencia['id']}/saida"
    resposta = client.post(path, json=pagamento)
    assert resposta.status_code == 200, resposta.text
    cobranca_id = resposta.json()['id']
    assert resposta.json()['nota_fiscal_solicitada'] is True
    assert client.post(path, json=pagamento).status_code == 409
    pedido = client.get(f'/cobrancas/{cobranca_id}/nota-fiscal')
    assert pedido.status_code == 200
    assert pedido.json()['nome'] == fiscal['nome']
    assert pedido.json()['documento'] == '52998224725'
    assert pedido.json()['email'] == fiscal['email']
    lista = client.get('/cobrancas?nota_fiscal=true').json()
    assert [c['id'] for c in lista] == [cobranca_id]
    assert lista[0]['nota_fiscal_solicitada'] is True
    assert 'documento' not in lista[0]
    contrato = criar(client, '/contratacoes', {
        'cliente_id': cliente['id'], 'vaga_id': vaga['id'],
        'data_inicio': agora_local().date().isoformat(),
    })
    mensalidade = client.get(f"/cobrancas?contratacao_id={contrato['id']}").json()[0]
    pagamento['nota_fiscal']['documento'] = '00.000.000/E08G-12'
    resposta = client.post(f"/cobrancas/{mensalidade['id']}/pagar", json=pagamento)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()['nota_fiscal_solicitada'] is True
    assert client.get(f"/cobrancas/{mensalidade['id']}/nota-fiscal").json()['documento'] == '00000000E08G12'
    pedidos = session.exec(select(SolicitacaoNotaFiscal)).all()
    assert len(pedidos) == 2
    assert all(p.criado_por and p.criado_em for p in pedidos)
    assert client.get('/cobrancas/999999/nota-fiscal').status_code == 404


def test_falha_ao_salvar_nf_reverte_saida_e_pagamento(mysql_client):
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError

    client, session = mysql_client
    _, veiculo, vaga = cadastros(client)
    permanencia = criar(client, '/permanencias', {
        'veiculo_id': veiculo['id'], 'vaga_id': vaga['id'],
    })
    path = f"/permanencias/{permanencia['id']}/saida"
    pagamento = {'forma_pagamento': 'dinheiro', 'nota_fiscal': {
        'nome': 'Cliente Fiscal', 'documento': '52998224725',
    }}
    invalido = {**pagamento, 'nota_fiscal': {'nome': '', 'documento': '123'}}
    assert client.post(path, json=invalido).status_code == 422

    def falhar_nf(sessao, *_):
        if any(isinstance(obj, SolicitacaoNotaFiscal) for obj in sessao.new):
            raise IntegrityError('Falha simulada no pedido de nota', None, Exception())

    event.listen(session, 'before_flush', falhar_nf)
    try:
        assert client.post(path, json=pagamento).status_code == 409
    finally:
        event.remove(session, 'before_flush', falhar_nf)
    aberta = session.get(Permanencia, permanencia['id'])
    assert aberta.saida is None
    assert aberta.usuario_saida_id is None
    assert session.exec(select(Cobranca).where(Cobranca.permanencia_id == aberta.id)).first() is None
    assert not session.exec(select(SolicitacaoNotaFiscal)).all()
    assert client.post(path, json=pagamento).status_code == 200


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
    # A consulta mantém o cliente da entrada mesmo após trocar o responsável.
    historico = client.get(f"/veiculos/{veiculo['id']}/historico").json()
    assert len(historico) == 1
    assert historico[0]['permanencia_id'] == permanencia['id']
    assert historico[0]['cliente_id'] == cliente['id']
    assert historico[0]['valor_cobrado'] == saida.json()['valor']
    assert historico[0]['forma_pagamento'] == 'pix'
    assert client.get(f"/veiculos/{outro['id']}/historico").json() == []
    segunda = criar(client, '/permanencias', dados)
    pagina = client.get(f"/veiculos/{veiculo['id']}/historico?limite=1").json()
    assert pagina[0]['permanencia_id'] == segunda['id']
    assert pagina[0]['saida'] is None
    anterior = client.get(f"/veiculos/{veiculo['id']}/historico?offset=1&limite=1").json()
    assert anterior[0]['permanencia_id'] == permanencia['id']


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
    vencidas=client.get('/cobrancas',params={'cliente_id':cliente['id'],'vencidas':True}).json()
    assert [c['id'] for c in vencidas]==[cobrancas[0].id]
    assert client.get('/cobrancas',params={'cliente_id':cliente['id']+10000,'vencidas':True}).json()==[]
    vigentes=client.get('/contratacoes',params={'cliente_id':cliente['id'],'vigentes':True}).json()
    assert [c['id'] for c in vigentes]==[contrato['id']]
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


def test_cadastro_e_entrada_atomicos_sem_cadastros_orfaos(mysql_client):
    client,session=mysql_client
    cliente,veiculo,vaga=cadastros(client)
    criar(client,'/permanencias',{'veiculo_id':veiculo['id'],'vaga_id':vaga['id']})
    antes_clientes=len(session.exec(select(Cliente)).all())
    antes_veiculos=len(session.exec(select(Veiculo)).all())
    body={'vaga_id':vaga['id'],'placa':'NEW1A23','modelo':'Argo','cor':'Branco',
          'cliente':{'nome':'Cadastro rápido','telefone':'11912345678'}}
    conflito=client.post('/permanencias/cadastro-entrada',json=body)
    assert conflito.status_code==409
    # O rollback da requisição deve remover os INSERTs parciais sem ajuda do teste.
    assert len(session.exec(select(Cliente)).all())==antes_clientes
    assert len(session.exec(select(Veiculo)).all())==antes_veiculos
    nova_vaga=criar(client,'/vagas',{'numero':'RAPIDA'})
    body['vaga_id']=nova_vaga['id']
    permanencia=criar(client,'/permanencias/cadastro-entrada',body)
    novo_veiculo=session.get(Veiculo,permanencia['veiculo_id'])
    assert novo_veiculo.placa=='NEW1A23'
    assert novo_veiculo.cliente_id==permanencia['cliente_id']
    assert len(session.exec(select(Cliente)).all())==antes_clientes+1
    assert len(session.exec(select(Veiculo)).all())==antes_veiculos+1
    repetida=client.post('/permanencias/cadastro-entrada',json=body)
    assert repetida.status_code==409
    assert len(session.exec(select(Cliente)).all())==antes_clientes+1
    existente=criar(client,'/vagas',{'numero':'EXISTENTE'})
    outro=criar(client,'/permanencias/cadastro-entrada',{
        'vaga_id':existente['id'],'placa':'NEW1A24','modelo':'Gol','cor':'Prata','cliente_id':cliente['id']})
    assert outro['cliente_id']==cliente['id']
    assert len(session.exec(select(Cliente)).all())==antes_clientes+1
    filtradas=client.get('/permanencias',params={'abertas':True,'veiculo_id':permanencia['veiculo_id']}).json()
    assert len(filtradas)==1 and filtradas[0]['id']==permanencia['id']
