// Cliente HTTP: autenticação, erros da API e leitura de todas as páginas.

import { token } from './sessao.js';

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch {
    throw new Error('Não foi possível conectar. Confira se o servidor está em execução.');
  }
  const data = await response.json().catch(() => ({}));
  if (response.status === 401 && path !== '/auth/login') {
    document.dispatchEvent(new Event('session-expired'));
    throw new Error('Sua sessão terminou. Entre novamente.');
  }
  if (!response.ok) {
    const error = new Error(
      typeof data.detail === 'string' ? data.detail : 'Confira os dados informados.',
    );
    error.status = response.status;
    error.fieldErrors = Array.isArray(data.erros)
      ? data.erros.filter(
          (item) => item && typeof item.campo === 'string' && typeof item.mensagem === 'string',
        )
      : [];
    if (error.fieldErrors.length)
      error.message = error.fieldErrors.map((item) => item.mensagem).join('\n');
    throw error;
  }
  return data;
}
const post = (path, body) =>
  api(path, { method: 'POST', ...(body !== undefined ? { body: JSON.stringify(body) } : {}) });
const patch = (path, body) => api(path, { method: 'PATCH', body: JSON.stringify(body) });

async function all(path) {
  const result = [];
  for (let offset = 0; ; offset += 100) {
    const rows = await api(`${path}${path.includes('?') ? '&' : '?'}offset=${offset}&limite=100`);
    result.push(...rows);
    if (rows.length < 100) return result;
  }
}

export { api, post, patch, all };
