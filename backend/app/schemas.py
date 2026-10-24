import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Login = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Telefone = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Modelo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Cor = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
Numero = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)]
Senha = Annotated[str, StringConstraints(min_length=8, max_length=128)]
Dinheiro = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Id = Annotated[int, Field(gt=0)]
FormaPagamento = Literal['pix', 'dinheiro', 'cartao']


def normalizar_placa(value: str):
    value = re.sub(r'[\s-]', '', value).upper()
    if not re.fullmatch(r'[A-Z]{3}(?:[0-9]{4}|[0-9][A-Z][0-9]{2})', value):
        raise ValueError('Placa brasileira inválida.')
    return value


class Entrada(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Edicao(Entrada):
    @model_validator(mode='before')
    @classmethod
    def sem_nulos(cls, value):
        if isinstance(value, dict) and any(v is None for v in value.values()):
            raise ValueError('Campos de edição não podem ser nulos.')
        return value


class Saida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuditoriaSaida(Saida):
    id: int
    criado_em: datetime
    criado_por: int | None
    atualizado_em: datetime | None
    atualizado_por: int | None


class LoginEntrada(Entrada):
    login: Login
    senha: str = Field(min_length=1, max_length=128)


class TokenSaida(Saida):
    access_token: str
    token_type: str = 'bearer'


class UsuarioCriar(Entrada):
    nome: Nome
    login: Login
    senha: Senha

    @field_validator('senha')
    @classmethod
    def senha_valida(cls, value):
        if not value.strip():
            raise ValueError('Senha não pode conter somente espaços.')
        return value


class UsuarioEditar(Edicao):
    nome: Nome | None = None
    login: Login | None = None
    senha: Senha | None = None
    ativo: bool | None = None

    @field_validator('senha')
    @classmethod
    def senha_valida(cls, value):
        return UsuarioCriar.senha_valida(value)


class UsuarioSaida(AuditoriaSaida):
    nome: str
    login: str
    ativo: bool


class ClienteCriar(Entrada):
    nome: Nome
    telefone: Telefone


class ClienteEditar(Edicao):
    nome: Nome | None = None
    telefone: Telefone | None = None
    ativo: bool | None = None


class ClienteSaida(AuditoriaSaida):
    nome: str
    telefone: str
    ativo: bool


class VeiculoCriar(Entrada):
    cliente_id: Id
    placa: str
    modelo: Modelo
    cor: Cor

    _placa = field_validator('placa')(normalizar_placa)


class VeiculoEditar(Edicao):
    cliente_id: Id | None = None
    placa: str | None = None
    modelo: Modelo | None = None
    cor: Cor | None = None

    _placa = field_validator('placa')(normalizar_placa)


class VeiculoSaida(AuditoriaSaida):
    cliente_id: int
    placa: str
    modelo: str
    cor: str


class VagaCriar(Entrada):
    numero: Numero


class VagaEditar(Edicao):
    numero: Numero | None = None
    ativa: bool | None = None


class VagaSaida(AuditoriaSaida):
    numero: str
    ativa: bool
    disponivel: bool
    motivo: str


class TarifaEntrada(Entrada):
    valor_hora: Dinheiro
    valor_mensal_vaga: Dinheiro


class TarifaSaida(AuditoriaSaida):
    valor_hora: Decimal
    valor_mensal_vaga: Decimal


class ContratacaoCriar(Entrada):
    cliente_id: Id
    vaga_id: Id
    data_inicio: date
    data_fim: date | None = None

    @model_validator(mode='after')
    def periodo_valido(self):
        if self.data_fim is not None and self.data_fim < self.data_inicio:
            raise ValueError('Data final deve ser igual ou posterior ao início.')
        return self


class ContratacaoSaida(AuditoriaSaida):
    cliente_id: int
    vaga_id: int
    data_inicio: date
    data_fim: date | None
    dia_vencimento: int


class PermanenciaCriar(Entrada):
    veiculo_id: Id
    vaga_id: Id


class PermanenciaCadastroCriar(Entrada):
    vaga_id: Id
    placa: str
    modelo: Modelo
    cor: Cor
    cliente_id: Id | None = None
    cliente: ClienteCriar | None = None

    _placa = field_validator('placa')(normalizar_placa)

    @model_validator(mode='after')
    def responsavel_unico(self):
        if (self.cliente_id is None) == (self.cliente is None):
            raise ValueError('Informe um cliente existente ou os dados de um novo cliente.')
        return self


class PermanenciaSaida(AuditoriaSaida):
    cliente_id: int
    veiculo_id: int
    vaga_id: int
    entrada: datetime
    saida: datetime | None
    valor_hora_aplicado: Decimal
    usuario_entrada_id: int
    usuario_saida_id: int | None


class PagamentoEntrada(Entrada):
    forma_pagamento: FormaPagamento


class CobrancaSaida(AuditoriaSaida):
    permanencia_id: int | None
    contratacao_mensal_id: int | None
    competencia: date | None
    vencimento: date
    valor: Decimal
    pago_em: datetime | None
    forma_pagamento: FormaPagamento | None
    usuario_recebimento_id: int | None


class PreviaSaida(Saida):
    permanencia_id: int
    calculado_em: datetime
    blocos: int
    valor: Decimal


class AcessoEntrada(Entrada):
    placa: str
    _placa = field_validator('placa')(normalizar_placa)


class AcessoSaida(Saida):
    liberado: bool
    motivo: str
    cliente_id: int | None = None
    vagas: list[int] = Field(default_factory=list)


class GeracaoSaida(Saida):
    geradas: int
