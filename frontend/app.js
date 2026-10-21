'use strict';

// Interface sem dependências. O backend decide horários, valores e disponibilidade.
const $ = (selector, root = document) => root.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = value => new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'}).format(Number(value));
const localDate = value => value ? value.split('T')[0].split('-').reverse().join('/') : 'Sem encerramento';
const localTime = value => value ? value.slice(11,16) : '—';
const timestamp = value => value ? `${localDate(value)} às ${localTime(value)}` : '—';
const today = () => new Intl.DateTimeFormat('en-CA', {timeZone:'America/Sao_Paulo', year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const paths = {
  grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/><circle cx="9" cy="7" r="4"/>',
  car:'<path d="m5 7 2-4h10l2 4m-16 3 2-3h14l2 3v8H3Zm2 8v3m14-3v3M3 12h18"/><path d="M6 15h2m8 0h2"/>',
  parking:'<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M9 17V7h4a3 3 0 0 1 0 6H9"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18m-13 4h2m4 0h2"/>',
  receipt:'<path d="M5 3h14v19l-3-2-4 2-4-2-3 2ZM9 7h6m-6 4h6m-6 4h3"/>',
  sliders:'<path d="M4 6h6m4 0h6M4 12h12m4 0h0M4 18h2m4 0h10"/><circle cx="12" cy="6" r="2"/><circle cx="18" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
  shield:'<path d="m12 3 8 4v6c0 5-8 9-8 9s-8-4-8-9V7Zm-4 9 3 3 5-6"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  search:'<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  refresh:'<path d="M20 7v5h-5M4 17v-5h5m-4-3a7 7 0 0 1 12-5l3 3M4 17l3 3a7 7 0 0 0 12-5"/>',
  lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3"/>',
};
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.grid}</svg>`;
const nav = [
  ['operacao','Visão geral','grid'], ['clientes','Clientes','users'], ['veiculos','Veículos','car'],
  ['vagas','Vagas','parking'], ['mensalistas','Mensalistas','calendar'], ['cobrancas','Cobranças','receipt'],
  ['tarifas','Tarifas','sliders'], ['usuarios','Operadores','shield'],
];
const state = {user:null, page:'operacao', offset:0, limit:20, query:'', filter:'', cache:{}, renderId:0};
let token = sessionStorage.getItem('mationamento_token');
let modalHandler = null;
let modalVersion = 0;

function toast(message, error = false) {
  const item = document.createElement('div');
  item.className = 'toast' + (error ? ' error' : '');
  item.textContent = message;
  $('#toast-container').append(item);
  setTimeout(() => item.remove(), error ? 8500 : 4500);
}

async function api(path, options = {}) {
  const headers = {'Content-Type':'application/json', ...options.headers};
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try { response = await fetch(path, {...options, headers}); }
  catch { throw new Error('Não foi possível conectar. Confira se o servidor está em execução.'); }
  const data = await response.json().catch(() => ({}));
  if (response.status === 401 && path !== '/auth/login') {
    logout();
    throw new Error('Sua sessão terminou. Entre novamente.');
  }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Confira os dados informados.');
  return data;
}
const post = (path, body) => api(path, {method:'POST', ...(body !== undefined ? {body:JSON.stringify(body)} : {})});
const patch = (path, body) => api(path, {method:'PATCH', body:JSON.stringify(body)});

async function all(path) {
  const result = [];
  for (let offset = 0; ; offset += 100) {
    const rows = await api(`${path}${path.includes('?') ? '&' : '?'}offset=${offset}&limite=100`);
    result.push(...rows);
    if (rows.length < 100) return result;
  }
}

function logout() {
  token = null;
  sessionStorage.removeItem('mationamento_token');
  state.user = null;
  state.cache = {};
  state.renderId++;
  closeModal();
  $('#app-view').hidden = true;
  $('#login-view').hidden = false;
  $('#login-form').reset();
}

function showApp(user) {
  state.user = user;
  $('#login-view').hidden = true;
  $('#app-view').hidden = false;
  $('#user-name').textContent = user.nome;
  $('#avatar').textContent = user.nome.split(/\s+/).slice(0,2).map(v => v[0]).join('').toUpperCase();
  $('#navigation').innerHTML = nav.map(([id,name,glyph],i) => `${i === 6 ? '<div class="nav-separator"></div>' : ''}<a class="nav-link" href="#${id}" data-page="${id}">${icon(glyph)}<span>${name}</span></a>`).join('');
  navigate();
}

function tick() {
  const now = new Date();
  $('#clock').textContent = new Intl.DateTimeFormat('pt-BR', {timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit'}).format(now);
  $('#sidebar-date').textContent = new Intl.DateTimeFormat('pt-BR', {timeZone:'America/Sao_Paulo',day:'numeric',month:'long',year:'numeric'}).format(now);
}

function navigate() {
  if (!state.user) return;
  const page = location.hash.slice(1);
  state.page = nav.some(v => v[0] === page) ? page : 'operacao';
  state.offset = 0; state.query = ''; state.filter = '';
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === state.page);
    if (a.dataset.page === state.page) a.setAttribute('aria-current','page');
    else a.removeAttribute('aria-current');
  });
  $('#breadcrumb').textContent = nav.find(v => v[0] === state.page)[1];
  $('#sidebar').classList.remove('open');
  $('#menu-toggle').setAttribute('aria-expanded','false');
  closeModal();
  render();
}

function action(label, type, glyph = '', secondary = false, data = '') {
  return `<button class="button ${secondary ? 'secondary' : 'primary'}" data-action="${type}" ${data}>${glyph ? icon(glyph) : ''}${label}</button>`;
}
function heading(kicker, title, subtitle, buttons = '') {
  return `<section class="page-heading"><div><span class="small-label">${esc(kicker)}</span><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div><div class="heading-actions">${buttons}</div></section>`;
}
const badge = (label, color = 'green') => `<span class="badge ${color}">${esc(label)}</span>`;
function empty(title, subtitle, glyph = 'parking') {
  return `<div class="empty">${icon(glyph)}<strong>${esc(title)}</strong>${esc(subtitle)}</div>`;
}
function table(headers, rows, noTitle = 'Nenhum registro por aqui.', noSubtitle = 'Os registros aparecerão aqui após o cadastro.') {
  if (!rows.length) return empty(noTitle,noSubtitle);
  return `<div class="table-scroll"><table><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
}
function pagination(count) {
  return `<div class="pagination"><span>${count ? `${state.offset + 1}–${state.offset + count}` : '0'} registros nesta página</span><button class="button secondary" data-action="previous" ${state.offset === 0 ? 'disabled' : ''}>← Anterior</button><button class="button secondary" data-action="next" ${count < state.limit ? 'disabled' : ''}>Próxima →</button></div>`;
}
function rowAction(label, actionName, id, danger = false) {
  return `<button class="subtle" ${danger ? 'style="color:var(--red)"' : ''} data-action="${actionName}" data-id="${id}">${label}</button>`;
}
function toolbar(searchPlaceholder = '', filters = '') {
  return `<div class="toolbar">${searchPlaceholder ? `<form id="search-form" class="search-form"><input name="search" aria-label="${esc(searchPlaceholder)}" placeholder="${esc(searchPlaceholder)}" value="${esc(state.query)}" maxlength="120"><button class="button secondary" type="submit" aria-label="Buscar">${icon('search')}</button></form>` : '<span class="toolbar-label">CADASTROS DO ESTACIONAMENTO</span>'}${filters}</div>`;
}
function selectFilter(options, label) {
  return `<select id="list-filter" aria-label="${esc(label)}">${options.map(([value,name]) => `<option value="${esc(value)}" ${state.filter===value?'selected':''}>${esc(name)}</option>`).join('')}</select>`;
}
function queryParams(extra = {}) {
  const params = new URLSearchParams({offset:state.offset,limite:state.limit,...extra});
  return params.toString();
}

