"""Recuperação local pelo dono da conta, com acesso autorizado ao banco do .env.

Executar em backend: python -m scripts.redefinir_senha --login matheus
"""
import argparse
import warnings
from getpass import GetPassWarning, getpass

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.auth import hash_senha
from app.database import get_engine
from app.models import Usuario
from app.regras_estacionamento import auditar
from app.schemas import UsuarioEditar


def main(argv=None):
    parser = argparse.ArgumentParser(description='Definir uma nova senha de usuário pelo terminal local.')
    parser.add_argument('--login', required=True, help='Login da conta a recuperar.')
    args = parser.parse_args(argv)
    try:
        # Recusa o fallback que exibiria a senha em terminais sem entrada oculta.
        with warnings.catch_warnings():
            warnings.simplefilter('error', GetPassWarning)
            senha = getpass('Nova senha (8 a 128 caracteres): ')
            confirmacao = getpass('Confirme a nova senha: ')
        if senha != confirmacao:
            print('As senhas não coincidem. Nada foi alterado.')
            return 1
        dados = UsuarioEditar(senha=senha)
        nova_hash = hash_senha(dados.senha)
        with Session(get_engine()) as session:
            usuario = session.exec(select(Usuario).where(Usuario.login == args.login.strip())
                                   .with_for_update()).first()
            if usuario is None:
                print('Usuário não encontrado. Nada foi alterado.')
                return 1
            if not usuario.ativo:
                print('Usuário inativo. Solicite a reativação a outro operador.')
                return 1
            usuario.senha_hash = nova_hash
            # Recuperação da própria conta solicitada pelo titular no terminal.
            auditar(usuario, usuario.id)
            session.commit()
        print('Senha redefinida. Entre no sistema com a nova senha.')
        return 0
    except ValidationError:
        print('Dados inválidos. Use uma senha de 8 a 128 caracteres, não composta apenas de espaços, e confira o .env.')
        return 1
    except SQLAlchemyError:
        print('Não foi possível redefinir. Confira se o MySQL do XAMPP está iniciado e o .env está correto.')
        return 1
    except GetPassWarning:
        print('Este terminal não permite ocultar a senha. Execute em uma janela interativa do Git Bash ou PowerShell.')
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nRedefinição cancelada.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
