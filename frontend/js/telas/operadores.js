// Consulta os dados e monta a tela de operadores.

import { api } from '../api.js';
import { state } from '../estado.js';
import {
  action,
  heading,
  badge,
  table,
  pagination,
  rowAction,
  queryParams,
} from '../ui/componentes.js';
import { esc } from '../utils/dom.js';
import { localDate } from '../utils/formatacao.js';

async function operators() {
  const rows = await api('/usuarios?' + queryParams());
  state.cache.rows = rows;
  return (
    heading(
      'ACESSO AO SISTEMA',
      'Operadores',
      'Todos os operadores possuem as mesmas permissões.',
      action('Novo operador', 'new-user', 'plus'),
    ) +
    /* HTML */ `<section class="panel">
      ${table(
        ['Nome', 'Login', 'Situação', 'Cadastro', ''],
        rows.map(
          (u) =>
            /* HTML */ `<tr>
              <td>
                <strong>${esc(u.nome)}</strong>${u.id === state.user.id
                  ? ' <span class="muted">(você)</span>'
                  : ''}
              </td>
              <td>${esc(u.login)}</td>
              <td>${badge(u.ativo ? 'Ativo' : 'Inativo', u.ativo ? 'green' : 'gray')}</td>
              <td>${localDate(u.criado_em)}</td>
              <td>${rowAction('Editar', 'edit-user', u.id)}</td>
            </tr>`,
        ),
      )}${pagination(rows.length)}
    </section>`
  );
}

export { operators };
