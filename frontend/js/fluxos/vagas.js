// Cadastro e edição de vagas.

import { post, patch } from '../api.js';
import { state } from '../estado.js';
import { complete } from './conclusao.js';
import { input, activeSelect } from '../ui/formularios.js';
import { openModal } from '../ui/modal.js';

function spaceModal(id) {
  const c = id ? state.cache.rows?.find((v) => v.id === id) : null;
  openModal(
    c ? 'Editar vaga' : 'Nova vaga',
    /* HTML */ `<div class="form-stack">
      ${input('numero', 'Número ou código da vaga', 'text', c?.numero || '', {
        required: true,
        maxlength: 10,
        placeholder: 'A-01',
      })}${c ? activeSelect('Situação', c.ativa, 'ativa') : ''}
    </div>`,
    async (values) => {
      const body = {
        numero: values.numero.trim(),
        ...(c ? { ativa: values.ativa === 'true' } : {}),
      };
      if (c) await patch('/vagas/' + c.id, body);
      else await post('/vagas', body);
      await complete(c ? 'Vaga atualizada.' : 'Vaga cadastrada.');
    },
  );
}

export { spaceModal };