async function render() {
  const renderId = ++state.renderId;
  $('#main').innerHTML = '<div class="loading" role="status"><span class="spinner"></span>Carregando seu estacionamento…</div>';
  try {
    const html = await ({operacao:operation,clientes:clients,veiculos:vehicles,vagas:spaces,mensalistas:contracts,cobrancas:charges,tarifas:rates,usuarios:operators}[state.page])();
    if (renderId !== state.renderId || !state.user) return;
    $('#main').innerHTML = html;
  } catch (error) {
    if (renderId !== state.renderId || !state.user) return;
    $('#main').innerHTML = `<div class="error-panel"><h2>Não foi possível carregar os dados.</h2><p>${esc(error.message)}</p>${action('Tentar novamente','refresh','refresh')}</div>`;
  }
}

async function operation() {
  const [vagas, abertas, contratos, veiculos, clientes] = await Promise.all([
    all('/vagas'), all('/permanencias?abertas=true'), all('/contratacoes'), all('/veiculos'), all('/clientes'),
  ]);
  Object.assign(state.cache,{vagas,abertas,contratos,veiculos,clientes});
  const livres = vagas.filter(v=>v.disponivel).length;
  const reservadas = vagas.filter(v=>v.ativa && v.motivo.includes('reservada')).length;
  const ativas = vagas.filter(v=>v.ativa).length;
  const uso = ativas ? Math.round((abertas.length + reservadas)/ativas*100) : 0;
  const metric = (label,value,note,glyph,highlight=false) => `<article class="metric ${highlight?'highlight':''}"><span class="metric-label">${label}${icon(glyph)}</span><div class="metric-value">${value}</div><span class="metric-note">${note}</span></article>`;
  const rows = abertas.slice(0,6).map(p => {
    const v = veiculos.find(v=>v.id===p.veiculo_id);
    const vaga = vagas.find(v=>v.id===p.vaga_id);
    return `<tr><td><span class="plate">${esc(v?.placa||'—')}</span></td><td>${esc(vaga?.numero||p.vaga_id)}</td><td>${localTime(p.entrada)}<div class="muted" style="font-size:9px;margin-top:4px">${localDate(p.entrada)}</div></td><td>${badge('Em andamento')}</td><td>${rowAction('Registrar saída ↗','exit',p.id)}</td></tr>`;
  });
  const lots = vagas.slice(0,24).map(v=>{
    const cls = !v.ativa ? 'inactive' : v.disponivel ? '' : v.motivo.includes('reservada') ? 'reserved' : 'busy';
    const label = !v.ativa ? 'Inativa' : v.disponivel ? 'Livre' : cls==='reserved' ? 'Mensalista' : 'Ocupada';
    return `<button class="parking-space ${cls}" data-action="space-detail" data-id="${v.id}" aria-label="Vaga ${esc(v.numero)}, ${label}"><span class="space-corner"></span>${icon(cls==='reserved'?'lock':'car')}<strong>${esc(v.numero)}</strong><small>${label}</small></button>`;
  }).join('');
  return heading('SEU ESTACIONAMENTO EM TEMPO REAL','Tudo sob controle.','Acompanhe as vagas e mantenha a operação em movimento.',
    action('Consultar mensalista','access','search',true)+action('Registrar entrada','entry','plus')) +
    `<div class="metrics">${metric('Vagas disponíveis',livres,`de ${ativas} vagas ativas`,'parking',true)}${metric('Horistas no pátio',abertas.length,'Permanências em andamento','car')}${metric('Vagas reservadas',reservadas,'Uso exclusivo de mensalistas','calendar')}${metric('Ocupação atual',`${uso}%`,'Horistas + reservas mensais','grid')}</div>
    <div class="dashboard-columns"><div class="dashboard-main"><section class="panel"><div class="panel-header"><div><h3>Mapa de vagas</h3><p>Um olhar rápido para o seu pátio.</p></div>${badge('Agora')}</div><div class="lot-legend"><span><i class="legend-dot"></i>Disponível</span><span><i class="legend-dot busy"></i>Horista</span><span><i class="legend-dot reserved"></i>Mensalista</span><span><i class="legend-dot inactive"></i>Inativa</span></div>${vagas.length ? `<div class="lot-grid">${lots}</div>` : empty('Vamos preparar o pátio?','Cadastre as vagas para visualizar a disponibilidade.')}
    <div class="panel-foot"><span>${vagas.length} vagas cadastradas${vagas.length>24?' · exibindo as primeiras 24':''}</span><a class="subtle" href="#vagas">Gerenciar vagas ↗</a></div></section>
    <section class="panel"><div class="panel-header"><div><h3>Horistas em andamento</h3><p>Entrada registrada. Saída quando o cliente precisar.</p></div><span class="badge gray">${abertas.length} no pátio</span></div>${table(['Veículo','Vaga','Entrada','Situação',''],rows,'O pátio está tranquilo.','Nenhum horista com permanência aberta.')}${abertas.length>6?`<div class="panel-foot"><span>Mostrando 6 de ${abertas.length}</span>${action('Ver todas','open-stays','car',true)}</div>`:''}</section></div>
    <div class="dashboard-side"><aside class="callout"><span class="small-label">ACESSO DE MENSALISTAS</span><h3>Uma placa.<br>Uma consulta. Tudo certo.</h3><p>Confira a reserva e as pendências antes de liberar o acesso.</p>${action('Consultar placa','access','search',true)}</aside>
    <section class="panel"><div class="panel-header"><h3>Atalhos da operação</h3></div><div class="quick-actions">${[['entry','car','Registrar entrada','Iniciar uma permanência horista'],['new-client','users','Cadastrar cliente','Cliente e veículo, tudo organizado'],['new-contract','calendar','Nova contratação','Reservar uma vaga mensal']].map(([a,i,t,s])=>`<button class="quick-action" data-action="${a}"><span class="quick-icon">${icon(i)}</span><span><strong>${t}</strong><small>${s}</small></span><span class="arrow">↗</span></button>`).join('')}</div></section>
    <section class="panel"><div class="panel-header"><div><h3>Distribuição do pátio</h3><p>Reservas contam como vagas em uso.</p></div></div><div style="padding:0 24px 23px"><div style="display:flex;justify-content:space-between;font-size:11px"><span class="muted">Ocupação</span><strong>${uso}%</strong></div><div class="progress-track"><div class="progress-fill" style="width:${Math.min(100,uso)}%"></div></div><p style="font-size:10px;margin:12px 0 0;color:var(--muted)">${livres} vagas livres para receber o próximo cliente.</p></div></section></div></div>`;
}

