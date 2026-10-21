from fastapi import APIRouter, HTTPException

from ..auth import UsuarioDep
from ..database import SessionDep, obter, salvar
from ..models import Tarifa
from ..regras_estacionamento import auditar, criacao
from ..schemas import TarifaEntrada, TarifaSaida

router = APIRouter(prefix='/tarifas', tags=['Tarifas'])


@router.get('', response_model=TarifaSaida)
def buscar(session: SessionDep, usuario: UsuarioDep):
    return TarifaSaida.model_validate(obter(session, Tarifa, 1))


@router.post('', response_model=TarifaSaida, status_code=201)
def criar(dados: TarifaEntrada, session: SessionDep, usuario: UsuarioDep):
    if session.get(Tarifa, 1):
        raise HTTPException(409, 'Tarifas já cadastradas. Use PUT para atualizar.')
    obj = Tarifa(id=1, **dados.model_dump(), **criacao(usuario.id))
    session.add(obj)
    salvar(session)
    return TarifaSaida.model_validate(obj)


@router.put('', response_model=TarifaSaida)
def editar(dados: TarifaEntrada, session: SessionDep, usuario: UsuarioDep):
    obj = obter(session, Tarifa, 1, True)
    obj.valor_hora = dados.valor_hora
    obj.valor_mensal_vaga = dados.valor_mensal_vaga
    auditar(obj, usuario.id)
    salvar(session)
    return TarifaSaida.model_validate(obj)
