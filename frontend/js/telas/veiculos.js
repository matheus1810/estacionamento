// Consulta os dados e monta a tela de veiculos.

import { api, all } from '../api.js';
import { state } from '../estado.js';
import {
  action,
  heading,
  table,
  pagination,
  rowAction,
  toolbar,
  selectFilter,
  queryParams,
} from '../ui/componentes.js';
import { esc } from '../utils/dom.js';

async function vehicles() {
  const clientes = await all('/clientes');
  state.cache.clientes = clientes;
  let rows;
  if (state.query) {
    try {
      rows = [await api('/veiculos/placa/' + encodeURIComponent(state.query))];
    } catch (e) {
      if (e.message === 'Veículo não encontrado.') rows = [];
      else throw e;
    }
  } else
    rows = await api('/veiculos?' + queryParams(state.filter ? { cliente_id: state.filter } : {}));
  state.cache.rows = rows;
  return (
    heading(
      'CADASTROS',
      'Veículos',
      'Cada placa conectada ao seu cliente.',
      action('Novo veículo', 'new-vehicle', 'plus'),
    ) +
    /* HTML */ `<section class="panel">
      ${toolbar(
        'Buscar pela placa completa',
        selectFilter(
          [['', 'Todos os clientes'], ...clientes.map((c) => [String(c.id), c.nome])],
          'Filtrar por cliente',
          true,
        ),
      )}${table(
        ['Placa', 'Modelo', 'Cor', 'Cliente', ''],
        rows.map(
          (v) =>
            /* HTML */ `<tr>
              <td><span class="plate">${esc(v.placa)}</span></td>
              <td>${esc(v.modelo)}</td>
              <td>${esc(v.cor)}</td>
              <td>${esc(clientes.find((c) => c.id === v.cliente_id)?.nome || v.cliente_id)}</td>
              <td>
                <div class="table-actions">
                  ${rowAction('Histórico', 'vehicle-history', v.id)}
                  ${rowAction('Editar', 'edit-vehicle', v.id)}
                </div>
              </td>
            </tr>`,
        ),
      )}${!state.query ? pagination(rows.length) : ''}
    </section>`
  );
}

export { vehicles };
