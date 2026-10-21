"""Mapeamento do mationamento.sql. O DDL original é responsável pelas constraints.

Não há criação automática de tabelas, relacionamentos com carregamento implícito
ou exclusões em cascata. Campos e tipos seguem as oito tabelas existentes.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, Enum, Numeric, UniqueConstraint
from sqlalchemy.dialects.mysql import TINYINT
from sqlmodel import Field, SQLModel


class Auditoria(SQLModel):
    criado_em: datetime
    criado_por: int = Field(foreign_key='usuarios.id')
    atualizado_em: datetime | None = None
    atualizado_por: int | None = Field(default=None, foreign_key='usuarios.id')


class Usuario(Auditoria, table=True):
    __tablename__ = 'usuarios'
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=120)
    login: str = Field(max_length=80, unique=True)
    senha_hash: str = Field(max_length=255)
    ativo: bool = True
    criado_por: int | None = Field(default=None, foreign_key='usuarios.id')


class Cliente(Auditoria, table=True):
    __tablename__ = 'clientes'
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=120)
    telefone: str = Field(max_length=20)
    ativo: bool = True


class Veiculo(Auditoria, table=True):
    __tablename__ = 'veiculos'
    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key='clientes.id')
    placa: str = Field(max_length=7, unique=True)
    modelo: str = Field(max_length=80)
    cor: str = Field(max_length=30)


class Vaga(Auditoria, table=True):
    __tablename__ = 'vagas'
    id: int | None = Field(default=None, primary_key=True)
    numero: str = Field(max_length=10, unique=True)
    ativa: bool = True


class Tarifa(Auditoria, table=True):
    __tablename__ = 'tarifas'
    id: int = Field(default=1, primary_key=True, sa_column_kwargs={'autoincrement': False})
    valor_hora: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    valor_mensal_vaga: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))


class Contratacao(Auditoria, table=True):
    __tablename__ = 'contratacoes_mensais'
    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key='clientes.id')
    vaga_id: int = Field(foreign_key='vagas.id')
    data_inicio: date
    data_fim: date | None = None
    dia_vencimento: int = Field(sa_column=Column(TINYINT, nullable=False))


class Permanencia(Auditoria, table=True):
    __tablename__ = 'permanencias'
    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key='clientes.id')
    veiculo_id: int = Field(foreign_key='veiculos.id')
    vaga_id: int = Field(foreign_key='vagas.id')
    entrada: datetime
    saida: datetime | None = None
    valor_hora_aplicado: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    usuario_entrada_id: int = Field(foreign_key='usuarios.id')
    usuario_saida_id: int | None = Field(default=None, foreign_key='usuarios.id')


class Cobranca(Auditoria, table=True):
    __tablename__ = 'cobrancas'
    __table_args__ = (UniqueConstraint('contratacao_mensal_id', 'competencia',
                                      name='uq_cobrancas_contratacao_competencia'),)
    id: int | None = Field(default=None, primary_key=True)
    permanencia_id: int | None = Field(default=None, foreign_key='permanencias.id', unique=True)
    contratacao_mensal_id: int | None = Field(default=None, foreign_key='contratacoes_mensais.id')
    competencia: date | None = None
    vencimento: date
    valor: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    pago_em: datetime | None = None
    forma_pagamento: str | None = Field(default=None, sa_column=Column(
        Enum('pix', 'dinheiro', 'cartao'), nullable=True))
    usuario_recebimento_id: int | None = Field(default=None, foreign_key='usuarios.id')
