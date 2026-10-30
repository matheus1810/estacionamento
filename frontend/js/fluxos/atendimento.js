// Atendimento pela placa: consulta, cadastro rápido, entrada e saída de horistas.

import { api, post, all } from '../api.js';
import { state } from '../estado.js';
import { monthlyAccess } from './mensalistas.js';
import { action } from '../ui/componentes.js';
import { complete } from './conclusao.js';
import { input, select, paymentSelect } from '../ui/formularios.js';
import { openModal, modalVersion } from '../ui/modal.js';
import { toast } from '../ui/notificacoes.js';
import { $, esc } from '../utils/dom.js';
import { money, localTime, timestamp, duration } from '../utils/formatacao.js';
import { refreshSearchableSelect } from '../ui/select-busca.js';
import { invoiceRequestFields, paymentPayload } from '../ui/nota-fiscal.js';

async function entryModal(vagaId, veiculoId) {
  const [vagas, veiculos, clientes] = await Promise.all([
    all('/vagas'),
    all('/veiculos'),
    all('/clientes'),
  ]);
  const validos = veiculos.filter((v) => clientes.some((c) => c.id === v.cliente_id && c.ativo));
  const livres = vagas.filter((v) => v.disponivel);
  if (!validos.length) {
    return plateModal(vagaId);
  }
  if (!livres.length) {
    toast('Nenhuma vaga disponível no momento.', true);
    return;
  }
  openModal(
    'Registrar entrada',
    /* HTML */ `<div class="form-stack">
        ${select(
          'veiculo_id',
          'Veículo / cliente',
          validos.map((v) => [
            v.id,
            `${v.placa} · ${v.modelo} · ${clientes.find((c) => c.id === v.cliente_id)?.nome}`,
          ]),
          veiculoId || '',
        )}${select(
          'vaga_id',
          'Vaga disponível',
          livres.map((v) => [v.id, `Vaga ${v.numero}`]),
          vagaId || livres[0].id,
        )}
      </div>
      <p class="muted" style="font-size:11px;margin-top:20px">
        O horário e a tarifa são registrados na confirmação. A disponibilidade será conferida
        novamente.
      </p>`,
    async (values) => {
      const p = await post('/permanencias', {
        veiculo_id: Number(values.veiculo_id),
        vaga_id: Number(values.vaga_id),
      });
      const v = validos.find((v) => v.id === Number(values.veiculo_id));
      const vaga =
        livres.find((v) => v.id === p.vaga_id) ||
        state.cache.vagas?.find((v) => v.id === p.vaga_id);
      await complete(`Entrada registrada: ${v.placa} · vaga ${vaga?.numero || p.vaga_id}.`);
    },
    'Confirmar entrada',
  );
  $('#modal-body').insertAdjacentHTML(
    'beforeend',
    action('Atualizar vagas livres', 'refresh-entry-spaces', 'refresh', true),
  );
}

