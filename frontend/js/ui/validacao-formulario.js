// Mensagens junto aos campos, associação acessível e foco no primeiro erro.

import { registrationError } from '../utils/validacao-campos.js';

let sequence = 0;
const fieldSelector = 'input[name], select[name], textarea[name]';

function proxy(field) {
  return field.closest('.select-busca')?.querySelector('input[role="combobox"]') || field;
}

function labelOf(field) {
  const label = field.labels?.[0];
  return (
    field.getAttribute('aria-label') ||
    field.dataset.fieldLabel ||
    (label
      ? [...label.childNodes]
          .filter((node) => node.nodeType === Node.TEXT_NODE)
          .map((node) => node.textContent)
          .join('')
          .trim()
      : '') ||
    'Campo'
  );
}

function clearFieldError(field) {
  const id = field.dataset.fieldErrorId;
  if (!id) return;
  document.getElementById(id)?.remove();
  for (const element of new Set([field, proxy(field)])) {
    element.removeAttribute('aria-invalid');
    const description = (element.getAttribute('aria-describedby') || '')
      .split(' ')
      .filter((item) => item && item !== id)
      .join(' ');
    if (description) element.setAttribute('aria-describedby', description);
    else element.removeAttribute('aria-describedby');
  }
  delete field.dataset.fieldErrorId;
}

function showFieldError(field, message) {
  let error = document.getElementById(field.dataset.fieldErrorId);
  if (!error) {
    error = document.createElement('span');
    error.id = `field-error-${++sequence}`;
    error.className = 'field-error';
    error.setAttribute('role', 'alert');
    (field.closest('.select-busca') || field).after(error);
    field.dataset.fieldErrorId = error.id;
  }
  error.textContent = message;
  for (const element of new Set([field, proxy(field)])) {
    element.setAttribute('aria-invalid', 'true');
    const descriptions = new Set(
      (element.getAttribute('aria-describedby') || '').split(' ').filter(Boolean),
    );
    descriptions.add(error.id);
    element.setAttribute('aria-describedby', [...descriptions].join(' '));
  }
}

function fieldError(field) {
  if (field.matches(':disabled') || !field.willValidate) return '';
  const value = field.value.trim();
  const label = labelOf(field);
  if (field.required && !value) {
    return field.tagName === 'SELECT'
      ? 'Selecione uma opção da lista.'
      : `${label}: preencha este campo.`;
  }
  if (!value) return '';
  const custom = registrationError(field.name, value, field.dataset.validation);
  if (custom) return custom;
  if (field.maxLength >= 0 && [...value].length > field.maxLength) {
    return `${label}: use no máximo ${field.maxLength} caracteres.`;
  }
  if (field.minLength > 0 && [...value].length < field.minLength) {
    return `${label}: informe pelo menos ${field.minLength} caracteres.`;
  }
  const validity = field.validity;
  if (validity.typeMismatch && field.type === 'email') return `${label}: informe um e-mail válido.`;
  if (validity.badInput) return `${label}: informe um número válido.`;
  if (validity.rangeUnderflow) return `${label}: o valor mínimo é ${field.min}.`;
  if (validity.rangeOverflow) return `${label}: o valor máximo é ${field.max}.`;
  if (validity.stepMismatch) return `${label}: confira o intervalo permitido para este valor.`;
  if (!validity.valid) return `${label}: confira o formato informado.`;
  return '';
}

function summary(form, extra = []) {
  const box = form.querySelector('#modal-error');
  box.textContent = ['Corrija os campos destacados para continuar.', ...extra].join('\n');
  box.dataset.validation = 'true';
  box.hidden = false;
}

function clearDisabledErrors(form) {
  form.querySelectorAll(fieldSelector).forEach((field) => {
    if (field.matches(':disabled')) clearFieldError(field);
  });
  const remaining = [...form.querySelectorAll(fieldSelector)].some(
    (field) => field.dataset.fieldErrorId,
  );
  const box = form.querySelector('#modal-error');
  if (!remaining && box.dataset.validation) box.hidden = true;
}

function validateForm(form) {
  const invalid = [];
  form.querySelectorAll(fieldSelector).forEach((field) => {
    clearFieldError(field);
    const message = fieldError(field);
    if (message) {
      showFieldError(field, message);
      invalid.push(field);
    }
  });
  if (!invalid.length) return true;
  summary(form);
  proxy(invalid[0]).focus();
  return false;
}

function applyServerErrors(form, errors = []) {
  if (!errors.length) return false;
  let first;
  const extra = [];
  for (const error of errors) {
    const parts = error.campo.split('.');
    const name = error.campo.startsWith('nota_fiscal.') ? `nf_${parts.at(-1)}` : parts.at(-1);
    const field = form.elements.namedItem(name);
    if (field instanceof HTMLElement && !field.matches(':disabled')) {
      showFieldError(field, error.mensagem);
      first ||= field;
    } else extra.push(error.mensagem);
  }
  summary(form, extra);
  if (first) proxy(first).focus();
  return true;
}

function bindFormValidation(form) {
  // A validação é exibida no formulário em português, em vez do balão do navegador.
  form.noValidate = true;
  const update = (event) => {
    const field = event.target;
    if (field.matches(fieldSelector) && field.dataset.fieldErrorId) {
      const message = fieldError(field);
      if (message) showFieldError(field, message);
      else clearFieldError(field);
    }
    queueMicrotask(() => clearDisabledErrors(form));
  };
  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('focusout', (event) => {
    const field = event.target;
    if (!field.matches(fieldSelector) || !field.value.trim()) return;
    const message = fieldError(field);
    if (message) showFieldError(field, message);
    else clearFieldError(field);
  });
}

export { bindFormValidation, validateForm, applyServerErrors };
