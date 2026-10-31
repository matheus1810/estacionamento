"""Mensagens de validação por campo, sem reproduzir valores recebidos na requisição."""

LABELS = {
    'nome': 'Nome',
    'telefone': 'Telefone',
    'placa': 'Placa',
    'modelo': 'Modelo',
    'cor': 'Cor',
    'cliente_id': 'Cliente responsável',
    'veiculo_id': 'Veículo',
    'vaga_id': 'Vaga',
    'documento': 'CPF/CNPJ',
    'email': 'E-mail',
    'endereco': 'Endereço',
    'forma_pagamento': 'Forma de pagamento',
    'login': 'Login',
    'senha': 'Senha',
    'numero': 'Número da vaga',
    'data_inicio': 'Data de início',
    'data_fim': 'Data final',
    'valor_hora': 'Valor por hora',
    'valor_mensal_vaga': 'Mensalidade por vaga',
    'ativo': 'Situação',
    'ativa': 'Situação',
}
MESSAGES = {
    'nome_cliente_invalido': 'use apenas letras, espaços, apóstrofos e hífens. Números não são permitidos.',
    'nome_invalido': 'informe um nome com letras; números ou símbolos sozinhos não são aceitos.',
    'telefone_invalido': 'informe um fixo ou celular com DDD. Ex.: (11) 91234-5678.',
    'modelo_invalido': 'informe o modelo do veículo. Ex.: Fiat Argo ou 208.',
    'cor_invalida': 'informe a cor por extenso, sem números. Ex.: Branco ou Prata/Preto.',
    'missing': 'preencha este campo.',
    'int_parsing': 'selecione uma opção válida.',
    'int_type': 'selecione uma opção válida.',
    'greater_than': 'informe um valor maior que zero.',
    'string_type': 'informe um texto válido.',
    'literal_error': 'selecione uma das opções disponíveis.',
    'extra_forbidden': 'campo não permitido nesta operação.',
}


def mensagens_por_campo(errors):
    result = []
    for error in errors:
        location = [
            str(part) for part in error['loc'] if part not in ('body', 'query', 'path')
        ]
        name = location[-1] if location else ''
        # Campos desconhecidos e valores de exceções não são refletidos na resposta.
        field = '.'.join(location) if name in LABELS else 'formulario'
        label = LABELS.get(name, 'Formulário')
        kind = error['type']
        context = error.get('ctx', {})
        if kind == 'string_too_short':
            message = (
                'preencha este campo.'
                if context['min_length'] == 1
                else f"informe pelo menos {context['min_length']} caracteres."
            )
        elif kind == 'string_too_long':
            message = f"use no máximo {context['max_length']} caracteres."
        elif kind == 'value_error' and name == 'placa':
            message = (
                'use ABC1234 (placa antiga) ou ABC1D23 (Mercosul), com 7 caracteres.'
            )
        elif kind == 'value_error' and name == 'documento':
            message = 'informe CPF com 11 dígitos ou CNPJ com 14 caracteres.'
        elif kind == 'value_error' and name == 'email':
            message = 'informe um e-mail válido ou deixe o campo vazio.'
        elif kind == 'greater_than' and name.endswith('_id'):
            message = 'selecione uma opção válida.'
        else:
            message = MESSAGES.get(kind, 'confira o valor informado neste campo.')
        result.append({'campo': field, 'mensagem': f'{label}: {message}'})
    return result
