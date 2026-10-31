"""Executar em backend: python -m scripts.criar_usuario."""

from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.auth import hash_senha
from app.database import get_engine
from app.erros_validacao import mensagens_por_campo
from app.models import Usuario
from app.regras_estacionamento import criacao
from app.schemas import UsuarioCriar


def mostrar_erros_validacao(error):
    if error.title == 'Settings':
        print('Configuração inválida no backend/.env ou nas variáveis do terminal:')
        campos = {
            'db_host': 'DB_HOST', 'db_port': 'DB_PORT', 'db_name': 'DB_NAME',
            'db_user': 'DB_USER', 'db_password': 'DB_PASSWORD',
            'jwt_secret': 'JWT_SECRET', 'jwt_expire_minutes': 'JWT_EXPIRE_MINUTES',
            'app_timezone': 'APP_TIMEZONE',
        }
        for item in error.errors():
            campo = campos.get(str(item['loc'][0]), 'Configuração')
            if item['type'] == 'missing':
                mensagem = 'campo obrigatório; preencha no arquivo .env.'
            elif campo == 'JWT_SECRET':
                mensagem = 'use uma chave aleatória com pelo menos 32 caracteres.'
            elif campo == 'DB_PORT':
                mensagem = 'informe uma porta numérica entre 1 e 65535.'
            elif campo == 'JWT_EXPIRE_MINUTES':
                mensagem = 'informe um número inteiro maior que zero.'
            else:
                mensagem = 'confira o formato da configuração.'
            print(f'- {campo}: {mensagem}')
        return
    print('Dados do operador inválidos:')
    for item in mensagens_por_campo(error.errors()):
        print('- ' + item['mensagem'])


def main():
    try:
        # Mantém a mesma conexão física até RELEASE_LOCK, inclusive após commit.
        with get_engine().connect() as connection, Session(connection) as session:
            # Lock nomeado cobre também a tabela vazia e execuções concorrentes do script.
            lock = session.exec(
                text("SELECT GET_LOCK('mationamento_primeiro_usuario', 5)")
            ).scalar()
            if lock != 1:
                print('Outro cadastro inicial está em execução. Tente novamente.')
                return 1
            try:
                if session.exec(select(Usuario.id).limit(1)).first() is not None:
                    print(
                        'Já existe usuário. Use um operador autenticado para novos cadastros.'
                    )
                    return 1
                nome = input('Nome: ')
                login = input('Login: ')
                senha = getpass('Senha (mínimo 8 caracteres): ')
                if senha != getpass('Confirme a senha: '):
                    print('As senhas não coincidem.')
                    return 1
                dados = UsuarioCriar(nome=nome, login=login, senha=senha)
                session.add(
                    Usuario(
                        nome=dados.nome,
                        login=dados.login,
                        senha_hash=hash_senha(dados.senha),
                        **criacao(None)
                    )
                )
                session.commit()
                print('Primeiro usuário criado.')
                return 0
            finally:
                session.rollback()
                session.exec(
                    text("SELECT RELEASE_LOCK('mationamento_primeiro_usuario')")
                )
    except ValidationError as error:
        mostrar_erros_validacao(error)
        return 1
    except SQLAlchemyError:
        print('Não foi possível cadastrar. Confira a conexão e a importação do SQL.')
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nCadastro cancelado.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
