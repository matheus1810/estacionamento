from datetime import datetime
from types import SimpleNamespace

import pytest

from app.auth import verificar_senha
from scripts import redefinir_senha


@pytest.mark.parametrize('senha,confirmacao', [('senha-de-teste', 'outra-senha'), ('curta', 'curta'), ('        ', '        ')])
def test_recusa_dados_invalidos_sem_acessar_banco(monkeypatch, capsys, senha, confirmacao):
    entradas = iter([senha, confirmacao])
    monkeypatch.setattr(redefinir_senha, 'getpass', lambda _: next(entradas))
    def acesso_indevido():
        pytest.fail('Não deve abrir conexão com entradas inválidas.')
    monkeypatch.setattr(redefinir_senha, 'get_engine', acesso_indevido)
    assert redefinir_senha.main(['--login', 'matheus']) == 1
    saida = capsys.readouterr().out
    assert senha not in saida and confirmacao not in saida


def test_redefine_hash_e_auditoria_sem_expor_senha(monkeypatch, capsys):
    senha = 'nova-senha-exclusiva-do-teste'
    usuario = SimpleNamespace(id=7, ativo=True, senha_hash='hash-antiga',
                              criado_em=datetime(2026, 10, 16), criado_por=None)
    commits = []
    class Sessao:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def exec(self, stmt):
            return self
        def first(self):
            return usuario
        def commit(self):
            commits.append(True)
    monkeypatch.setattr(redefinir_senha, 'getpass', lambda _: senha)
    monkeypatch.setattr(redefinir_senha, 'get_engine', lambda: None)
    monkeypatch.setattr(redefinir_senha, 'Session', lambda _: Sessao())
    monkeypatch.setattr('app.regras_estacionamento.agora_local', lambda: datetime(2026, 10, 27, 10))
    assert redefinir_senha.main(['--login', 'matheus']) == 0
    assert commits == [True]
    assert verificar_senha(senha, usuario.senha_hash)
    assert usuario.atualizado_por == 7
    assert usuario.atualizado_em == datetime(2026, 10, 27, 10)
    assert usuario.criado_em == datetime(2026, 10, 16)
    assert usuario.criado_por is None
    saida = capsys.readouterr().out
    assert senha not in saida and usuario.senha_hash not in saida
