// Cadastro e edição de operadores.

import { post, patch } from '../api.js';
import { logout } from '../autenticacao.js';
import { state } from '../estado.js';
import { complete } from './conclusao.js';
import { input, activeSelect } from '../ui/formularios.js';
import { openModal } from '../ui/modal.js';
import { toast } from '../ui/notificacoes.js';

function userModal(id) {
  const u = id ? state.cache.rows?.find((v) => v.id === id) : null;
  openModal(
    u ? 'Editar operador' : 'Novo operador',
    /* HTML */ `<div class="form-stack">
      ${input('nome', 'Nome', 'text', u?.nome || '', { required: true, maxlength: 120 })}${input(
        'login',
        'Login',
        'text',
        u?.login || '',
        { required: true, maxlength: 80, autocomplete: 'off' },
      )}${input('senha', u ? 'Nova senha (opcional)' : 'Senha', 'password', '', {
        ...(u ? {} : { required: true }),
        minlength: 8,
        maxlength: 128,
        autocomplete: 'new-password',
      })}${u ? activeSelect('Situação', u.ativo) : ''}
    </div>`,
    async (values) => {
      const body = { ...values, ...(u ? { ativo: values.ativo === 'true' } : {}) };
      if (u && !body.senha) delete body.senha;
      if (u) await patch('/usuarios/' + u.id, body);
      else await post('/usuarios', body);
      if (u?.id === state.user.id && body.ativo === false) {
        logout();
        toast('Sua conta foi desativada.');
        return;
      }
      await complete(u ? 'Operador atualizado.' : 'Operador cadastrado.');
    },
  );
}

export { userModal };
