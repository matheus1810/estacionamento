// Liga os eventos da página aos fluxos. data-action identifica cada botão.

import { api } from './api.js';
import { state } from './estado.js';
import {
  exitModal,
  plateModal,
  consultPlate,
  refreshEntrySpaces,
  spaceDetail,
} from './fluxos/atendimento.js';
import { clientModal } from './fluxos/clientes.js';
import {
  contractModal,
  payModal,
  cancelContract,
  accessModal,
  monthlyAccess,
} from './fluxos/mensalistas.js';
import { userModal } from './fluxos/operadores.js';
import { spaceModal } from './fluxos/vagas.js';
import { vehicleModal } from './fluxos/veiculos.js';
import { vehicleHistory } from './fluxos/historico-veiculo.js';
import { invoiceRequest } from './fluxos/nota-fiscal.js';
import { navigate, navigateTo, render } from './navegacao.js';
import { table, rowAction } from './ui/componentes.js';
import { openModal } from './ui/modal.js';
import { toast } from './ui/notificacoes.js';
import { $, esc } from './utils/dom.js';
import { timestamp } from './utils/formatacao.js';

const actions = {
  refresh: () => render(),
  'new-client': () => clientModal(),
  'edit-client': (id) => clientModal(id),
  'new-vehicle': () => vehicleModal(),
  'edit-vehicle': (id) => vehicleModal(id),
  'vehicle-history': (id) => vehicleHistory(id),
  'invoice-request': (id) => invoiceRequest(id),
  'new-space': () => spaceModal(),
  'edit-space': (id) => spaceModal(id),
  'new-user': () => userModal(),
  'edit-user': (id) => userModal(id),
  'new-contract': () => contractModal(),
  'cancel-contract': (id) => cancelContract(id),
  entry: () => plateModal(),
  exit: (id) => exitModal(id),
  'pay-charge': (id) => payModal(id),
  'access-payment': (id) => payModal(id, state.atendimento?.placa),
  'retry-access': () => monthlyAccess(state.atendimento.placa),
  'refresh-entry-spaces': () => refreshEntrySpaces(),
  access: () => accessModal(),
  'space-detail': (id) => spaceDetail(id),
  previous: () => {
    state.offset = Math.max(0, state.offset - state.limit);
    return render();
  },
  next: () => {
    state.offset += state.limit;
    return render();
  },
  'client-vehicles': async (id) => {
    navigateTo('veiculos');
    await new Promise((resolve) => setTimeout(resolve, 0));
    state.filter = String(id);
    await render();
  },
  'open-stays': () => {
    const rows = state.cache.abertas || [];
    openModal(
      'Horistas no pátio',
      table(
        ['Placa', 'Entrada', ''],
        rows.map(
          (p) =>
            /* HTML */ `<tr>
              <td>
                <span class="plate"
                  >${esc(
                    state.cache.veiculos.find((v) => v.id === p.veiculo_id)?.placa || '—',
                  )}</span
                >
              </td>
              <td>${timestamp(p.entrada)}</td>
              <td>${rowAction('Saída ↗', 'exit', p.id)}</td>
            </tr>`,
        ),
      ),
      null,
    );
  },
};

function bindPageEvents() {
  document.addEventListener('click', async (event) => {
    const link = event.target.closest('a[data-page]');
    if (
      link &&
      event.button === 0 &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.shiftKey &&
      !event.altKey
    ) {
      event.preventDefault();
      navigateTo(link.dataset.page);
      return;
    }
    const button = event.target.closest('[data-action]');
    if (!button || button.disabled) return;
    const fn = actions[button.dataset.action];
    if (!fn) return;
    button.disabled = true;
    try {
      await fn(Number(button.dataset.id));
    } catch (error) {
      toast(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  document.addEventListener('submit', async (event) => {
    if (event.target.id === 'attendance-form') {
      event.preventDefault();
      const button = $('button', event.target);
      button.disabled = true;
      try {
        await consultPlate(new FormData(event.target).get('placa'));
      } catch (error) {
        toast(error.message, true);
        $('#attendance-plate')?.focus();
      } finally {
        button.disabled = false;
      }
    }
    if (event.target.id === 'search-form') {
      event.preventDefault();
      state.query = new FormData(event.target).get('search').trim();
      state.offset = 0;
      render();
    }
    if (event.target.id === 'rates-form') {
      event.preventDefault();
      const button = $('button', event.target);
      button.disabled = true;
      try {
        await api('/tarifas', {
          method: state.cache.tarifa ? 'PUT' : 'POST',
          body: JSON.stringify(Object.fromEntries(new FormData(event.target))),
        });
        toast('Tarifas salvas.');
        await render();
      } catch (error) {
        toast(error.message, true);
      } finally {
        button.disabled = false;
      }
    }
  });
  document.addEventListener('change', (event) => {
    if (event.target.id === 'list-filter') {
      state.filter = event.target.value;
      state.offset = 0;
      render();
    }
    if (event.target.id === 'quick-client') {
      const novo = event.target.value === 'novo';
      $('#quick-client-fields').hidden = !novo;
      $('#quick-client-fields')
        .querySelectorAll('input')
        .forEach((input) => {
          input.disabled = !novo;
          input.required = novo;
        });
    }
  });
  document.addEventListener('input', (event) => {
    if (event.target.name === 'placa' && !event.target.dataset.fieldErrorId)
      event.target.removeAttribute('aria-invalid');
    if (event.target.id !== 'stay-filter') return;
    const query = event.target.value.replace(/[\s-]/g, '').toUpperCase();
    let visible = 0;
    document.querySelectorAll('[data-stay-plate]').forEach((row) => {
      row.hidden = !row.dataset.stayPlate.includes(query);
      if (!row.hidden) visible++;
    });
    $('#stay-count').textContent = `${visible} ${visible === 1 ? 'veículo' : 'veículos'}`;
    $('#stay-no-results').hidden = visible !== 0;
  });
  document.addEventListener('keydown', (event) => {
    if (
      event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      event.key.toLowerCase() === 'p' &&
      state.user &&
      !$('#modal').open
    ) {
      event.preventDefault();
      if (state.page === 'operacao') $('#attendance-plate')?.focus();
      else plateModal();
    }
  });

  $('#menu-toggle').addEventListener('click', () => {
    const open = $('#sidebar').classList.toggle('open');
    $('#menu-toggle').setAttribute('aria-expanded', String(open));
  });
  window.addEventListener('hashchange', navigate);
}

export { bindPageEvents };
