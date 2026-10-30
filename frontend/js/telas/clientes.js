// Consulta os dados e monta a tela de clientes.

import { api } from '../api.js';
import { state } from '../estado.js';
import {
  action,
  heading,
  badge,
  table,
  pagination,
  rowAction,
  toolbar,
  selectFilter,
  queryParams,
} from '../ui/componentes.js';
import { esc } from '../utils/dom.js';
import { localDate } from '../utils/formatacao.js';

async function clients() {
  const params = {
    ...(state.query ? { nome: state.query } : {}),
    ...(state.filter ? { ativo: state.filter } : {}),
  };
  const rows = await api('/clientes?' + queryParams(params));
  state.cache.rows = rows;
  return (
    heading(
      'CADASTROS',
      'Clientes',
      'Pessoas, contatos e um histórico preservado.',
      action('Novo cliente', 'new-client', 'plus'),
    ) +
    /* HTML */ `<section class="panel">
      ${toolbar(
        'Buscar cliente por nome',
        selectFilter(
          [
            ['', 'Todos os clientes'],
            ['true', 'Ativos'],
            ['false', 'Inativos'],
          ],
          'Situação do cliente',
        ),
      )}${table(
        ['Nome', 'Telefone', 'Situação', 'Cadastro', 'Ações'],
        rows.map(
          (c) =>
            /* HTML */ `<tr>
              <td><strong>${esc(c.nome)}</strong></td>
              <td>${esc(c.telefone)}</td>
              <td>${badge(c.ativo ? 'Ativo' : 'Inativo', c.ativo ? 'green' : 'gray')}</td>
              <td>${localDate(c.criado_em)}</td>
              <td>
                <div class="table-actions">
                  ${rowAction('Editar', 'edit-client', c.id)}${rowAction(
                    'Veículos',
                    'client-vehicles',
                    c.id,
                  )}
                </div>
              </td>
            </tr>`,
        ),
      )}${pagination(rows.length)}
    </section>`
  );
}

export { clients };
