// Consulta os dados e monta a tela de mensalistas.

import { api, all } from '../api.js';
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
import { localDate, today } from '../utils/formatacao.js';

async function contracts() {
  const [rows, clientes, vagas] = await Promise.all([
    api('/contratacoes?' + queryParams()),
    all('/clientes'),
    all('/vagas'),
  ]);
  Object.assign(state.cache, { rows, clientes, vagas });
  return (
    heading(
      'RESERVAS EXCLUSIVAS',
      'Mensalistas',
      'Uma contratação por vaga. O cliente pode alternar seus veículos.',
      action('Consultar placa', 'access', 'search', true) +
        action('Nova contratação', 'new-contract', 'plus'),
    ) +
    /* HTML */ `<div class="notice">
        Mensalidade antecipada e integral por vaga. O atraso bloqueia o acesso e mantém a reserva. A
        presença dos veículos é controlada manualmente.
      </div>
      <section class="panel">
        ${table(
          ['Cliente', 'Vaga', 'Início', 'Fim da reserva', 'Situação', ''],
          rows.map((c) => {
            const encerrada = c.data_fim && c.data_fim < today();
            const futura = c.data_inicio > today();
            return /* HTML */ `<tr>
              <td>
                <strong
                  >${esc(clientes.find((v) => v.id === c.cliente_id)?.nome || c.cliente_id)}</strong
                >
              </td>
              <td>${esc(vagas.find((v) => v.id === c.vaga_id)?.numero || c.vaga_id)}</td>
              <td>${localDate(c.data_inicio)}</td>
              <td>${c.data_fim ? localDate(c.data_fim) : 'Sem encerramento'}</td>
              <td>
                ${badge(
                  encerrada
                    ? 'Encerrada'
                    : futura
                      ? 'Agendada'
                      : c.data_fim
                        ? 'Encerramento programado'
                        : 'Vigente',
                  encerrada ? 'gray' : futura ? 'amber' : 'green',
                )}
              </td>
              <td>
                ${!encerrada && !futura
                  ? rowAction('Cancelar renovação', 'cancel-contract', c.id, true)
                  : '—'}
              </td>
            </tr>`;
          }),
        )}${pagination(rows.length)}
      </section>`
  );
}

export { contracts };
