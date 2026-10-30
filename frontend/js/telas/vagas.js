// Consulta os dados e monta a tela de vagas.

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

async function spaces() {
  const rows = await api('/vagas?' + queryParams());
  state.cache.rows = rows;
  return (
    heading(
      'ORGANIZAÇÃO DO PÁTIO',
      'Vagas',
      'Disponibilidade calculada a partir das permanências e reservas.',
      action('Nova vaga', 'new-space', 'plus'),
    ) +
    /* HTML */ `<section class="panel">
      <div class="panel-header">
        <h3>Vagas do estacionamento</h3>
        <span class="muted" style="font-size:10px">Situação atual</span>
      </div>
      ${table(
        ['Vaga', 'Cadastro', 'Disponibilidade', 'Ações'],
        rows.map(
          (v) =>
            /* HTML */ `<tr>
              <td><strong>${esc(v.numero)}</strong></td>
              <td>${badge(v.ativa ? 'Ativa' : 'Inativa', v.ativa ? 'green' : 'gray')}</td>
              <td>
                ${badge(
                  v.disponivel ? 'Disponível' : v.motivo.replace('Vaga ', '').replace('.', ''),
                  v.disponivel ? 'green' : !v.ativa ? 'gray' : 'amber',
                )}
              </td>
              <td>${rowAction('Editar', 'edit-space', v.id)}</td>
            </tr>`,
        ),
      )}${pagination(rows.length)}
    </section>`
  );
}

export { spaces };
