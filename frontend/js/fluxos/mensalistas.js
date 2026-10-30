// Contratação, cancelamento, consulta de acesso e recebimento de mensalidades.

import { post, all } from '../api.js';
import { state } from '../estado.js';
import { action, table, rowAction } from '../ui/componentes.js';
import { complete } from './conclusao.js';
import { input, select, paymentSelect } from '../ui/formularios.js';
import { icon } from '../ui/icones.js';
import { openModal } from '../ui/modal.js';
import { toast } from '../ui/notificacoes.js';
import { esc } from '../utils/dom.js';
import { money, localDate, today } from '../utils/formatacao.js';
import { invoiceRequestFields, paymentPayload } from '../ui/nota-fiscal.js';

async function contractModal() {
  const [clientes, vagas] = await Promise.all([all('/clientes'), all('/vagas')]);
  if (!clientes.some((c) => c.ativo) || !vagas.some((v) => v.ativa)) {
    toast('Cadastre cliente ativo, vaga ativa e tarifas antes de contratar.', true);
    return;
  }
  openModal(
    'Nova contratação',
    /* HTML */ `<div class="notice">
        Reserva exclusiva. A primeira mensalidade é gerada no início do contrato. Valor integral,
        sem proporcionalidade.
      </div>
      <div class="form-stack">
        ${select(
          'cliente_id',
          'Cliente',
          clientes.filter((c) => c.ativo).map((c) => [c.id, c.nome]),
        )}${select(
          'vaga_id',
          'Vaga',
          vagas.filter((v) => v.ativa).map((v) => [v.id, `Vaga ${v.numero}`]),
        )}
        <div class="form-grid">
          ${input('data_inicio', 'Data de início', 'date', today(), { required: true })}${input(
            'data_fim',
            'Último dia da reserva (opcional)',
            'date',
          )}
        </div>
      </div>`,
    async (values) => {
      await post('/contratacoes', {
        cliente_id: Number(values.cliente_id),
        vaga_id: Number(values.vaga_id),
        data_inicio: values.data_inicio,
        data_fim: values.data_fim || null,
      });
      await complete('Contratação criada. Consulte a tela Cobranças para receber a mensalidade.');
    },
    'Criar contratação',
  );
}

function payModal(id, placa = null) {
  const c = (placa ? state.atendimento?.pendencias : state.cache.rows)?.find((c) => c.id === id);
  if (!c) throw new Error('Atualize a consulta antes de receber esta cobrança.');
  openModal(
    'Receber mensalidade',
    /* HTML */ `<dl class="details">
        <div>
          <dt>Vencimento</dt>
          <dd>${localDate(c.vencimento)}</dd>
        </div>
        <div>
          <dt>Competência</dt>
          <dd>${c.competencia.slice(0, 7).split('-').reverse().join('/')}</dd>
        </div>
      </dl>
      <div class="total"><span>Pagamento integral</span><strong>${money(c.valor)}</strong></div>
      ${paymentSelect()}${invoiceRequestFields()}`,
    async (values) => {
      const payment = await post(`/cobrancas/${id}/pagar`, paymentPayload(values));
      const invoiceMessage = payment.nota_fiscal_solicitada
        ? ' Solicitação de nota fiscal salva para emissão posterior.'
        : '';
      if (placa) {
        toast('Mensalidade recebida. Conferindo o acesso…' + invoiceMessage);
        openModal(
          'Pagamento confirmado',
          /* HTML */ `<p>O pagamento foi registrado. Confira novamente o acesso do mensalista.</p>
            ${action('Conferir acesso', 'retry-access', 'refresh', true)}`,
          null,
        );
        await monthlyAccess(placa);
        return;
      }
      await complete('Mensalidade recebida.' + invoiceMessage);
    },
    'Confirmar pagamento',
  );
}

function cancelContract(id) {
  openModal(
    'Cancelar renovação',
    /* HTML */ `<p>
        A reserva permanece até o fim do último período já iniciado. A contratação não terá novas
        renovações depois dessa data.
      </p>
      <div class="notice">
        Os valores já cobrados são preservados, inclusive dívidas. Não há devolução ou crédito por
        cancelamento antecipado.
      </div>`,
    async () => {
      const c = await post(`/contratacoes/${id}/cancelar`);
      await complete(`Renovação cancelada. Reserva mantida até ${localDate(c.data_fim)}.`);
    },
    'Confirmar cancelamento',
  );
}

function accessModal() {
  openModal(
    'Consultar mensalista',
    /* HTML */ `<p>
        Consulte a placa antes de liberar o acesso. Esta consulta atualiza as mensalidades e não
        registra entrada ou saída.
      </p>
      ${input('placa', 'Placa do veículo', 'text', '', {
        required: true,
        maxlength: 12,
        placeholder: 'ABC1D23',
        autocomplete: 'off',
      })}`,
    async (values) => {
      await monthlyAccess(values.placa);
    },
    'Consultar acesso',
  );
}

async function monthlyAccess(placa) {
  const result = await post('/cobrancas/consultar-acesso', { placa });
  const pendencias = result.cliente_id
    ? await all('/cobrancas?vencidas=true&cliente_id=' + result.cliente_id)
    : [];
  state.atendimento = { ...state.atendimento, placa, pendencias };
  const rows = pendencias.map(
    (c) =>
      /* HTML */ `<tr>
        <td>${localDate(c.vencimento)}</td>
        <td><strong>${money(c.valor)}</strong></td>
        <td>${rowAction('Receber', 'access-payment', c.id)}</td>
      </tr>`,
  );
  openModal(
    'Resultado da consulta',
    /* HTML */ `<p class="access-plate">
        <span class="plate">${esc(placa.replace(/[\s-]/g, '').toUpperCase())}</span>
      </p>
      <div class="access-result ${result.liberado ? '' : 'blocked'}">
        ${icon(result.liberado ? 'check' : 'lock')}
        <h3>${result.liberado ? 'Acesso liberado' : 'Acesso bloqueado'}</h3>
        <p>${esc(result.motivo)}</p>
        ${result.vagas.length
          ? /* HTML */ `<p style="margin-top:16px;font-size:11px">
              ${result.vagas.length}
              ${result.vagas.length === 1 ? 'vaga contratada' : 'vagas contratadas'}
            </p>`
          : ''}
      </div>
      ${rows.length
        ? /* HTML */ `<h3 class="debt-title">Mensalidades vencidas</h3>
            <p>
              Pague uma cobrança por vez. O acesso será conferido novamente após cada recebimento.
            </p>
            ${table(['Vencimento', 'Valor', ''], rows)}`
        : ''}`,
    null,
  );
}

export { contractModal, payModal, cancelContract, accessModal, monthlyAccess };
