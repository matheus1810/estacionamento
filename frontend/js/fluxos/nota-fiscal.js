// Consulta do pedido salvo na cobrança para emissão posterior.

import { api } from '../api.js';
import { state } from '../estado.js';
import { openModal, modalVersion } from '../ui/modal.js';
import { esc } from '../utils/dom.js';
import { timestamp } from '../utils/formatacao.js';
import { action } from '../ui/componentes.js';

async function invoiceRequest(id) {
  openModal('Solicitação de nota fiscal', '<p role="status">Carregando solicitação…</p>', null);
  const version = modalVersion;
  let request;
  try {
    request = await api(`/cobrancas/${id}/nota-fiscal`);
  } catch (error) {
    if (version !== modalVersion || !state.user) return;
    openModal(
      'Solicitação de nota fiscal',
      `<p role="alert">${esc(error.message)}</p>` +
        action('Tentar novamente', 'invoice-request', 'refresh', true, `data-id="${id}"`),
      null,
    );
    return;
  }
  if (version !== modalVersion || !state.user) return;
  openModal(
    'Solicitação de nota fiscal',
    /* HTML */ ` <p>Solicitada para emissão posterior · cobrança #${id}</p>
      <dl class="details">
        <div>
          <dt>Nome ou razão social</dt>
          <dd>${esc(request.nome)}</dd>
        </div>
        <div>
          <dt>CPF/CNPJ</dt>
          <dd>${esc(request.documento)}</dd>
        </div>
        <div>
          <dt>E-mail para envio</dt>
          <dd>${esc(request.email || 'Não informado')}</dd>
        </div>
        <div>
          <dt>Endereço</dt>
          <dd>${esc(request.endereco || 'Não informado')}</dd>
        </div>
        <div>
          <dt>Solicitada em</dt>
          <dd>${timestamp(request.criado_em)}</dd>
        </div>
      </dl>`,
    null,
  );
}

export { invoiceRequest };
