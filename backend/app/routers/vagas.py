from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ..auth import UsuarioDep
from ..config import agora_local
from ..database import SessionDep, obter, salvar
from ..models import Vaga
from ..regras_estacionamento import auditar, criacao, disponibilidade, ocupada, reservas
from ..schemas import VagaCriar, VagaEditar, VagaSaida

router = APIRouter(prefix='/vagas', tags=['Vagas'])


def resposta(session, vaga):
    disponivel, motivo = disponibilidade(session, vaga, agora_local().date())
    return VagaSaida(**vaga.model_dump(), disponivel=disponivel, motivo=motivo)


@router.post('', response_model=VagaSaida, status_code=201)
def criar(dados: VagaCriar, session: SessionDep, usuario: UsuarioDep):
    obj = Vaga(**dados.model_dump(), **criacao(usuario.id))
    session.add(obj)
    salvar(session)
    return resposta(session, obj)


@router.get('', response_model=list[VagaSaida])
def listar(session: SessionDep, usuario: UsuarioDep, offset: int = Query(0, ge=0),
           limite: int = Query(50, ge=1, le=100)):
    return [resposta(session, v) for v in session.exec(
        select(Vaga).order_by(Vaga.id).offset(offset).limit(limite)).all()]


@router.patch('/{vaga_id}', response_model=VagaSaida)
def editar(vaga_id: int, dados: VagaEditar, session: SessionDep, usuario: UsuarioDep):
    obj = obter(session, Vaga, vaga_id, True)
    if dados.ativa is False and (ocupada(session, obj.id) or
                                 reservas(session, obj.id, agora_local().date())):
        raise HTTPException(409, 'Vaga com permanência aberta ou reserva atual/futura.')
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(obj, campo, valor)
    auditar(obj, usuario.id)
    salvar(session)
    return resposta(session, obj)
