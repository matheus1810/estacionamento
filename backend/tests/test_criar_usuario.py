"""Diagnóstico do primeiro operador sem expor senha e sem acessar banco real."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import Settings
from scripts import criar_usuario


@pytest.mark.parametrize('nome,login,senha,campo', [
    ('Matheus', 'admin', 'curta', 'Senha'),
    ('', 'admin', 'senha-exclusiva-do-teste', 'Nome'),
    ('Matheus', '', 'senha-exclusiva-do-teste', 'Login'),
    ('Matheus', 'admin', '        ', 'Senha'),
])
def test_diagnostico_indica_campo_sem_salvar_ou_expor_valores(
    monkeypatch, capsys, nome, login, senha, campo,
):
    class Sessao:
        def exec(self, *_):
            return self

        def scalar(self):
            return 1

        def first(self):
            return None

        def rollback(self):
            pass

        def add(self, *_):
            pytest.fail('Não deve salvar operador com dados inválidos.')

        def commit(self):
            pytest.fail('Não deve confirmar operador com dados inválidos.')

    monkeypatch.setattr(criar_usuario, 'get_engine', lambda: SimpleNamespace(
        connect=lambda: nullcontext(object()),
    ))
    monkeypatch.setattr(criar_usuario, 'Session', lambda _: nullcontext(Sessao()))
    respostas = iter([nome, login])
    monkeypatch.setattr('builtins.input', lambda _: next(respostas))
    monkeypatch.setattr(criar_usuario, 'getpass', lambda _: senha)
    assert criar_usuario.main() == 1
    output = capsys.readouterr().out
    assert 'Dados do operador inválidos:' in output
    assert campo + ':' in output
    assert senha not in output
    if campo == 'Senha':
        assert '8' in output


def test_diagnostico_configuracao_nao_mostra_segredos(capsys):
    with pytest.raises(ValidationError) as captured:
        Settings(_env_file=None, db_name='exemplo', db_user='exemplo',
                 db_password='senha-privada-do-banco', jwt_secret='segredo-curto')
    criar_usuario.mostrar_erros_validacao(captured.value)
    output = capsys.readouterr().out
    assert 'JWT_SECRET' in output and '32' in output
    assert 'segredo-curto' not in output
    assert 'senha-privada-do-banco' not in output
