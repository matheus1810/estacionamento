// Componentes HTML compartilhados: títulos, tabelas, filtros e paginação.

import { state } from '../estado.js';
import { icon } from './icones.js';
import { esc } from '../utils/dom.js';

function action(label, type, glyph = '', secondary = false, data = '') {
  return /* HTML */ `<button
    type="button"
    class="button ${secondary ? 'secondary' : 'primary'}"
    data-action="${type}"
    ${data}
  >
    ${glyph ? icon(glyph) : ''}${label}
  </button>`;
}
function heading(kicker, title, subtitle, buttons = '') {
  return /* HTML */ `<section class="page-heading">
    <div>
      <span class="small-label">${esc(kicker)}</span>
      <h1>${esc(title)}</h1>
      <p>${esc(subtitle)}</p>
    </div>
    <div class="heading-actions">${buttons}</div>
  </section>`;
}
const badge = (label, color = 'green') =>
  /* HTML */ `<span class="badge ${color}">${esc(label)}</span>`;
function empty(title, subtitle, glyph = 'parking') {
  return /* HTML */ `<div class="empty">
    ${icon(glyph)}<strong>${esc(title)}</strong>${esc(subtitle)}
  </div>`;
}
function table(
  headers,
  rows,
  noTitle = 'Nenhum registro por aqui.',
  noSubtitle = 'Os registros aparecerão aqui após o cadastro.',
) {
  if (!rows.length) return empty(noTitle, noSubtitle);
  return /* HTML */ `<div class="table-scroll">
    <table>
      <thead>
        <tr>
          ${headers.map((h) => /* HTML */ `<th scope="col">${h}</th>`).join('')}
        </tr>
      </thead>
      <tbody>
        ${rows.join('')}
      </tbody>
    </table>
  </div>`;
}
function pagination(count) {
  return /* HTML */ `<div class="pagination">
    <span
      >${count ? `${state.offset + 1}–${state.offset + count}` : '0'} registros nesta página</span
    ><button
      class="button secondary"
      data-action="previous"
      ${state.offset === 0 ? 'disabled' : ''}
    >
      ← Anterior</button
    ><button class="button secondary" data-action="next" ${count < state.limit ? 'disabled' : ''}>
      Próxima →
    </button>
  </div>`;
}
function rowAction(label, actionName, id, danger = false) {
  return /* HTML */ `<button
    type="button"
    class="subtle"
    ${danger ? 'style="color:var(--red)"' : ''}
    data-action="${actionName}"
    data-id="${id}"
  >
    ${label}
  </button>`;
}
function toolbar(searchPlaceholder = '', filters = '') {
  return /* HTML */ `<div class="toolbar">
    ${searchPlaceholder
      ? /* HTML */ `<form id="search-form" class="search-form">
          <input
            name="search"
            aria-label="${esc(searchPlaceholder)}"
            placeholder="${esc(searchPlaceholder)}"
            value="${esc(state.query)}"
            maxlength="120"
          /><button class="button secondary" type="submit" aria-label="Buscar">
            ${icon('search')}
          </button>
        </form>`
      : '<span class="toolbar-label">CADASTROS DO ESTACIONAMENTO</span>'}${filters}
  </div>`;
}
function selectFilter(options, label, searchable = false) {
  return /* HTML */ `<select
    id="list-filter"
    aria-label="${esc(label)}"
    ${searchable ? 'data-searchable' : ''}
  >
    ${options
      .map(
        ([value, name]) =>
          /* HTML */ `<option value="${esc(value)}" ${state.filter === value ? 'selected' : ''}>
            ${esc(name)}
          </option>`,
      )
      .join('')}
  </select>`;
}
function queryParams(extra = {}) {
  const params = new URLSearchParams({ offset: state.offset, limite: state.limit, ...extra });
  return params.toString();
}

export {
  action,
  heading,
  badge,
  empty,
  table,
  pagination,
  rowAction,
  toolbar,
  selectFilter,
  queryParams,
};