async function exitModal(id, atendimento = null) {
  const previa = await api(`/permanencias/${id}/previa`);
  const p = atendimento?.permanencia || state.cache.abertas?.find((p) => p.id === id);
  const veiculo = atendimento?.veiculo || state.cache.veiculos?.find((v) => v.id === p?.veiculo_id);
  const vaga = state.cache.vagas?.find((v) => v.id === p?.vaga_id);
  openModal(
    'Registrar saída',
    /* HTML */ `<p>Confira o valor e selecione como o cliente vai pagar.</p>
      <dl class="details">
        <div>
          <dt>Veículo</dt>
          <dd>${veiculo ? esc(veiculo.placa) : `Permanência #${id}`}</dd>
        </div>
        ${p
          ? /* HTML */ `<div>
                <dt>Vaga</dt>
                <dd>${esc(vaga?.numero || p.vaga_id)}</dd>
              </div>
              <div>
                <dt>Entrada</dt>
                <dd>${timestamp(p.entrada)}</dd>
              </div>
              <div>
                <dt>Tempo decorrido</dt>
                <dd>${duration(p.entrada, previa.calculado_em)}</dd>
              </div>`
          : ''}
        <div>
          <dt>Blocos de 30 minutos</dt>
          <dd>${previa.blocos}</dd>
        </div>
        <div>
          <dt>Prévia calculada às</dt>
          <dd>${localTime(previa.calculado_em)}</dd>
        </div>
      </dl>
      <div class="total"><span>Valor previsto</span><strong>${money(previa.valor)}</strong></div>
      ${paymentSelect()} ${invoiceRequestFields()}
      <p style="font-size:10px;margin-top:16px">
        O valor será recalculado ao confirmar. A confirmação encerra a permanência e registra o
        pagamento integral.
      </p>`,
    async (values) => {
      const cobranca = await post(`/permanencias/${id}/saida`, paymentPayload(values));
      await complete(
        `Saída registrada${veiculo ? ': ' + veiculo.placa : ''}. Pagamento de ${money(cobranca.valor)} confirmado.` +
          (cobranca.nota_fiscal_solicitada
            ? ' Solicitação de nota fiscal salva para emissão posterior.'
            : ''),
      );
    },
    'Confirmar saída e pagamento',
  );
}

function plateModal(vagaId, placa = '') {
  openModal(
    'Atender veículo',
    /* HTML */ `<p>Informe a placa para encontrar a próxima ação.</p>
      ${input('placa', 'Placa do veículo', 'text', placa, {
        required: true,
        maxlength: 12,
        placeholder: 'ABC1D23',
        autocomplete: 'off',
        spellcheck: 'false',
        'aria-describedby': 'plate-format-hint modal-error',
      })}
      <p id="plate-format-hint" class="plate-format-hint">
        Use 7 caracteres: ABC1234 (placa antiga) ou ABC1D23 (Mercosul). Espaços e hífens são
        desconsiderados.
      </p>`,
    (values) => consultPlate(values.placa, vagaId),
    'Consultar placa',
  );
}

async function consultPlate(value, vagaId) {
  const placa = value.replace(/[\s-]/g, '').toUpperCase();
  const field = $('#modal[open] input[name="placa"]') || $('#attendance-plate');
  if (!/^[A-Z]{3}(?:\d{4}|\d[A-Z]\d{2})$/.test(placa)) {
    const message =
      placa.length !== 7
        ? `Você digitou ${placa.length} caracteres. A placa deve ter 7, sem contar espaços ou hífens. Confira a digitação. Exemplos: ABC1234 ou ABC1D23.`
        : 'O formato da placa não foi reconhecido. Use ABC1234 (3 letras e 4 números) ou ABC1D23 (Mercosul).';
    field?.setAttribute('aria-invalid', 'true');
    field?.focus();
    throw new Error(message);
  }
  field?.removeAttribute('aria-invalid');
  openModal(
    'Consultando placa',
    /* HTML */ `<div class="loading" role="status">
      <span class="spinner"></span>Localizando ${esc(placa)}…
    </div>`,
    null,
  );
  const version = modalVersion;
  try {
    let veiculo;
    try {
      veiculo = await api('/veiculos/placa/' + encodeURIComponent(placa));
    } catch (error) {
      if (version !== modalVersion) return;
      if (error.status === 404) {
        await quickRegistrationModal(placa, vagaId);
        return;
      }
      throw error;
    }
    const [cliente, abertas, contratos] = await Promise.all([
      api('/clientes/' + veiculo.cliente_id),
      all('/permanencias?abertas=true&veiculo_id=' + veiculo.id),
      all('/contratacoes?vigentes=true&cliente_id=' + veiculo.cliente_id),
    ]);
    if (version !== modalVersion || !state.user) return;
    const permanencia = abertas.find((p) => p.veiculo_id === veiculo.id);
    state.atendimento = { placa, cliente, veiculo, permanencia };
    if (permanencia) {
      await exitModal(permanencia.id, state.atendimento);
      return;
    }
    if (!cliente.ativo) {
      openModal(
        'Cliente inativo',
        /* HTML */ `<p>
          ${esc(cliente.nome)} está inativo. Reative o cadastro em Clientes para registrar uma nova
          entrada.
        </p>`,
        null,
      );
      return;
    }
    if (contratos.length) {
      await monthlyAccess(placa);
      return;
    }
    await entryModal(vagaId, veiculo.id);
  } catch (error) {
    if (version !== modalVersion || !state.user) return;
    plateModal(vagaId, placa);
    $('#modal-error').textContent = error.message;
    $('#modal-error').hidden = false;
  }
}

async function quickRegistrationModal(placa, vagaId) {
  const [clientes, vagas] = await Promise.all([all('/clientes'), all('/vagas')]);
  const livres = vagas.filter((v) => v.disponivel);
  if (!livres.length) {
    openModal(
      'Sem vaga disponível',
      /* HTML */ `<p>
        A placa ${esc(placa)} ainda não está cadastrada. Não há vaga livre para concluir a entrada
        agora.
      </p>`,
      null,
    );
    return;
  }
  openModal(
    'Cadastrar e registrar entrada',
    /* HTML */ `<div class="notice">
        Placa não cadastrada. Preencha os dados uma vez e confirme a entrada aqui mesmo.
      </div>
      <div class="form-grid">
        ${input('placa', 'Placa', 'text', placa, { required: true, maxlength: 12 })}${select(
          'vaga_id',
          'Vaga disponível',
          livres.map((v) => [v.id, 'Vaga ' + v.numero]),
          vagaId || livres[0].id,
        )}${input('modelo', 'Modelo', 'text', '', { required: true, maxlength: 80 })}${input(
          'cor',
          'Cor',
          'text',
          '',
          { required: true, maxlength: 30 },
        )}
        <div class="full">
          <label
            >Responsável<select
              name="responsavel"
              id="quick-client"
              aria-label="Responsável"
              data-searchable
            >
              <option value="novo">Cadastrar novo cliente</option>
              ${clientes
                .filter((c) => c.ativo)
                .map(
                  (c) =>
                    /* HTML */ `<option value="${c.id}">
                      ${esc(c.nome)} · ${esc(c.telefone)}
                    </option>`,
                )
                .join('')}
            </select></label
          >
        </div>
        <div id="quick-client-fields" class="form-grid full">
          ${input('nome', 'Nome do cliente', 'text', '', {
            required: true,
            maxlength: 120,
          })}${input('telefone', 'Telefone', 'tel', '', { required: true, maxlength: 20 })}
        </div>
      </div>
      <p class="muted" style="font-size:10px;margin-top:18px">
        Cliente, veículo e entrada são salvos juntos. Se houver conflito, os dados continuam nesta
        tela para correção.
      </p>`,
    async (values) => {
      const body = {
        placa: values.placa,
        modelo: values.modelo,
        cor: values.cor,
        vaga_id: Number(values.vaga_id),
        ...(values.responsavel === 'novo'
          ? { cliente: { nome: values.nome.trim(), telefone: values.telefone.trim() } }
          : { cliente_id: Number(values.responsavel) }),
      };
      const p = await post('/permanencias/cadastro-entrada', body);
      const vaga =
        livres.find((v) => v.id === p.vaga_id) ||
        state.cache.vagas?.find((v) => v.id === p.vaga_id);
      await complete(
        `Entrada registrada: ${values.placa.replace(/[\s-]/g, '').toUpperCase()} · vaga ${vaga?.numero || p.vaga_id}. Cadastro concluído.`,
      );
    },
    'Cadastrar e confirmar entrada',
  );
  // A placa já foi digitada no atendimento; começa pelo modelo.
  $('#modal-body input[name="modelo"]').focus();
  $('#modal-body').insertAdjacentHTML(
    'beforeend',
    action('Atualizar vagas livres', 'refresh-entry-spaces', 'refresh', true),
  );
}

async function refreshEntrySpaces() {
  const version = modalVersion;
  const vagas = await all('/vagas');
  const livres = vagas.filter((v) => v.disponivel);
  if (version !== modalVersion) return;
  state.cache.vagas = vagas;
  const field = $('#modal-body select[name="vaga_id"]');
  if (!field) return;
  const previous = field.value;
  field.innerHTML =
    '<option value="">Selecione…</option>' +
    livres.map((v) => /* HTML */ `<option value="${v.id}">Vaga ${esc(v.numero)}</option>`).join('');
  if (livres.some((v) => String(v.id) === previous)) field.value = previous;
  $('#modal-error').hidden = true;
  toast(
    livres.length
      ? 'Vagas atualizadas. Confira a seleção antes de confirmar.'
      : 'Nenhuma vaga livre. Seus dados continuam preenchidos.',
    !livres.length,
  );
  refreshSearchableSelect(field).focus();
}

async function spaceDetail(id) {
  const v = state.cache.vagas?.find((v) => v.id === id);
  if (v.disponivel) return entryModal(id);
  const p = state.cache.abertas?.find((p) => p.vaga_id === id);
  if (p) return exitModal(p.id);
  openModal(
    `Vaga ${v.numero}`,
    /* HTML */ `<p>${esc(v.motivo)}</p>
      <div class="notice">
        Vagas de mensalistas permanecem reservadas mesmo quando estão vazias. O controle de presença
        é manual.
      </div>`,
    null,
  );
}

export { entryModal, exitModal, plateModal, consultPlate, refreshEntrySpaces, spaceDetail };