async function clients() {
  const params = {...(state.query ? {nome:state.query}:{}),...(state.filter ? {ativo:state.filter}:{})};
  const rows = await api('/clientes?' + queryParams(params)); state.cache.rows = rows;
  return heading('CADASTROS','Clientes','Pessoas, contatos e um histórico preservado.',action('Novo cliente','new-client','plus'))+
    `<section class="panel">${toolbar('Buscar cliente por nome',selectFilter([['','Todos os clientes'],['true','Ativos'],['false','Inativos']],'Situação do cliente'))}${table(['Nome','Telefone','Situação','Cadastro','Ações'],rows.map(c=>`<tr><td><strong>${esc(c.nome)}</strong></td><td>${esc(c.telefone)}</td><td>${badge(c.ativo?'Ativo':'Inativo',c.ativo?'green':'gray')}</td><td>${localDate(c.criado_em)}</td><td><div class="table-actions">${rowAction('Editar','edit-client',c.id)}${rowAction('Veículos','client-vehicles',c.id)}</div></td></tr>`))}${pagination(rows.length)}</section>`;
}

async function vehicles() {
  const clientes = await all('/clientes'); state.cache.clientes = clientes;
  let rows;
  if (state.query) {
    try { rows = [await api('/veiculos/placa/'+encodeURIComponent(state.query))]; }
    catch (e) { if (e.message==='Veículo não encontrado.') rows=[]; else throw e; }
  } else rows = await api('/veiculos?' + queryParams(state.filter?{cliente_id:state.filter}:{}));
  state.cache.rows = rows;
  return heading('CADASTROS','Veículos','Cada placa conectada ao seu cliente.',action('Novo veículo','new-vehicle','plus'))+
    `<section class="panel">${toolbar('Buscar pela placa completa',selectFilter([['','Todos os clientes'],...clientes.map(c=>[String(c.id),c.nome])],'Filtrar por cliente'))}${table(['Placa','Modelo','Cor','Cliente',''],rows.map(v=>`<tr><td><span class="plate">${esc(v.placa)}</span></td><td>${esc(v.modelo)}</td><td>${esc(v.cor)}</td><td>${esc(clientes.find(c=>c.id===v.cliente_id)?.nome||v.cliente_id)}</td><td>${rowAction('Editar','edit-vehicle',v.id)}</td></tr>`))}${!state.query?pagination(rows.length):''}</section>`;
}

