// Campos opcionais e payload do pedido de nota, compartilhados pelos pagamentos.

import { input } from './formularios.js';

function invoiceRequestFields() {
  return /* HTML */ ` <section class="invoice-request">
    <label class="invoice-toggle">
      <input
        type="checkbox"
        name="solicitar_nota_fiscal"
        value="sim"
        aria-controls="invoice-request-fields"
        aria-expanded="false"
      />
      <span>Cliente solicitou nota fiscal</span>
    </label>
    <fieldset id="invoice-request-fields" class="invoice-fields" hidden disabled>
      <legend>Dados para emissão posterior</legend>
      ${input('nf_nome', 'Nome ou razão social', 'text', '', {
        required: true,
        maxlength: 120,
        autocomplete: 'name',
      })}
      ${input('nf_documento', 'CPF/CNPJ', 'text', '', {
        required: true,
        minlength: 11,
        maxlength: 18,
        autocomplete: 'off',
        'aria-describedby': 'invoice-document-hint',
      })}
      <p id="invoice-document-hint" class="invoice-hint">Com ou sem pontuação.</p>
      ${input('nf_email', 'E-mail para envio (opcional)', 'email', '', {
        maxlength: 254,
        autocomplete: 'email',
      })}
      ${input('nf_endereco', 'Endereço (opcional)', 'text', '', {
        maxlength: 250,
        autocomplete: 'street-address',
      })}
      <p class="invoice-hint">O pedido será salvo com o pagamento para emissão posterior.</p>
    </fieldset>
  </section>`;
}

function initInvoiceRequest(root) {
  const checkbox = root.querySelector('[name="solicitar_nota_fiscal"]');
  if (!checkbox) return;
  const fields = root.querySelector('#invoice-request-fields');
  const toggle = () => {
    fields.hidden = !checkbox.checked;
    fields.disabled = !checkbox.checked;
    checkbox.setAttribute('aria-expanded', String(checkbox.checked));
  };
  checkbox.addEventListener('change', toggle);
  toggle();
}

function paymentPayload(values) {
  const result = { forma_pagamento: values.forma_pagamento };
  if (values.solicitar_nota_fiscal === 'sim') {
    const document = values.nf_documento.replace(/[.\-/\s]/g, '').toUpperCase();
    if (!/^(?:[0-9]{11}|[A-Z0-9]{12}[0-9]{2})$/.test(document)) {
      throw new Error('Confira o CPF/CNPJ: use 11 dígitos para CPF ou 14 caracteres para CNPJ.');
    }
    result.nota_fiscal = {
      nome: values.nf_nome.trim(),
      documento: document,
      email: values.nf_email.trim() || null,
      endereco: values.nf_endereco.trim() || null,
    };
  }
  return result;
}

export { invoiceRequestFields, initInvoiceRequest, paymentPayload };
