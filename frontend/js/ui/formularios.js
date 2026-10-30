// Campos reutilizáveis dos formulários.

import { esc } from '../utils/dom.js';

function input(name, label, type = 'text', value = '', attributes = {}) {
  const attrs = Object.entries(attributes)
    .map(([k, v]) => (v === true ? k : `${k}="${esc(v)}"`))
    .join(' ');
  return /* HTML */ `<label
    >${label}<input name="${name}" type="${type}" value="${esc(value)}" ${attrs}
  /></label>`;
}
function select(name, label, options, value = '', required = true) {
  const searchable = ['cliente_id', 'veiculo_id', 'vaga_id'].includes(name);
  return /* HTML */ `<label
    >${label}<select
      name="${name}"
      aria-label="${esc(label)}"
      ${required ? 'required' : ''}
      ${searchable ? 'data-searchable' : ''}
    >
      <option value="">Selecione…</option>
      ${options
        .map(
          ([id, title]) =>
            /* HTML */ `<option
              value="${esc(id)}"
              ${String(id) === String(value) ? 'selected' : ''}
            >
              ${esc(title)}
            </option>`,
        )
        .join('')}
    </select></label
  >`;
}
const activeSelect = (label, value, name = 'ativo') =>
  select(
    name,
    label,
    [
      ['true', 'Ativo'],
      ['false', 'Inativo'],
    ],
    String(value),
  );
const paymentSelect = () =>
  select('forma_pagamento', 'Forma de pagamento', [
    ['pix', 'Pix'],
    ['dinheiro', 'Dinheiro'],
    ['cartao', 'Cartão'],
  ]);

export { input, select, activeSelect, paymentSelect };
