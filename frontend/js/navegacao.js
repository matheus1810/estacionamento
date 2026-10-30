// Rotas pelo hash da URL e renderização da tela selecionada.

import { state } from './estado.js';
import { clients } from './telas/clientes.js';
import { charges } from './telas/cobrancas.js';
import { contracts } from './telas/mensalistas.js';
import { operation } from './telas/operacao.js';
import { operators } from './telas/operadores.js';
import { rates } from './telas/tarifas.js';
import { spaces } from './telas/vagas.js';
import { vehicles } from './telas/veiculos.js';
import { action } from './ui/componentes.js';
import { closeModal } from './ui/modal.js';
import { $, esc } from './utils/dom.js';
import { initSearchableSelects } from './ui/select-busca.js';

const nav = [
  ['operacao', 'Visão geral', 'grid'],
  ['clientes', 'Clientes', 'users'],
  ['veiculos', 'Veículos', 'car'],
  ['vagas', 'Vagas', 'parking'],
  ['mensalistas', 'Mensalistas', 'calendar'],
  ['cobrancas', 'Cobranças', 'receipt'],
  ['tarifas', 'Tarifas', 'sliders'],
  ['usuarios', 'Operadores', 'shield'],
];

function navigateTo(page) {
  if (!state.user || !nav.some(([id]) => id === page)) return;
  // Os menus são telas do mesmo documento; preserva a página externa anterior.
  history.replaceState(history.state, '', `#${page}`);
  navigate();
}

function navigate() {
  if (!state.user) return;
  const page = location.hash.slice(1);
  state.page = nav.some((v) => v[0] === page) ? page : 'operacao';
  state.offset = 0;
  state.query = '';
  state.filter = '';
  document.querySelectorAll('.nav-link').forEach((a) => {
    a.classList.toggle('active', a.dataset.page === state.page);
    if (a.dataset.page === state.page) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  $('#breadcrumb').textContent = nav.find((v) => v[0] === state.page)[1];
  $('#sidebar').classList.remove('open');
  $('#menu-toggle').setAttribute('aria-expanded', 'false');
  closeModal();
  render();
}

async function render() {
  const renderId = ++state.renderId;
  $('#main').innerHTML =
    '<div class="loading" role="status"><span class="spinner"></span>Carregando seu estacionamento…</div>';
  try {
    const html = await {
      operacao: operation,
      clientes: clients,
      veiculos: vehicles,
      vagas: spaces,
      mensalistas: contracts,
      cobrancas: charges,
      tarifas: rates,
      usuarios: operators,
    }[state.page]();
    if (renderId !== state.renderId || !state.user) return;
    $('#main').innerHTML = html;
    initSearchableSelects($('#main'));
    if (state.page === 'operacao' && !$('#modal').open) $('#attendance-plate')?.focus();
  } catch (error) {
    if (renderId !== state.renderId || !state.user) return;
    $('#main').innerHTML = /* HTML */ `<div class="error-panel">
      <h2>Não foi possível carregar os dados.</h2>
      <p>${esc(error.message)}</p>
      ${action('Tentar novamente', 'refresh', 'refresh')}
    </div>`;
  }
}

export { nav, navigate, navigateTo, render };
