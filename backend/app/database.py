from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, create_engine, select

from .config import get_settings


@lru_cache
def get_engine():
    # READ COMMITTED evita snapshots antigos depois de aguardar um bloqueio.
    # Todas as datas gravadas são fornecidas pela aplicação no fuso configurado.
    return create_engine(get_settings().database_url, pool_pre_ping=True,
                         isolation_level='READ COMMITTED',
                         connect_args={'connect_timeout': 5})


def get_session():
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.rollback()  # Encerra também transações de consultas GET.


SessionDep = Annotated[Session, Depends(get_session)]


def salvar(session):
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, 'Operação em conflito com os dados cadastrados.') from None
    except OperationalError as exc:
        session.rollback()
        if exc.orig.args[0] in (1205, 1213):
            raise HTTPException(409, 'Operação concorrente. Tente novamente.') from None
        raise


def obter(session, model, registro_id, bloquear=False):
    stmt = select(model).where(model.id == registro_id)
    if bloquear:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    obj = session.exec(stmt).first()
    if obj is None:
        raise HTTPException(404, 'Registro não encontrado.')
    return obj