async function spaces() {
  const rows = await api('/vagas?' + queryParams()); state.cache.rows = rows;
  return heading('ORGANIZAÇÃO DO PÁTIO','Vagas','Disponibilidade calculada a partir das permanências e reservas.',action('Nova vaga','new-space','plus'))+
    `<section class="panel"><div class="panel-header"><h3>Vagas do estacionamento</h3><span class="muted" style="font-size:10px">Situação atual</span></div>${table(['Vaga','Cadastro','Disponibilidade','Ações'],rows.map(v=>`<tr><td><strong>${esc(v.numero)}</strong></td><td>${badge(v.ativa?'Ativa':'Inativa',v.ativa?'green':'gray')}</td><td>${badge(v.disponivel?'Disponível':v.motivo.replace('Vaga ','').replace('.',''),v.disponivel?'green':!v.ativa?'gray':'amber')}</td><td>${rowAction('Editar','edit-space',v.id)}</td></tr>`))}${pagination(rows.length)}</section>`;
}

async function contracts() {
  const [rows, clientes, vagas] = await Promise.all([api('/contratacoes?'+queryParams()),all('/clientes'),all('/vagas')]);
  Object.assign(state.cache,{rows,clientes,vagas});
  return heading('RESERVAS EXCLUSIVAS','Mensalistas','Uma contratação por vaga. O cliente pode alternar seus veículos.',action('Consultar placa','access','search',true)+action('Nova contratação','new-contract','plus'))+
    `<div class="notice">Mensalidade antecipada e integral por vaga. O atraso bloqueia o acesso e mantém a reserva. A presença dos veículos é controlada manualmente.</div><section class="panel">${table(['Cliente','Vaga','Início','Fim da reserva','Situação',''],rows.map(c=>{
      const encerrada = c.data_fim && c.data_fim<today();
      const futura = c.data_inicio>today();
      return `<tr><td><strong>${esc(clientes.find(v=>v.id===c.cliente_id)?.nome||c.cliente_id)}</strong></td><td>${esc(vagas.find(v=>v.id===c.vaga_id)?.numero||c.vaga_id)}</td><td>${localDate(c.data_inicio)}</td><td>${c.data_fim?localDate(c.data_fim):'Sem encerramento'}</td><td>${badge(encerrada?'Encerrada':futura?'Agendada':c.data_fim?'Encerramento programado':'Vigente',encerrada?'gray':futura?'amber':'green')}</td><td>${!encerrada&&!futura?rowAction('Cancelar renovação','cancel-contract',c.id,true):'—'}</td></tr>`;
    }))}${pagination(rows.length)}</section>`;
}

