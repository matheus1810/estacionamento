"""Validação dos cadastros e respostas por campo sem abrir conexão com o banco."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import usuario_atual
from app.database import get_session
from app.main import app
from app.schemas import (
    ClienteCriar,
    ClienteEditar,
    PermanenciaCadastroCriar,
    SolicitacaoNotaFiscalEntrada,
    VeiculoCriar,
)


@pytest.mark.parametrize(
    'telefone,esperado',
    [
        ('11912345678', '11912345678'),
        ('(11) 91234-5678', '11912345678'),
        ('+55 (11) 91234-5678', '11912345678'),
        ('5511912345678', '11912345678'),
        ('(11) 3234-5678', '1132345678'),
        ('+55 (55) 3234-5678', '5532345678'),
    ],
)
def test_telefone_normaliza_fixo_e_celular(telefone, esperado):
    assert ClienteCriar(nome='João D’Ávila', telefone=telefone).telefone == esperado
    assert ClienteEditar(telefone=telefone).telefone == esperado


@pytest.mark.parametrize(
    'telefone',
    [
        'qualquer coisa',
        'abc11912345678',
        '123',
        '912345678',
        '01912345678',
        '1191234567',
        '11323456789',
        '99999999999',
        '+1 11912345678',
        '++55 11912345678',
    ],
)
def test_telefone_rejeita_formatos_invalidos(telefone):
    with pytest.raises(ValidationError):
        ClienteCriar(nome='Maria', telefone=telefone)


@pytest.mark.parametrize(
    'campo,valor', [('placa', '1234567'), ('modelo', '!!!'), ('cor', '123')]
)
def test_veiculo_rejeita_campos_invalidos(campo, valor):
    dados = {'cliente_id': 1, 'placa': 'ABC1D23', 'modelo': '208', 'cor': 'Prata/Preto'}
    dados[campo] = valor
    with pytest.raises(ValidationError):
        VeiculoCriar(**dados)


def test_nome_exige_letras_e_edicao_continua_parcial():
    with pytest.raises(ValidationError):
        ClienteCriar(nome='12345', telefone='11912345678')
    assert ClienteEditar(nome='Maria D’Ávila').model_dump(exclude_unset=True) == {
        'nome': 'Maria D’Ávila'
    }
    assert (
        VeiculoCriar(
            cliente_id=1, placa='abc-1234', modelo='F-150', cor='Azul-metálico'
        ).placa
        == 'ABC1234'
    )


@pytest.mark.parametrize(
    'nome', ['5L1212', 'João123', 'Maria 2', 'Ana@Silva', 'Maria_Clara', 'João１']
)
def test_nome_cliente_rejeita_numeros_e_simbolos(nome):
    for schema, dados in [
        (ClienteCriar, {'nome': nome, 'telefone': '11912345678'}),
        (ClienteEditar, {'nome': nome}),
        (PermanenciaCadastroCriar, {
            'vaga_id': 1, 'placa': 'ABC1D23', 'modelo': 'Uno', 'cor': 'Azul',
            'cliente': {'nome': nome, 'telefone': '11912345678'},
        }),
    ]:
        with pytest.raises(ValidationError):
            schema(**dados)


@pytest.mark.parametrize(
    'nome', ['João da Silva', "Ana D'Ávila", 'Maria-Clara', 'José D’Ávila', 'Joa\u0303o Silva']
)
def test_nome_cliente_preserva_acentos_e_separadores(nome):
    assert ClienteCriar(nome=nome, telefone='11912345678').nome


def test_razao_social_de_nota_continua_aceitando_numeros():
    dados = SolicitacaoNotaFiscalEntrada(nome='3M Transportes', documento='52998224725')
    assert dados.nome == '3M Transportes'


def test_api_rejeita_nome_da_imagem_na_criacao_edicao_e_cadastro_rapido(validation_client):
    payload = {'nome': '5L1212', 'telefone': '11912345678'}
    responses = [
        validation_client.post('/clientes', json=payload),
        validation_client.patch('/clientes/1', json={'nome': '5L1212'}),
        validation_client.post('/permanencias/cadastro-entrada', json={
            'vaga_id': 1, 'placa': 'ABC1D23', 'modelo': 'Uno', 'cor': 'Azul', 'cliente': payload,
        }),
    ]
    for response in responses:
        assert response.status_code == 422
        assert 'Números não são permitidos.' in response.json()['erros'][0]['mensagem']


@pytest.fixture
def validation_client():
    class Sessao:
        def exec(self, *_):
            pytest.fail(
                'Dados inválidos não podem chegar à consulta/gravação no banco.'
            )

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = lambda: Sessao()
    app.dependency_overrides[usuario_atual] = lambda: SimpleNamespace(id=1)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_api_indica_campos_sem_reproduzir_valores(validation_client):
    response = validation_client.post(
        '/clientes',
        json={
            'nome': '12345',
            'telefone': 'telefone-privado-invalido',
        },
    )
    assert response.status_code == 422
    errors = {error['campo']: error['mensagem'] for error in response.json()['erros']}
    assert set(errors) == {'nome', 'telefone'}
    assert errors['nome'].startswith('Nome:')
    assert 'DDD' in errors['telefone']
    assert 'telefone-privado-invalido' not in response.text
    response = validation_client.post(
        '/veiculos',
        json={
            'cliente_id': 1,
            'placa': '1234567',
            'modelo': '!!!',
            'cor': '123',
        },
    )
    assert response.status_code == 422
    assert {error['campo'] for error in response.json()['erros']} == {
        'placa',
        'modelo',
        'cor',
    }
    assert '!!!' not in response.text


def test_api_cadastro_rapido_indica_telefone_do_cliente(validation_client):
    response = validation_client.post(
        '/permanencias/cadastro-entrada',
        json={
            'vaga_id': 1,
            'placa': 'ABC1D23',
            'modelo': 'Uno',
            'cor': 'Azul',
            'cliente': {'nome': 'Cliente', 'telefone': '123'},
        },
    )
    assert response.status_code == 422
    assert response.json()['erros'][0]['campo'] == 'cliente.telefone'
    assert 'body.cliente.telefone' in response.json()['campos']
    assert (
        validation_client.patch(
            '/clientes/1', json={'telefone': 'invalido'}
        ).status_code
        == 422
    )
