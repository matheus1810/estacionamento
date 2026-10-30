// Entrada da aplicação: registra os eventos, inicia o relógio e restaura a sessão.

import { bindAuthEvents, restoreSession } from './js/autenticacao.js';
import { bindPageEvents } from './js/eventos.js';
import { bindModalEvents } from './js/ui/modal.js';
import { $ } from './js/utils/dom.js';

function start() {
  bindModalEvents();
  bindAuthEvents();
  bindPageEvents();
  tick();
  setInterval(tick, 30000);
  restoreSession();
}

function tick() {
  const now = new Date();
  $('#clock').textContent = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    hour: '2-digit',
    minute: '2-digit',
  }).format(now);
  $('#sidebar-date').textContent = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(now);
}

start();
