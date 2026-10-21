from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

from .config import get_settings
from .database import SessionDep
from .models import Usuario
from .schemas import LoginEntrada, TokenSaida, UsuarioSaida

router = APIRouter(prefix='/auth', tags=['Autenticação'])
bearer = HTTPBearer(auto_error=False)
hasher = PasswordHasher()
# Verificação fictícia reduz a diferença de tempo para login inexistente.
dummy_hash = hasher.hash('verificacao-interna-sem-credencial')


def hash_senha(senha):
    return hasher.hash(senha)


def verificar_senha(senha, senha_hash):
    try:
        return hasher.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return False


def nao_autorizado():
    return HTTPException(401, 'Credenciais inválidas ou usuário inativo.',
                         headers={'WWW-Authenticate': 'Bearer'})


def usuario_atual(session: SessionDep,
                  credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credenciais is None:
        raise nao_autorizado()
    try:
        payload = jwt.decode(credenciais.credentials,
                             get_settings().jwt_secret.get_secret_value(),
                             algorithms=['HS256'], options={'require': ['exp', 'sub', 'iat']})
        usuario_id = int(payload['sub'])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise nao_autorizado() from None
    usuario = session.get(Usuario, usuario_id)
    if not usuario or not usuario.ativo:
        raise nao_autorizado()
    return usuario


UsuarioDep = Annotated[Usuario, Depends(usuario_atual)]


@router.post('/login', response_model=TokenSaida)
def login(dados: LoginEntrada, session: SessionDep):
    usuario = session.exec(select(Usuario).where(Usuario.login == dados.login)).first()
    valido = verificar_senha(dados.senha, usuario.senha_hash if usuario else dummy_hash)
    if not usuario or not valido or not usuario.ativo:
        raise nao_autorizado()
    settings = get_settings()
    agora = datetime.now(timezone.utc)
    token = jwt.encode({'sub': str(usuario.id), 'iat': agora,
                        'exp': agora + timedelta(minutes=settings.jwt_expire_minutes)},
                       settings.jwt_secret.get_secret_value(), algorithm='HS256')
    return TokenSaida(access_token=token)


@router.get('/me', response_model=UsuarioSaida)
def me(usuario: UsuarioDep):
    return UsuarioSaida.model_validate(usuario)