async function charges() {
  // POST explícito antes de listar, como exige a regra de geração sem agendador.
  await post('/cobrancas/atualizar-mensalidades');
  const [rows, contratos, clientes, vagas] = await Promise.all([
    api('/cobrancas?'+queryParams(state.filter?{pendentes:state.filter}:{})),all('/contratacoes'),all('/clientes'),all('/vagas'),
  ]);
  Object.assign(state.cache,{rows,contratos,clientes,vagas});
  return heading('CONTROLE DE RECEBIMENTOS','Cobranças','Mensalidades atualizadas ao abrir esta tela. Valores antigos são preservados.',action('Atualizar mensalidades','refresh','refresh',true))+
    `<section class="panel">${toolbar('',selectFilter([['','Todas as cobranças'],['true','Pendentes'],['false','Pagas']],'Situação do pagamento'))}${table(['Origem / cliente','Vencimento','Valor','Situação','Pagamento',''],rows.map(c=>{
      const contrato = contratos.find(v=>v.id===c.contratacao_mensal_id);
      const cliente = contrato ? clientes.find(v=>v.id===contrato.cliente_id) : null;
      const vaga = contrato ? vagas.find(v=>v.id===contrato.vaga_id) : null;
      const status = c.pago_em?'Paga':c.vencimento<today()?'Vencida':'Pendente';
      return `<tr><td><strong>${contrato?esc(cliente?.nome||'Mensalista'):`Horista · permanência #${c.permanencia_id}`}</strong><div class="muted" style="font-size:9px;margin-top:5px">${contrato?`Vaga ${esc(vaga?.numero||contrato.vaga_id)} · competência ${c.competencia.slice(0,7).split('-').reverse().join('/')}`:'Pagamento na saída'}</div></td><td>${localDate(c.vencimento)}</td><td><strong>${money(c.valor)}</strong></td><td>${badge(status,status==='Paga'?'green':status==='Vencida'?'red':'amber')}</td><td>${c.pago_em?`${esc(c.forma_pagamento)}<div class="muted" style="font-size:9px;margin-top:4px">${localDate(c.pago_em)}</div>`:'—'}</td><td>${!c.pago_em&&contrato?rowAction('Receber','pay-charge',c.id):'—'}</td></tr>`;
    }))}${pagination(rows.length)}</section>`;
}

async function rates() {
  let tarifa;
  try { tarifa = await api('/tarifas'); }
  catch (error) { if (error.message==='Registro não encontrado.') tarifa=null; else throw error; }
  state.cache.tarifa = tarifa;
  return heading('CONFIGURAÇÃO','Tarifas','Preços gerais para novas permanências e novas mensalidades.')+
    `<section class="panel settings-card"><h3>${tarifa?'Tarifas do estacionamento':'Configure seus primeiros valores'}</h3><p class="muted" style="font-size:12px;margin-top:8px">${tarifa?'Atualize os valores quando precisar. O histórico fica preservado.':'Nenhum preço é definido automaticamente.'}</p><form id="rates-form"><div class="form-grid">${input('valor_hora','Valor por hora (R$)','number',tarifa?.valor_hora||'',{min:'0.01',max:'99999999.99',step:'.01',required:true})}${input('valor_mensal_vaga','Mensalidade por vaga (R$)','number',tarifa?.valor_mensal_vaga||'',{min:'0.01',max:'99999999.99',step:'.01',required:true})}</div><button class="button primary" type="submit">${icon('check')}${tarifa?'Salvar tarifas':'Cadastrar tarifas'}</button></form><div class="notice">Horistas são cobrados em blocos de 30 minutos, arredondados para cima, com mínimo de um bloco. A tarifa da entrada vale até a saída.</div>${tarifa?`<p class="muted" style="font-size:10px;margin:18px 0 0">Último registro: ${timestamp(tarifa.atualizado_em||tarifa.criado_em)}</p>`:''}</section>`;
}

async function operators() {
  const rows = await api('/usuarios?' + queryParams()); state.cache.rows = rows;
  return heading('ACESSO AO SISTEMA','Operadores','Todos os operadores possuem as mesmas permissões.',action('Novo operador','new-user','plus'))+
    `<section class="panel">${table(['Nome','Login','Situação','Cadastro',''],rows.map(u=>`<tr><td><strong>${esc(u.nome)}</strong>${u.id===state.user.id?' <span class="muted">(você)</span>':''}</td><td>${esc(u.login)}</td><td>${badge(u.ativo?'Ativo':'Inativo',u.ativo?'green':'gray')}</td><td>${localDate(u.criado_em)}</td><td>${rowAction('Editar','edit-user',u.id)}</td></tr>`))}${pagination(rows.length)}</section>`;
}

function input(name, label, type = 'text', value = '', attributes = {}) {
  const attrs = Object.entries(attributes).map(([k,v])=>v===true?k:`${k}="${esc(v)}"`).join(' ');
  return `<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${attrs}></label>`;
}
function select(name, label, options, value = '', required = true) {
  return `<label>${label}<select name="${name}" aria-label="${esc(label)}" ${required?'required':''}><option value="">Selecione…</option>${options.map(([id,title])=>`<option value="${esc(id)}" ${String(id)===String(value)?'selected':''}>${esc(title)}</option>`).join('')}</select></label>`;
}
const activeSelect = (label, value, name='ativo') => select(name,label,[['true','Ativo'],['false','Inativo']],String(value));
const paymentSelect = () => select('forma_pagamento','Forma de pagamento',[['pix','Pix'],['dinheiro','Dinheiro'],['cartao','Cartão']]);

