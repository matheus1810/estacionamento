// Cadastro e edição de clientes.

import { post, patch } from '../api.js';
import { state } from '../estado.js';
import { complete } from './conclusao.js';
import { input, activeSelect } from '../ui/formularios.js';
import { openModal } from '../ui/modal.js';
import { normalizePhone } from '../utils/validacao-campos.js';

async function clientModal(id) {
  const c = id ? state.cache.rows?.find((v) => v.id === id) : null;
  openModal(
    c ? 'Editar cliente' : 'Novo cliente',
    /* HTML */ `<div class="form-stack">
      ${input('nome', 'Nome completo', 'text', c?.nome || '', {
        required: true,
        maxlength: 120,
        'data-validation': 'nome-cliente',
      })}${input('telefone', 'Telefone', 'tel', c?.telefone || '', {
        required: true,
        maxlength: 25,
      })}${c ? activeSelect('Situação', c.ativo) : ''}
    </div>`,
    async (values) => {
      const body = {
        nome: values.nome.trim(),
        telefone: normalizePhone(values.telefone),
        ...(c ? { ativo: values.ativo === 'true' } : {}),
      };
      if (c) await patch('/clientes/' + c.id, body);
      else await post('/clientes', body);
      await complete(
        c ? 'Cliente atualizado.' : 'Cliente cadastrado. Cadastre o veículo na tela Veículos.',
      );
    },
  );
}

export { clientModal };
