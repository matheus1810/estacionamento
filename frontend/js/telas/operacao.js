// Consulta os dados e monta a tela de operacao.

import { all } from '../api.js';
import { state } from '../estado.js';
import { action, heading, badge, empty, table, rowAction } from '../ui/componentes.js';
import { icon } from '../ui/icones.js';
import { esc } from '../utils/dom.js';
import { localDate, localTime } from '../utils/formatacao.js';

async function operation() {
  const [vagas, abertas, contratos, veiculos, clientes] = await Promise.all([
    all('/vagas'),
    all('/permanencias?abertas=true'),
    all('/contratacoes'),
    all('/veiculos'),
    all('/clientes'),
  ]);
  Object.assign(state.cache, { vagas, abertas, contratos, veiculos, clientes });
  const livres = vagas.filter((v) => v.disponivel).length;
  const reservadas = vagas.filter((v) => v.ativa && v.motivo.includes('reservada')).length;
  const ativas = vagas.filter((v) => v.ativa).length;
  const uso = ativas ? Math.round(((abertas.length + reservadas) / ativas) * 100) : 0;
  const metric = (label, value, note, glyph, highlight = false) =>
    /* HTML */ `<article class="metric ${highlight ? 'highlight' : ''}">
      <span class="metric-label">${label}${icon(glyph)}</span>
      <div class="metric-value">${value}</div>
      <span class="metric-note">${note}</span>
    </article>`;
  const rows = abertas.map((p) => {
    const v = veiculos.find((v) => v.id === p.veiculo_id);
    const vaga = vagas.find((v) => v.id === p.vaga_id);
    return /* HTML */ `<tr data-stay-plate="${esc(v?.placa || '')}">
      <td>
        <span class="plate">${esc(v?.placa || '—')}</span>
        <div class="muted" style="font-size:9px;margin-top:5px">${esc(v?.modelo || '')}</div>
      </td>
      <td>${esc(vaga?.numero || p.vaga_id)}</td>
      <td>
        ${localTime(p.entrada)}
        <div class="muted" style="font-size:9px;margin-top:4px">${localDate(p.entrada)}</div>
      </td>
      <td>${badge('Em andamento')}</td>
      <td>${rowAction('Registrar saída ↗', 'exit', p.id)}</td>
    </tr>`;
  });
  const lots = vagas
    .slice(0, 24)
    .map((v) => {
      const cls = !v.ativa
        ? 'inactive'
        : v.disponivel
          ? ''
          : v.motivo.includes('reservada')
            ? 'reserved'
            : 'busy';
      const label = !v.ativa
        ? 'Inativa'
        : v.disponivel
          ? 'Livre'
          : cls === 'reserved'
            ? 'Mensalista'
            : 'Ocupada';
      return /* HTML */ `<button
        class="parking-space ${cls}"
        data-action="space-detail"
        data-id="${v.id}"
        aria-label="Vaga ${esc(v.numero)}, ${label}"
      >
        <span class="space-corner"></span>${icon(cls === 'reserved' ? 'lock' : 'car')}<strong
          >${esc(v.numero)}</strong
        ><small>${label}</small>
      </button>`;
    })
    .join('');
  return (
    heading(
      'SEU ESTACIONAMENTO EM TEMPO REAL',
      'Tudo sob controle.',
      'Acompanhe as vagas e mantenha a operação em movimento.',
      action('Consultar mensalista', 'access', 'search', true) +
        action('Registrar entrada', 'entry', 'plus'),
    ) +
    /* HTML */ `<section class="attendance-bar" aria-labelledby="attendance-title">
      <div>
        <span class="small-label">ATENDIMENTO RÁPIDO</span>
        <h2 id="attendance-title">Qual é a placa?</h2>
        <p>Entrada, saída ou mensalista. Comece por aqui.</p>
      </div>
      <form id="attendance-form">
        <label for="attendance-plate" class="sr-only">Placa para atendimento</label
        ><input
          id="attendance-plate"
          name="placa"
          placeholder="ABC1D23"
          maxlength="12"
          required
          autocomplete="off"
          spellcheck="false"
          aria-describedby="plate-hint"
        /><button class="button primary" type="submit">${icon('search')}Atender veículo</button
        ><small id="plate-hint"
          >7 caracteres: ABC1234 ou ABC1D23. Pressione Enter para consultar.
          <kbd>Alt</kbd> + <kbd>P</kbd> para focar.</small
        >
      </form>
    </section>` +
    /* HTML */ `<div class="metrics">
        ${metric(
          'Vagas disponíveis',
          livres,
          `de ${ativas} vagas ativas`,
          'parking',
          true,
        )}${metric(
          'Horistas no pátio',
          abertas.length,
          'Permanências em andamento',
          'car',
        )}${metric(
          'Vagas reservadas',
          reservadas,
          'Uso exclusivo de mensalistas',
          'calendar',
        )}${metric('Ocupação atual', `${uso}%`, 'Horistas + reservas mensais', 'grid')}
      </div>
      <div class="dashboard-columns">
        <div class="dashboard-main">
          <section class="panel">
            <div class="panel-header">
              <div>
                <h3>Mapa de vagas</h3>
                <p>Um olhar rápido para o seu pátio.</p>
              </div>
              ${badge('Agora')}
            </div>
            <div class="lot-legend">
              <span><i class="legend-dot"></i>Disponível</span
              ><span><i class="legend-dot busy"></i>Horista</span
              ><span><i class="legend-dot reserved"></i>Mensalista</span
              ><span><i class="legend-dot inactive"></i>Inativa</span>
            </div>
            ${vagas.length
              ? /* HTML */ `<div class="lot-grid">${lots}</div>`
              : empty(
                  'Vamos preparar o pátio?',
                  'Cadastre as vagas para visualizar a disponibilidade.',
                )}
            <div class="panel-foot">
              <span
                >${vagas.length} vagas
                cadastradas${vagas.length > 24 ? ' · exibindo as primeiras 24' : ''}</span
              ><a class="subtle" href="#vagas">Gerenciar vagas ↗</a>
            </div>
          </section>
          <section class="panel stays-panel">
            <div class="panel-header">
              <div>
                <h3>Horistas em andamento</h3>
                <p>Localize a placa e confirme a saída.</p>
              </div>
              <span class="badge gray">${abertas.length} no pátio</span>
            </div>
            ${abertas.length
              ? '<div class="stay-search"><label class="sr-only" for="stay-filter">Filtrar veículos no pátio</label><input id="stay-filter" type="search" placeholder="Filtrar placa no pátio…" autocomplete="off"><span id="stay-count" class="muted"></span></div>'
              : ''}${table(
              ['Veículo', 'Vaga', 'Entrada', 'Situação', ''],
              rows,
              'O pátio está tranquilo.',
              'Nenhum horista com permanência aberta.',
            )}
            <p id="stay-no-results" class="empty" hidden>Nenhuma placa corresponde à busca.</p>
          </section>
        </div>
        <div class="dashboard-side">
          <aside class="callout">
            <span class="small-label">ACESSO DE MENSALISTAS</span>
            <h3>Uma placa.<br />Uma consulta. Tudo certo.</h3>
            <p>Confira a reserva e as pendências antes de liberar o acesso.</p>
            ${action('Consultar placa', 'access', 'search', true)}
          </aside>
          <section class="panel">
            <div class="panel-header"><h3>Atalhos da operação</h3></div>
            <div class="quick-actions">
              ${[
                ['entry', 'car', 'Registrar entrada', 'Iniciar uma permanência horista'],
                ['new-client', 'users', 'Cadastrar cliente', 'Cliente e veículo, tudo organizado'],
                ['new-contract', 'calendar', 'Nova contratação', 'Reservar uma vaga mensal'],
              ]
                .map(
                  ([a, i, t, s]) =>
                    /* HTML */ `<button class="quick-action" data-action="${a}">
                      <span class="quick-icon">${icon(i)}</span
                      ><span><strong>${t}</strong><small>${s}</small></span
                      ><span class="arrow">↗</span>
                    </button>`,
                )
                .join('')}
            </div>
          </section>
          <section class="panel">
            <div class="panel-header">
              <div>
                <h3>Distribuição do pátio</h3>
                <p>Reservas contam como vagas em uso.</p>
              </div>
            </div>
            <div style="padding:0 24px 23px">
              <div style="display:flex;justify-content:space-between;font-size:11px">
                <span class="muted">Ocupação</span><strong>${uso}%</strong>
              </div>
              <div class="progress-track">
                <div class="progress-fill" style="width:${Math.min(100, uso)}%"></div>
              </div>
              <p style="font-size:10px;margin:12px 0 0;color:var(--muted)">
                ${livres} vagas livres para receber o próximo cliente.
              </p>
            </div>
          </section>
        </div>
      </div>`
  );
}

export { operation };
