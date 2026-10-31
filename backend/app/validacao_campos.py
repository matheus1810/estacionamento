"""Regras dos campos de cadastro, sem consultas ou alterações no banco."""

import re
from unicodedata import normalize

from pydantic_core import PydanticCustomError


def validar_nome(value: str):
    if not any(char.isalpha() for char in value) or re.search(
        r'[\x00-\x1f\x7f]', value
    ):
        raise PydanticCustomError('nome_invalido', 'Informe um nome com letras.')
    return value


def validar_nome_cliente(value: str):
    value = normalize('NFC', value)
    if not any(char.isalpha() for char in value) or not all(
        char.isalpha() or char in " '-’" for char in value
    ):
        raise PydanticCustomError(
            'nome_cliente_invalido',
            'Use apenas letras, espaços, apóstrofos e hífens no nome do cliente. Números não são permitidos.',
        )
    return value


def normalizar_telefone(value: str):
    message = 'Informe telefone fixo ou celular com DDD. Exemplo: (11) 91234-5678.'
    if not re.fullmatch(r'\+?[0-9() .\-]+', value):
        raise PydanticCustomError('telefone_invalido', message)
    digits = re.sub(r'\D', '', value)
    if value.startswith('+') and not value.startswith('+55'):
        raise PydanticCustomError('telefone_invalido', message)
    if len(digits) in (12, 13) and digits.startswith('55'):
        digits = digits[2:]
    if (
        not re.fullmatch(r'[1-9]{2}(?:[2-5][0-9]{7}|9[0-9]{8})', digits)
        or len(set(digits)) == 1
    ):
        raise PydanticCustomError('telefone_invalido', message)
    return digits


def validar_modelo(value: str):
    if not any(char.isalnum() for char in value) or re.search(
        r'[\x00-\x1f\x7f]', value
    ):
        raise PydanticCustomError(
            'modelo_invalido', 'Informe o modelo do veículo. Exemplo: Fiat Argo ou 208.'
        )
    return value


def validar_cor(value: str):
    if not any(char.isalpha() for char in value) or not all(
        char.isalpha() or char in " -/'’" for char in value
    ):
        raise PydanticCustomError(
            'cor_invalida', 'Informe a cor por extenso. Exemplo: Branco ou Prata/Preto.'
        )
    return value
