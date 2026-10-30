// Mensagens temporárias de sucesso e erro.

import { $ } from '../utils/dom.js';

function toast(message, error = false) {
  const item = document.createElement('div');
  item.className = 'toast' + (error ? ' error' : '');
  item.textContent = message;
  $('#toast-container').append(item);
  setTimeout(() => item.remove(), error ? 8500 : 4500);
}

export { toast };