function openModal(title, body, handler, button = 'Salvar') {
  modalVersion++;
  $('#modal-title').textContent = title;
  $('#modal-body').innerHTML = body;
  $('#modal-error').hidden = true;
  $('#modal-submit').textContent = button;
  $('#modal-submit').disabled = !handler;
  $('#modal-submit').hidden = !handler;
  $('#modal-cancel').textContent = handler ? 'Cancelar' : 'Fechar';
  modalHandler = handler;
  if (!$('#modal').open) $('#modal').showModal();
}
function closeModal() {
  $('#modal').close(); modalHandler=null; modalVersion++;
}
async function complete(message) { closeModal(); toast(message); await render(); }

async function clientModal(id) {
  const c = id ? state.cache.rows?.find(v=>v.id===id) : null;
  openModal(c?'Editar cliente':'Novo cliente',`<div class="form-stack">${input('nome','Nome completo','text',c?.nome||'',{required:true,maxlength:120})}${input('telefone','Telefone','tel',c?.telefone||'',{required:true,maxlength:20})}${c?activeSelect('Situação',c.ativo):''}</div>`,async values=>{
    const body = {nome:values.nome.trim(),telefone:values.telefone.trim(),...(c?{ativo:values.ativo==='true'}:{})};
    if (c) await patch('/clientes/'+c.id,body); else await post('/clientes',body);
    await complete(c?'Cliente atualizado.':'Cliente cadastrado. Cadastre o veículo na tela Veículos.');
  });
}

async function vehicleModal(id) {
  const c = id ? state.cache.rows?.find(v=>v.id===id) : null;
  const clientes = await all('/clientes');
  if (!clientes.length) { toast('Cadastre um cliente antes do veículo.',true); return; }
  openModal(c?'Editar veículo':'Novo veículo',`<div class="form-grid"><div class="full">${select('cliente_id','Cliente responsável',clientes.map(v=>[v.id,v.nome+(v.ativo?'':' (inativo)')]),c?.cliente_id)}</div>${input('placa','Placa','text',c?.placa||'',{required:true,maxlength:12,placeholder:'ABC1D23'})}${input('modelo','Modelo','text',c?.modelo||'',{required:true,maxlength:80})}${input('cor','Cor','text',c?.cor||'',{required:true,maxlength:30})}</div>${c?'<p class="muted" style="font-size:10px;margin-top:18px">Alterar o responsável preserva o cliente histórico das permanências.</p>':''}`,async values=>{
    const body={...values,cliente_id:Number(values.cliente_id)};
    if(c) await patch('/veiculos/'+c.id,body); else await post('/veiculos',body);
    await complete(c?'Veículo atualizado.':'Veículo cadastrado.');
  });
}

function spaceModal(id) {
  const c = id ? state.cache.rows?.find(v=>v.id===id) : null;
  openModal(c?'Editar vaga':'Nova vaga',`<div class="form-stack">${input('numero','Número ou código da vaga','text',c?.numero||'',{required:true,maxlength:10,placeholder:'A-01'})}${c?activeSelect('Situação',c.ativa,'ativa'):''}</div>`,async values=>{
    const body={numero:values.numero.trim(),...(c?{ativa:values.ativa==='true'}:{})};
    if(c) await patch('/vagas/'+c.id,body);else await post('/vagas',body);
    await complete(c?'Vaga atualizada.':'Vaga cadastrada.');
  });
}

function userModal(id) {
  const u = id ? state.cache.rows?.find(v=>v.id===id) : null;
  openModal(u?'Editar operador':'Novo operador',`<div class="form-stack">${input('nome','Nome','text',u?.nome||'',{required:true,maxlength:120})}${input('login','Login','text',u?.login||'',{required:true,maxlength:80,autocomplete:'off'})}${input('senha',u?'Nova senha (opcional)':'Senha','password','',{...(u?{}:{required:true}),minlength:8,maxlength:128,autocomplete:'new-password'})}${u?activeSelect('Situação',u.ativo):''}</div>`,async values=>{
    const body={...values,...(u?{ativo:values.ativo==='true'}:{})};
    if(u&&!body.senha) delete body.senha;
    if(u) await patch('/usuarios/'+u.id,body);else await post('/usuarios',body);
    if(u?.id===state.user.id&&body.ativo===false) {logout();toast('Sua conta foi desativada.');return;}
    await complete(u?'Operador atualizado.':'Operador cadastrado.');
  });
}

async function contractModal() {
  const [clientes,vagas] = await Promise.all([all('/clientes'),all('/vagas')]);
  if(!clientes.some(c=>c.ativo)||!vagas.some(v=>v.ativa)){toast('Cadastre cliente ativo, vaga ativa e tarifas antes de contratar.',true);return;}
  openModal('Nova contratação',`<div class="notice">Reserva exclusiva. A primeira mensalidade é gerada no início do contrato. Valor integral, sem proporcionalidade.</div><div class="form-stack">${select('cliente_id','Cliente',clientes.filter(c=>c.ativo).map(c=>[c.id,c.nome]))}${select('vaga_id','Vaga',vagas.filter(v=>v.ativa).map(v=>[v.id,`Vaga ${v.numero}`]))}<div class="form-grid">${input('data_inicio','Data de início','date',today(),{required:true})}${input('data_fim','Último dia da reserva (opcional)','date')}</div></div>`,async values=>{
    await post('/contratacoes',{cliente_id:Number(values.cliente_id),vaga_id:Number(values.vaga_id),data_inicio:values.data_inicio,data_fim:values.data_fim||null});
    await complete('Contratação criada. Consulte a tela Cobranças para receber a mensalidade.');
  },'Criar contratação');
}

