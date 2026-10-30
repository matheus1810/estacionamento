// Login, logout e restauração da sessão ao abrir a aplicação.

import { api, post } from './api.js';
import { state } from './estado.js';
import { nav, navigate } from './navegacao.js';
import { token, saveToken } from './sessao.js';
import { icon } from './ui/icones.js';
import { closeModal } from './ui/modal.js';
import { $ } from './utils/dom.js';

let authVersion = 0;

function logout() {
  authVersion++;
  saveToken(null);
  state.user = null;
  state.cache = {};
  state.atendimento = null;
  state.renderId++;
  closeModal();
  $('#app-view').hidden = true;
  $('#login-view').hidden = false;
  $('#login-form').reset();
  $('#main').replaceChildren();
}

function showApp(user) {
  state.user = user;
  $('#login-view').hidden = true;
  $('#app-view').hidden = false;
  $('#user-name').textContent = user.nome;
  $('#avatar').textContent = user.nome
    .split(/\s+/)
    .slice(0, 2)
    .map((v) => v[0])
    .join('')
    .toUpperCase();
  $('#navigation').innerHTML = nav
    .map(
      ([id, name, glyph], i) =>
        /* HTML */ `${i === 6 ? '<div class="nav-separator"></div>' : ''}<a
            class="nav-link"
            href="#${id}"
            data-page="${id}"
            >${icon(glyph)}<span>${name}</span></a
          >`,
    )
    .join('');
  navigate();
}

function bindAuthEvents() {
  $('#logout').addEventListener('click', logout);
  // Limpa também o documento que o navegador pode guardar no cache do histórico.
  window.addEventListener('pagehide', logout);
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) logout();
  });

  $('#login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = $('button', event.target);
    button.disabled = true;
    $('#login-error').hidden = true;
    const version = ++authVersion;
    try {
      const result = await post('/auth/login', Object.fromEntries(new FormData(event.target)));
      if (version !== authVersion) return;
      saveToken(result.access_token);
      const user = await api('/auth/me');
      if (version !== authVersion) return;
      event.target.reset();
      showApp(user);
    } catch (error) {
      if (version !== authVersion) return;
      logout();
      $('#login-error').textContent = error.message;
      $('#login-error').hidden = false;
    } finally {
      button.disabled = false;
    }
  });
  document.addEventListener('session-expired', logout);
}

async function restoreSession() {
  const version = authVersion;
  if (token) {
    try {
      const user = await api('/auth/me');
      if (version !== authVersion) return;
      showApp(user);
      return;
    } catch (error) {
      if (version !== authVersion) return;
      logout();
      $('#login-error').textContent = error.message;
      $('#login-error').hidden = false;
    }
  }
  $('#login-view').hidden = false;
}

export { logout, showApp, bindAuthEvents, restoreSession };
