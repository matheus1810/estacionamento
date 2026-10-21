from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth import hash_senha
from app.config import get_settings
from app.database import get_session
from app.main import app
from app.schemas import UsuarioSaida


@pytest.fixture
def operador(monkeypatch):
    monkeypatch.setenv('DB_NAME', 'nao_conectado')
    monkeypatch.setenv('DB_USER', 'exemplo')
    monkeypatch.setenv('DB_PASSWORD', 'exemplo')
    monkeypatch.setenv('JWT_SECRET', 'segredo-exclusivo-dos-testes-unitarios-1234')
    get_settings.cache_clear()
    obj = SimpleNamespace(id=1, nome='Ana', login='ana', senha_hash=hash_senha('senha-teste'),
                          ativo=True, criado_em=datetime(2026, 10, 16), criado_por=None,
                          atualizado_em=None, atualizado_por=None)
    class Consulta:
        def first(self):
            return obj
    class Sessao:
        def get(self, *args):
            return obj
        def exec(self, *args):
            return Consulta()
    app.dependency_overrides[get_session] = lambda: Sessao()
    yield obj
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_login_invalido_e_inativo(operador):
    with TestClient(app) as client:
        assert client.post('/auth/login', json={'login': 'ana', 'senha': 'errada'}).status_code == 401
        operador.ativo = False
        assert client.post('/auth/login', json={'login': 'ana', 'senha': 'senha-teste'}).status_code == 401


def test_token_revalida_ativo_e_nao_expoe_hash(operador):
    with TestClient(app) as client:
        resposta = client.post('/auth/login', json={'login': 'ana', 'senha': 'senha-teste'})
        assert resposta.status_code == 200
        headers = {'Authorization': 'Bearer ' + resposta.json()['access_token']}
        me = client.get('/auth/me', headers=headers)
        assert me.status_code == 200
        assert 'senha_hash' not in me.json()
        assert 'senha_hash' not in UsuarioSaida.model_validate(operador).model_dump()
        operador.ativo = False
        assert client.get('/auth/me', headers=headers).status_code == 401
        assert client.get('/auth/me').status_code == 401


def test_jwt_expirado_e_validacao_sem_eco_de_senha(operador):
    with TestClient(app) as client:
        now = datetime.now(timezone.utc)
        token = jwt.encode({'sub': '1', 'iat': now - timedelta(hours=2), 'exp': now - timedelta(hours=1)},
                           get_settings().jwt_secret.get_secret_value(), algorithm='HS256')
        assert client.get('/auth/me', headers={'Authorization': 'Bearer ' + token}).status_code == 401
        resposta = client.post('/auth/login', json={'login': 'ana', 'senha': 'secreto', 'extra': 'indevido'})
        assert resposta.status_code == 422
        assert 'secreto' not in resposta.text