async function entryModal(vagaId) {
  const [vagas,veiculos,clientes] = await Promise.all([all('/vagas'),all('/veiculos'),all('/clientes')]);
  const validos = veiculos.filter(v=>clientes.some(c=>c.id===v.cliente_id&&c.ativo));
  const livres = vagas.filter(v=>v.disponivel);
  if(!validos.length){toast('Cadastre um cliente ativo e seu veículo antes de registrar a entrada.',true);return;}
  if(!livres.length){toast('Nenhuma vaga disponível no momento.',true);return;}
  openModal('Registrar entrada',`<div class="form-stack">${select('veiculo_id','Veículo / cliente',validos.map(v=>[v.id,`${v.placa} · ${v.modelo} · ${clientes.find(c=>c.id===v.cliente_id)?.nome}`]))}${select('vaga_id','Vaga disponível',livres.map(v=>[v.id,`Vaga ${v.numero}`]),vagaId||'')}</div><p class="muted" style="font-size:11px;margin-top:20px">O horário e a tarifa são registrados na confirmação. A disponibilidade será conferida novamente.</p>`,async values=>{
    await post('/permanencias',{veiculo_id:Number(values.veiculo_id),vaga_id:Number(values.vaga_id)});
    await complete('Entrada registrada. Boa permanência!');
  },'Confirmar entrada');
}

async function exitModal(id) {
  const previa = await api(`/permanencias/${id}/previa`);
  const p = state.cache.abertas?.find(p=>p.id===id);
  const veiculo = state.cache.veiculos?.find(v=>v.id===p?.veiculo_id);
  openModal('Registrar saída',`<p>Confira o valor e selecione como o cliente vai pagar.</p><dl class="details"><div><dt>Veículo</dt><dd>${veiculo?esc(veiculo.placa):`Permanência #${id}`}</dd></div><div><dt>Blocos de 30 minutos</dt><dd>${previa.blocos}</dd></div><div><dt>Prévia calculada às</dt><dd>${localTime(previa.calculado_em)}</dd></div></dl><div class="total"><span>Valor previsto</span><strong>${money(previa.valor)}</strong></div>${paymentSelect()}<p style="font-size:10px;margin-top:16px">O valor será recalculado ao confirmar. A confirmação encerra a permanência e registra o pagamento integral.</p>`,async values=>{
    const cobranca=await post(`/permanencias/${id}/saida`,values);
    await complete(`Saída registrada. Pagamento de ${money(cobranca.valor)} confirmado.`);
  },'Confirmar saída e pagamento');
}

function payModal(id) {
  const c=state.cache.rows.find(c=>c.id===id);
  openModal('Receber mensalidade',`<dl class="details"><div><dt>Vencimento</dt><dd>${localDate(c.vencimento)}</dd></div><div><dt>Competência</dt><dd>${c.competencia.slice(0,7).split('-').reverse().join('/')}</dd></div></dl><div class="total"><span>Pagamento integral</span><strong>${money(c.valor)}</strong></div>${paymentSelect()}`,async values=>{
    await post(`/cobrancas/${id}/pagar`,values);
    await complete('Mensalidade recebida.');
  },'Confirmar pagamento');
}

function cancelContract(id) {
  openModal('Cancelar renovação',`<p>A reserva permanece até o fim do último período já iniciado. A contratação não terá novas renovações depois dessa data.</p><div class="notice">Os valores já cobrados são preservados, inclusive dívidas. Não há devolução ou crédito por cancelamento antecipado.</div>`,async()=>{
    const c=await post(`/contratacoes/${id}/cancelar`);
    await complete(`Renovação cancelada. Reserva mantida até ${localDate(c.data_fim)}.`);
  },'Confirmar cancelamento');
}

function accessModal() {
  openModal('Consultar mensalista',`<p>Consulte a placa antes de liberar o acesso. Esta consulta atualiza as mensalidades e não registra entrada ou saída.</p>${input('placa','Placa do veículo','text','',{required:true,maxlength:12,placeholder:'ABC1D23',autocomplete:'off'})}`,async values=>{
    const result=await post('/cobrancas/consultar-acesso',values);
    openModal('Resultado da consulta',`<div class="access-result ${result.liberado?'':'blocked'}">${icon(result.liberado?'check':'lock')}<h3>${result.liberado?'Acesso liberado':'Acesso bloqueado'}</h3><p>${esc(result.motivo)}</p>${result.vagas.length?`<p style="margin-top:16px;font-size:11px">${result.vagas.length} ${result.vagas.length===1?'vaga contratada':'vagas contratadas'}</p>`:''}</div>`,null);
  },'Consultar acesso');
}

