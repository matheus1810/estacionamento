"""Regressão: DATETIME local não pode virar UTCDateTime no SQLModel."""
from datetime import datetime

import pytest
from sqlalchemy import DateTime
from sqlalchemy.dialects.mysql import pymysql

from app.models import Cliente, Cobranca, Contratacao, Permanencia, Tarifa, Usuario, Vaga, Veiculo


@pytest.mark.parametrize('model', [Usuario, Cliente, Veiculo, Vaga, Tarifa, Contratacao, Permanencia, Cobranca])
def test_datetime_preserva_relogio_local_sem_fuso(model):
    dialect = pymysql.dialect()
    local = datetime(2026, 10, 23, 9, 30)
    for column in model.__table__.columns:
        if column.name not in {'criado_em', 'atualizado_em', 'entrada', 'saida', 'pago_em'}:
            continue
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is False
        impl = column.type.dialect_impl(dialect)
        bind = impl.bind_processor(dialect)
        result = impl.result_processor(dialect, None)
        assert (bind(local) if bind else local) == local
        assert (result(local) if result else local) == local
