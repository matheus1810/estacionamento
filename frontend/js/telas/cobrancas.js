// Consulta os dados e monta a tela de cobrancas.

import { api, post, all } from '../api.js';
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
import { money, localDate, today } from '../utils/formatacao.js';

async function charges() {
  // POST explícito antes de listar, como exige a regra de geração sem agendador.
  await post('/cobrancas/atualizar-mensalidades');
  const [rows, contratos, clientes, vagas] = await Promise.all([
    api(
      '/cobrancas?' +
        queryParams(
          state.filter === 'nota-fiscal'
            ? { nota_fiscal: true }
            : state.filter
              ? { pendentes: state.filter }
              : {},
        ),
    ),
    all('/contratacoes'),
    all('/clientes'),
    all('/vagas'),
  ]);
  Object.assign(state.cache, { rows, contratos, clientes, vagas });
  return (
    heading(
      'CONTROLE DE RECEBIMENTOS',
      'Cobranças',
      'Mensalidades atualizadas ao abrir esta tela. Valores antigos são preservados.',
      action('Atualizar mensalidades', 'refresh', 'refresh', true),
    ) +
    /* HTML */ `<section class="panel">
      ${toolbar(
        '',
        selectFilter(
          [
            ['', 'Todas as cobranças'],
            ['true', 'Pendentes'],
            ['false', 'Pagas'],
            ['nota-fiscal', 'Com solicitação de NF'],
          ],
          'Situação do pagamento',
        ),
      )}${table(
        ['Origem / cliente', 'Vencimento', 'Valor', 'Situação', 'Pagamento', ''],
        rows.map((c) => {
          const contrato = contratos.find((v) => v.id === c.contratacao_mensal_id);
          const cliente = contrato ? clientes.find((v) => v.id === contrato.cliente_id) : null;
          const vaga = contrato ? vagas.find((v) => v.id === contrato.vaga_id) : null;
          const status = c.pago_em ? 'Paga' : c.vencimento < today() ? 'Vencida' : 'Pendente';
          return /* HTML */ `<tr>
            <td>
              <strong
                >${contrato
                  ? esc(cliente?.nome || 'Mensalista')
                  : `Horista · permanência #${c.permanencia_id}`}</strong
              >
              <div class="muted" style="font-size:9px;margin-top:5px">
                ${contrato
                  ? `Vaga ${esc(vaga?.numero || contrato.vaga_id)} · competência ${c.competencia.slice(0, 7).split('-').reverse().join('/')}`
                  : 'Pagamento na saída'}
              </div>
            </td>
            <td>${localDate(c.vencimento)}</td>
            <td><strong>${money(c.valor)}</strong></td>
            <td>
              ${badge(status, status === 'Paga' ? 'green' : status === 'Vencida' ? 'red' : 'amber')}
            </td>
            <td>
              ${c.pago_em
                ? /* HTML */ `${esc(c.forma_pagamento)}
                    <div class="muted" style="font-size:9px;margin-top:4px">
                      ${localDate(c.pago_em)}
                    </div>`
                : '—'}
            </td>
            <td>
              <div class="table-actions">
                ${!c.pago_em && contrato ? rowAction('Receber', 'pay-charge', c.id) : ''}
                ${c.nota_fiscal_solicitada
                  ? rowAction('Ver pedido de NF', 'invoice-request', c.id)
                  : ''}
                ${c.pago_em && !c.nota_fiscal_solicitada ? '—' : ''}
              </div>
            </td>
          </tr>`;
        }),
      )}${pagination(rows.length)}
    </section>`
  );
}

export { charges };
