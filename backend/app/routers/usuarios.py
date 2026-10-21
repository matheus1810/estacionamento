from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ..auth import UsuarioDep, hash_senha
from ..database import SessionDep, obter, salvar
from ..models import Usuario
from ..regras_estacionamento import auditar, criacao
from ..schemas import UsuarioCriar, UsuarioEditar, UsuarioSaida

router = APIRouter(prefix='/usuarios', tags=['Usuários'])


@router.post('', response_model=UsuarioSaida, status_code=201)
def criar(dados: UsuarioCriar, session: SessionDep, usuario: UsuarioDep):
    obj = Usuario(nome=dados.nome, login=dados.login, senha_hash=hash_senha(dados.senha),
                  **criacao(usuario.id))
    session.add(obj)
    salvar(session)
    return UsuarioSaida.model_validate(obj)


@router.get('', response_model=list[UsuarioSaida])
def listar(session: SessionDep, usuario: UsuarioDep, offset: int = Query(0, ge=0),
           limite: int = Query(50, ge=1, le=100)):
    return [UsuarioSaida.model_validate(u) for u in session.exec(
        select(Usuario).order_by(Usuario.id).offset(offset).limit(limite)).all()]


@router.patch('/{usuario_id}', response_model=UsuarioSaida)
def editar(usuario_id: int, dados: UsuarioEditar, session: SessionDep, usuario: UsuarioDep):
    # Bloquear todos na mesma ordem serializa desativações simultâneas.
    usuarios = session.exec(select(Usuario).order_by(Usuario.id).with_for_update()
                           .execution_options(populate_existing=True)).all()
    obj = next((u for u in usuarios if u.id == usuario_id), None)
    if obj is None:
        raise HTTPException(404, 'Usuário não encontrado.')
    valores = dados.model_dump(exclude_unset=True)
    if valores.get('ativo') is False and obj.ativo and sum(u.ativo for u in usuarios) <= 1:
        raise HTTPException(409, 'Não é possível desativar o último usuário ativo.')
    if 'senha' in valores:
        valores['senha_hash'] = hash_senha(valores.pop('senha'))
    for campo, valor in valores.items():
        setattr(obj, campo, valor)
    auditar(obj, usuario.id)
    salvar(session)
    return UsuarioSaida.model_validate(obj)
