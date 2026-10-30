"""Validação de dados opcionais para emissão posterior de nota fiscal."""

import pytest
from pydantic import ValidationError

from app.schemas import PagamentoEntrada, SolicitacaoNotaFiscalEntrada


@pytest.mark.parametrize(
    'documento,normalizado',
    [
        ('529.982.247-25', '52998224725'),
        ('00.000.000/0001-91', '00000000000191'),
        ('00.000.000/e08g-12', '00000000E08G12'),
    ],
)
def test_normaliza_documento_e_campos_opcionais(documento, normalizado):
    dados = SolicitacaoNotaFiscalEntrada(
        nome='  Cliente  ',
        documento=documento,
        email='  ',
        endereco='  Rua A, 10  ',
    )
    assert dados.nome == 'Cliente'
    assert dados.documento == normalizado
    assert dados.email is None
    assert dados.endereco == 'Rua A, 10'


@pytest.mark.parametrize(
    'dados',
    [
        {'nome': '', 'documento': '52998224725'},
        {'nome': 'Cliente', 'documento': '123'},
        {'nome': 'Cliente', 'documento': '1234567890A'},
        {'nome': 'Cliente', 'documento': '00000000E08GXX'},
        {'nome': 'Cliente', 'documento': '52998224725', 'email': 'invalido'},
        {'nome': 'Cliente', 'documento': '52998224725', 'email': 'a\nb@exemplo.com'},
        {'nome': 'Cliente', 'documento': '52998224725', 'endereco': 'a' * 251},
    ],
)
def test_rejeita_dados_fiscais_incompletos_ou_invalidos(dados):
    with pytest.raises(ValidationError):
        PagamentoEntrada(forma_pagamento='pix', nota_fiscal=dados)


def test_pagamento_sem_pedido_nao_exige_dados_fiscais():
    assert PagamentoEntrada(forma_pagamento='pix').nota_fiscal is None
    assert PagamentoEntrada(forma_pagamento='pix', nota_fiscal=None).nota_fiscal is None
