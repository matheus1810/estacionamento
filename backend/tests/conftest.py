import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine

from app.auth import hash_senha
from app.config import get_settings
from app.database import get_session
from app.main import app
from app.models import Usuario
from app.regras_estacionamento import criacao


@pytest.fixture
def mysql_client(monkeypatch):
    raw_url = os.getenv('TEST_DATABASE_URL')
    if not raw_url:
        pytest.skip('Configure TEST_DATABASE_URL para um MySQL isolado com o SQL original importado.')
    url = make_url(raw_url)
    # Não aceita banco de desenvolvimento, SQLite nem nomes ambíguos.
    if url.drivername != 'mysql+pymysql' or not url.database or not url.database.endswith('_test'):
        pytest.fail('TEST_DATABASE_URL deve usar mysql+pymysql e banco com sufixo _test.')
    if os.getenv('DB_NAME') == url.database:
        pytest.fail('O banco de integração precisa ser diferente do banco da aplicação.')
    engine = create_engine(url, isolation_level='READ COMMITTED')
    assert set(inspect(engine).get_table_names()) >= {
        'usuarios','clientes','veiculos','vagas','tarifas','contratacoes_mensais','permanencias','cobrancas',
    }, 'Importe o SQL original no banco de teste antes de executar.'
    monkeypatch.setenv('DB_NAME','nao_conectado')
    monkeypatch.setenv('DB_USER','exemplo')
    monkeypatch.setenv('DB_PASSWORD','exemplo')
    monkeypatch.setenv('JWT_SECRET','segredo-exclusivo-dos-testes-mysql-123456')
    get_settings.cache_clear()
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            # Os commits da API liberam savepoints; o rollback externo restaura os dados.
            with Session(connection, join_transaction_mode='create_savepoint', expire_on_commit=False) as session:
                from uuid import uuid4
                login = 'teste_' + uuid4().hex[:16]
                operador = Usuario(nome='Teste integração',login=login,senha_hash=hash_senha('senha-integracao'),**criacao(None))
                session.add(operador)
                session.commit()
                app.dependency_overrides[get_session] = lambda: session
                with TestClient(app) as client:
                    resposta = client.post('/auth/login',json={'login':login,'senha':'senha-integracao'})
                    assert resposta.status_code == 200
                    client.headers['Authorization'] = 'Bearer ' + resposta.json()['access_token']
                    yield client,session
                session.rollback()
            outer.rollback()
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        engine.dispose()
