// Select com busca local. O select original continua responsável pelo valor do formulário.

const controls = new WeakMap();
let sequence = 0;
let eventsBound = false;

function normalize(value) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');
}

function bindGlobalEvents() {
  if (eventsBound) return;
  eventsBound = true;
  document.addEventListener('pointerdown', (event) => {
    document.querySelectorAll('[data-select-open]').forEach((wrapper) => {
      if (!wrapper.contains(event.target)) controls.get(wrapper).close();
    });
  });
  const reposition = () =>
    document
      .querySelectorAll('[data-select-open]')
      .forEach((wrapper) => controls.get(wrapper).position());
  document.addEventListener('scroll', reposition, true);
  window.addEventListener('resize', reposition);
  window.visualViewport?.addEventListener('resize', reposition);
  window.visualViewport?.addEventListener('scroll', reposition);
}

function enhance(select) {
  const label = select.getAttribute('aria-label') || select.name;
  const id = `select-busca-${++sequence}`;
  const wrapper = document.createElement('div');
  wrapper.className = 'select-busca';
  wrapper.innerHTML = `
    <div class="select-busca-field">
      <input type="text" role="combobox" aria-autocomplete="list" aria-expanded="false"
        aria-haspopup="listbox" autocomplete="off" spellcheck="false"
        placeholder="Digite para buscar…">
      <button type="button" class="select-busca-toggle" tabindex="-1">▾</button>
    </div>
    <div class="select-busca-popup" popover="manual" hidden>
      <div class="select-busca-list" role="listbox"></div>
      <div class="select-busca-status" role="status" aria-live="polite"></div>
    </div>`;
  const input = wrapper.querySelector('input');
  const toggle = wrapper.querySelector('button');
  const popup = wrapper.querySelector('.select-busca-popup');
  const list = wrapper.querySelector('[role="listbox"]');
  const status = wrapper.querySelector('[role="status"]');
  input.id = id;
  input.setAttribute('aria-label', label);
  input.setAttribute('aria-controls', `${id}-list`);
  input.setAttribute('aria-required', String(select.required));
  toggle.setAttribute('aria-label', `Abrir opções de ${label}`);
  list.id = `${id}-list`;
  list.setAttribute('aria-label', label);
  select.before(wrapper);
  wrapper.prepend(select);
  select.hidden = true;
  select.removeAttribute('aria-label');
  select.setAttribute('aria-hidden', 'true');
  const parentLabel = wrapper.closest('label');
  if (parentLabel) parentLabel.htmlFor = id;

  let matches = [];
  let active = -1;
  let isOpen = false;

  function sync() {
    const selected = select.selectedOptions[0];
    input.value = selected && (selected.value || !select.required) ? selected.label.trim() : '';
    input.disabled = select.disabled;
    toggle.disabled = select.disabled;
    input.removeAttribute('aria-invalid');
  }

  function position() {
    const rect = wrapper.querySelector('.select-busca-field').getBoundingClientRect();
    const viewport = window.visualViewport;
    const viewportTop = viewport?.offsetTop || 0;
    const viewportHeight = viewport?.height || window.innerHeight;
    const below = viewportTop + viewportHeight - rect.bottom - 12;
    const above = rect.top - viewportTop - 12;
    const upwards = below < 180 && above > below;
    popup.style.width = `${Math.min(rect.width, window.innerWidth - 24)}px`;
    popup.style.left = `${Math.max(12, Math.min(rect.left, window.innerWidth - popup.offsetWidth - 12))}px`;
    popup.style.maxHeight = `${Math.max(60, Math.min(260, upwards ? above : below))}px`;
    popup.style.top = `${upwards ? rect.top - popup.offsetHeight - 4 : rect.bottom + 4}px`;
  }

  function setActive(index) {
    active = index;
    [...list.children].forEach((item, i) => item.classList.toggle('active', i === active));
    const item = list.children[active];
    if (item) {
      input.setAttribute('aria-activedescendant', item.id);
      item.scrollIntoView({ block: 'nearest' });
    } else input.removeAttribute('aria-activedescendant');
  }

  function filter(query = '') {
    const term = normalize(query);
    matches = [...select.options].filter(
      (option) =>
        !option.disabled &&
        !option.hidden &&
        (option.value || !select.required) &&
        normalize(option.label).includes(term),
    );
    list.replaceChildren();
    matches.forEach((option, index) => {
      const item = document.createElement('div');
      item.id = `${id}-option-${index}`;
      item.className = 'select-busca-option';
      item.setAttribute('role', 'option');
      item.setAttribute('aria-selected', String(option.selected));
      item.textContent = option.label.trim();
      item.addEventListener('pointerdown', (event) => event.preventDefault());
      item.addEventListener('click', (event) => {
        event.preventDefault();
        choose(index);
      });
      list.append(item);
    });
    status.textContent = matches.length
      ? matches.length === 1
        ? '1 opção encontrada'
        : `${matches.length} opções encontradas`
      : 'Nenhum resultado encontrado.';
    const selectedIndex = matches.findIndex((option) => option.selected);
    setActive(term ? (matches.length ? 0 : -1) : selectedIndex);
    if (isOpen) position();
  }

  function open() {
    if (select.disabled || isOpen) return;
    isOpen = true;
    wrapper.setAttribute('data-select-open', '');
    input.setAttribute('aria-expanded', 'true');
    popup.hidden = false;
    popup.showPopover();
    filter();
    position();
  }

  function close() {
    isOpen = false;
    wrapper.removeAttribute('data-select-open');
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    popup.hidePopover();
    popup.hidden = true;
    sync();
  }

  function choose(index) {
    if (!matches[index]) return;
    select.value = matches[index].value;
    close();
    // Preserva os eventos existentes de filtros e do cadastro rápido.
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }

  input.addEventListener('focus', () => {
    open();
    input.select();
  });
  input.addEventListener('click', open);
  input.addEventListener('input', () => {
    open();
    filter(input.value);
  });
  input.addEventListener('keydown', (event) => {
    if (event.isComposing) return;
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      if (['Home', 'End'].includes(event.key) && !isOpen) return;
      event.preventDefault();
      open();
      const last = matches.length - 1;
      const next =
        event.key === 'Home'
          ? 0
          : event.key === 'End'
            ? last
            : event.key === 'ArrowDown'
              ? Math.min(last, active + 1)
              : active < 0
                ? last
                : Math.max(0, active - 1);
      setActive(next);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (isOpen) choose(active);
      else open();
    } else if (event.key === 'Escape' && isOpen) {
      event.preventDefault();
      event.stopPropagation();
      close();
    } else if (event.key === 'Tab') close();
  });
  toggle.addEventListener('pointerdown', (event) => event.preventDefault());
  toggle.addEventListener('click', () => {
    if (isOpen) close();
    else {
      input.focus();
      open();
    }
  });
  wrapper.addEventListener('focusout', (event) => {
    if (!wrapper.contains(event.relatedTarget)) close();
  });
  select.addEventListener('change', () => {
    sync();
    if (isOpen) filter();
  });
  select.addEventListener('invalid', (event) => {
    event.preventDefault();
    input.focus();
    open();
    input.setAttribute('aria-invalid', 'true');
    status.textContent = 'Selecione uma opção da lista.';
  });
  const control = {
    close,
    position,
    refresh: () => {
      close();
    },
    input,
  };
  controls.set(select, control);
  controls.set(wrapper, control);
  sync();
}

function initSearchableSelects(root = document) {
  bindGlobalEvents();
  root.querySelectorAll('select[data-searchable]').forEach((select) => {
    if (!controls.has(select)) enhance(select);
  });
}

function refreshSearchableSelect(select) {
  controls.get(select)?.refresh();
  return controls.get(select)?.input || select;
}

function closeSearchableSelects(root = document) {
  root.querySelectorAll('[data-select-open]').forEach((wrapper) => controls.get(wrapper).close());
}

export { initSearchableSelects, refreshSearchableSelect, closeSearchableSelects };
