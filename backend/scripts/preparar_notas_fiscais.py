"""Cria somente a tabela de pedidos de nota: python -m scripts.preparar_notas_fiscais."""

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine


def main():
    sql = (
        Path(__file__).resolve().parents[1]
        / 'migrations'
        / '001_solicitacoes_nota_fiscal.sql'
    ).read_text(encoding='utf-8')
    try:
        with get_engine().begin() as connection:
            connection.execute(text(sql))
    except SQLAlchemyError:
        print(
            'Não foi possível preparar a tabela. Confira a conexão e a permissão CREATE no banco configurado.'
        )
        return 1
    print(
        'Tabela de solicitações de nota fiscal preparada. Os dados existentes foram preservados.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