async function spaceDetail(id) {
  const v=state.cache.vagas?.find(v=>v.id===id);
  if(v.disponivel) return entryModal(id);
  const p=state.cache.abertas?.find(p=>p.vaga_id===id);
  if(p) return exitModal(p.id);
  openModal(`Vaga ${v.numero}`,`<p>${esc(v.motivo)}</p><div class="notice">Vagas de mensalistas permanecem reservadas mesmo quando estão vazias. O controle de presença é manual.</div>`,null);
}

const actions = {
  'refresh':()=>render(), 'new-client':()=>clientModal(), 'edit-client':id=>clientModal(id),
  'new-vehicle':()=>vehicleModal(), 'edit-vehicle':id=>vehicleModal(id),
  'new-space':()=>spaceModal(), 'edit-space':id=>spaceModal(id),
  'new-user':()=>userModal(), 'edit-user':id=>userModal(id),
  'new-contract':()=>contractModal(), 'cancel-contract':id=>cancelContract(id),
  'entry':()=>entryModal(), 'exit':id=>exitModal(id), 'pay-charge':id=>payModal(id),
  'access':()=>accessModal(), 'space-detail':id=>spaceDetail(id),
  'previous':()=>{state.offset=Math.max(0,state.offset-state.limit);return render();},
  'next':()=>{state.offset+=state.limit;return render();},
  'client-vehicles':async id=>{location.hash='veiculos';await new Promise(resolve=>setTimeout(resolve,0));state.filter=String(id);await render();},
  'open-stays':()=>{
    const rows=state.cache.abertas||[];
    openModal('Horistas no pátio',table(['Placa','Entrada',''],rows.map(p=>`<tr><td><span class="plate">${esc(state.cache.veiculos.find(v=>v.id===p.veiculo_id)?.placa||'—')}</span></td><td>${timestamp(p.entrada)}</td><td>${rowAction('Saída ↗','exit',p.id)}</td></tr>`)),null);
  },
};

document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-action]');
  if(!button||button.disabled) return;
  const fn=actions[button.dataset.action]; if(!fn) return;
  button.disabled=true;
  try {await fn(Number(button.dataset.id));}catch(error){toast(error.message,true);}
  finally{button.disabled=false;}
});
document.addEventListener('submit',async event=>{
  if(event.target.id==='search-form'){
    event.preventDefault();state.query=new FormData(event.target).get('search').trim();state.offset=0;render();
  }
  if(event.target.id==='rates-form'){
    event.preventDefault();const button=$('button',event.target);button.disabled=true;
    try {await api('/tarifas',{method:state.cache.tarifa?'PUT':'POST',body:JSON.stringify(Object.fromEntries(new FormData(event.target)))});toast('Tarifas salvas.');await render();}
    catch(error){toast(error.message,true);}finally{button.disabled=false;}
  }
});
document.addEventListener('change',event=>{
  if(event.target.id==='list-filter'){state.filter=event.target.value;state.offset=0;render();}
});
$('#modal-form').addEventListener('submit',async event=>{
  event.preventDefault();if(!modalHandler)return;
  const handler=modalHandler;const version=modalVersion;
  $('#modal-submit').disabled=true;$('#modal-error').hidden=true;
  $('#modal-close').disabled=true;$('#modal-cancel').disabled=true;
  try {await handler(Object.fromEntries(new FormData(event.target)));}
  catch(error){if(version===modalVersion){$('#modal-error').textContent=error.message;$('#modal-error').hidden=false;}else toast(error.message,true);}
  finally {$('#modal-close').disabled=false;$('#modal-cancel').disabled=false;$('#modal-submit').disabled=!modalHandler;}
});
$('#modal-close').addEventListener('click',closeModal);
$('#modal-cancel').addEventListener('click',closeModal);
$('#modal').addEventListener('cancel',event=>{
  if($('#modal-cancel').disabled)event.preventDefault();else modalHandler=null;
});
$('#logout').addEventListener('click',logout);
$('#menu-toggle').addEventListener('click',()=>{
  const open=$('#sidebar').classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(open));
});
window.addEventListener('hashchange',navigate);
$('#login-form').addEventListener('submit',async event=>{
  event.preventDefault();const button=$('button',event.target);button.disabled=true;$('#login-error').hidden=true;
  try {
    const result=await post('/auth/login',Object.fromEntries(new FormData(event.target)));
    token=result.access_token;sessionStorage.setItem('mationamento_token',token);
    const user=await api('/auth/me');event.target.reset();showApp(user);
  } catch(error){$('#login-error').textContent=error.message;$('#login-error').hidden=false;}
  finally{button.disabled=false;}
});

async function start(){
  tick();setInterval(tick,30000);
  if(token){
    try{showApp(await api('/auth/me'));return;}
    catch(error){logout();$('#login-error').textContent=error.message;$('#login-error').hidden=false;}
  }
  $('#login-view').hidden=false;
}
start();
