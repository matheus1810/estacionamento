// Ciclo de vida da janela: abertura, fechamento, envio e proteção contra respostas antigas.

import { state } from '../estado.js';
import { toast } from './notificacoes.js';
import { $ } from '../utils/dom.js';
import { initSearchableSelects, closeSearchableSelects } from './select-busca.js';
import { initInvoiceRequest } from './nota-fiscal.js';

let modalHandler = null;
let modalVersion = 0;

function openModal(title, body, handler, button = 'Salvar') {
  modalVersion++;
  $('#modal-title').textContent = title;
  $('#modal-body').innerHTML = body;
  initSearchableSelects($('#modal-body'));
  initInvoiceRequest($('#modal-body'));
  $('#modal-error').hidden = true;
  $('#modal-submit').textContent = button;
  $('#modal-submit').disabled = !handler;
  $('#modal-submit').hidden = !handler;
  $('#modal-cancel').textContent = handler ? 'Cancelar' : 'Fechar';
  modalHandler = handler;
  if (!$('#modal').open) $('#modal').showModal();
  const first = $(
    '#modal-body input:enabled, #modal-body select:enabled:not([hidden]), #modal-body button:enabled',
  );
  if (first) first.focus();
}
function closeModal() {
  closeSearchableSelects($('#modal-body'));
  $('#modal').close();
  modalHandler = null;
  modalVersion++;
  if (state.page === 'operacao') $('#attendance-plate')?.focus();
}

function bindModalEvents() {
  $('#modal-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!modalHandler) return;
    const handler = modalHandler;
    const version = modalVersion;
    $('#modal-submit').disabled = true;
    $('#modal-error').hidden = true;
    $('#modal-close').disabled = true;
    $('#modal-cancel').disabled = true;
    try {
      await handler(Object.fromEntries(new FormData(event.target)));
    } catch (error) {
      if (version === modalVersion) {
        $('#modal-error').textContent = error.message;
        $('#modal-error').hidden = false;
      } else toast(error.message, true);
    } finally {
      $('#modal-close').disabled = false;
      $('#modal-cancel').disabled = false;
      $('#modal-submit').disabled = !modalHandler;
    }
  });
  $('#modal-close').addEventListener('click', closeModal);
  $('#modal-cancel').addEventListener('click', closeModal);
  $('#modal').addEventListener('cancel', (event) => {
    if ($('#modal-cancel').disabled) event.preventDefault();
    else {
      closeSearchableSelects($('#modal-body'));
      modalHandler = null;
      modalVersion++;
    }
  });
}

export { openModal, closeModal, modalVersion, bindModalEvents };
