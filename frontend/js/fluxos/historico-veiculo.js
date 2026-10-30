// Consulta paginada das permanências do veículo, sem alterar os dados da listagem.

import { api } from '../api.js';
import { state } from '../estado.js';
import { badge, empty } from '../ui/componentes.js';
import { openModal, modalVersion } from '../ui/modal.js';
import { $, esc } from '../utils/dom.js';
import { duration, money, timestamp } from '../utils/formatacao.js';

const PAGE_SIZE = 10;
const paymentNames = { pix: 'Pix', dinheiro: 'Dinheiro', cartao: 'Cartão' };

function movementCard(movement) {
  const closed = Boolean(movement.saida);
  const paid = Boolean(movement.pago_em);
  const amount =
    movement.valor_cobrado === null
      ? closed
        ? 'Sem cobrança registrada'
        : 'Calculado na saída'
      : money(movement.valor_cobrado);
  return /* HTML */ ` <article class="vehicle-movement">
    <div class="movement-heading">
      <h3>Permanência #${movement.permanencia_id}</h3>
      ${badge(closed ? 'Encerrada' : 'No pátio', closed ? 'gray' : 'green')}
    </div>
    <dl class="movement-details">
      <div>
        <dt>Entrada</dt>
        <dd>${timestamp(movement.entrada)}</dd>
        <dd class="muted">${esc(movement.operador_entrada)}</dd>
      </div>
      <div>
        <dt>Saída</dt>
        <dd>${closed ? timestamp(movement.saida) : 'Ainda no pátio'}</dd>
        ${movement.operador_saida ? `<dd class="muted">${esc(movement.operador_saida)}</dd>` : ''}
      </div>
      <div>
        <dt>Vaga</dt>
        <dd>${esc(movement.vaga_numero)}</dd>
      </div>
      <div>
        <dt>Tempo de permanência</dt>
        <dd>${closed ? duration(movement.entrada, movement.saida) : 'Em andamento'}</dd>
      </div>
      <div class="movement-full">
        <dt>Cliente na entrada</dt>
        <dd>${esc(movement.cliente_nome)}</dd>
      </div>
      <div>
        <dt>Tarifa da entrada</dt>
        <dd>${money(movement.valor_hora_aplicado)}/hora</dd>
      </div>
      <div>
        <dt>Valor cobrado</dt>
        <dd>${amount}</dd>
      </div>
      <div class="movement-full">
        <dt>Pagamento</dt>
        <dd>
          ${paid
            ? `${esc(paymentNames[movement.forma_pagamento] || movement.forma_pagamento)} · ${timestamp(movement.pago_em)}`
            : movement.valor_cobrado !== null
              ? 'Pendente'
              : 'Sem pagamento registrado'}
        </dd>
      </div>
    </dl>
  </article>`;
}

async function vehicleHistory(id) {
  const vehicle = state.cache.rows?.find((row) => row.id === id);
  if (!vehicle) throw new Error('Atualize a lista de veículos antes de consultar o histórico.');
  const summary = /* HTML */ ` <div class="vehicle-history-summary" tabindex="-1">
    <span class="plate">${esc(vehicle.placa)}</span>
    <p>${esc(vehicle.modelo)} · ${esc(vehicle.cor)}</p>
    <p>Entradas e saídas de horistas, da mais recente para a mais antiga.</p>
  </div>`;

  async function loadPage(offset = 0) {
    openModal(
      'Histórico do veículo',
      `${summary}<div class="loading" role="status">
      <span class="spinner"></span>Carregando movimentações…</div>`,
      null,
    );
    const version = modalVersion;
    try {
      // Uma linha extra informa se há outra página, sem carregar todo o histórico.
      const rows = await api(`/veiculos/${id}/historico?offset=${offset}&limite=${PAGE_SIZE + 1}`);
      if (version !== modalVersion || !state.user) return;
      const page = rows.slice(0, PAGE_SIZE);
      const content = page.length
        ? `<div class="vehicle-movements">${page.map(movementCard).join('')}</div>`
        : empty(
            'Nenhuma movimentação registrada.',
            'Este veículo ainda não tem permanências nesta consulta.',
            'clock',
          );
      openModal(
        'Histórico do veículo',
        /* HTML */ `${summary}${content}
          <div class="history-pagination">
            <span>${page.length ? `${offset + 1}–${offset + page.length}` : '0'} registros</span>
            <button
              type="button"
              class="button secondary"
              data-history-offset="${offset - PAGE_SIZE}"
              ${offset === 0 ? 'disabled' : ''}
            >
              ← Anterior
            </button>
            <button
              type="button"
              class="button secondary"
              data-history-offset="${offset + PAGE_SIZE}"
              ${rows.length <= PAGE_SIZE ? 'disabled' : ''}
            >
              Próxima →
            </button>
          </div>`,
        null,
      );
      $('#modal-body')
        .querySelectorAll('[data-history-offset]')
        .forEach((button) => {
          button.addEventListener('click', () => loadPage(Number(button.dataset.historyOffset)));
        });
      $('#modal-body .vehicle-history-summary').focus({ preventScroll: true });
    } catch (error) {
      if (version !== modalVersion || !state.user) return;
      openModal(
        'Histórico do veículo',
        /* HTML */ `${summary}
          <p role="alert">${esc(error.message)}</p>
          <button type="button" class="button secondary" id="history-retry">
            Tentar novamente
          </button>`,
        null,
      );
      $('#history-retry').addEventListener('click', () => loadPage(offset));
    }
    $('#modal').scrollTop = 0;
  }

  await loadPage();
}

export { vehicleHistory };
