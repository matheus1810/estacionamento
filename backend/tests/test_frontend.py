"""Navegador real, API simulada: verifica telas e requisições, não o MySQL."""
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = pytest.mark.browser
playwright = pytest.importorskip('playwright.sync_api')
ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / 'frontend'
ARTIFACTS = ROOT / 'backend' / '.artifacts'


@pytest.fixture
def browser_page():
    executable = os.getenv('BROWSER_EXECUTABLE', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    if not Path(executable).is_file():
        pytest.skip('Defina BROWSER_EXECUTABLE com o caminho de um Chromium instalado.')
    usuario = {'id':1,'nome':'Ana Operadora','login':'ana','ativo':True,'criado_em':'2026-10-16T08:00:00'}
    cliente = {'id':1,'nome':'Ana Cliente','telefone':'11999999999','ativo':True,'criado_em':'2026-10-16T08:00:00'}
    veiculo = {'id':1,'cliente_id':1,'placa':'ABC1D23','modelo':'Uno','cor':'Azul'}
    vagas = [{'id':1,'numero':'A-01','ativa':True,'disponivel':True,'motivo':'Vaga disponível.'},
             {'id':2,'numero':'A-02','ativa':True,'disponivel':False,'motivo':'Vaga ocupada por horista.'}]
    permanencia = {'id':1,'cliente_id':1,'veiculo_id':1,'vaga_id':2,'entrada':'2026-10-20T09:00:00','saida':None}
    contrato = {'id':1,'cliente_id':1,'vaga_id':1,'data_inicio':'2026-10-16','data_fim':None}
    cobranca = {'id':1,'permanencia_id':None,'contratacao_mensal_id':1,'competencia':'2026-10-01','vencimento':'2026-10-16','valor':'300.00','pago_em':None,'forma_pagamento':None}
    calls = []
    failures = []
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable,headless=True)
        page = browser.new_page(viewport={'width':1440,'height':1000},locale='pt-BR',reduced_motion='reduce')
        page.on('pageerror',lambda exc:failures.append(str(exc)))

        def route_handler(route):
            request = route.request
            url = urlparse(request.url)
            path = url.path
            if url.hostname != 'mationamento.test':
                route.abort()
                return
            if path=='/' or path.startswith('/assets/'):
                filename = 'index.html' if path=='/' else path.removeprefix('/assets/')
                file = FRONTEND / filename
                route.fulfill(path=str(file))
                return
            body = request.post_data_json if request.post_data else None
            calls.append((request.method,path,body))
            data = None
            status = 200
            if path=='/auth/login': data={'access_token':'token-apenas-do-teste','token_type':'bearer'}
            elif path=='/auth/me': data=usuario
            elif path=='/cobrancas/atualizar-mensalidades':data={'geradas':0}
            elif path=='/cobrancas/consultar-acesso':data={'liberado':False,'motivo':'Cliente possui mensalidade vencida e não paga.','vagas':[],'cliente_id':1}
            elif path.endswith('/previa'):data={'permanencia_id':1,'calculado_em':'2026-10-20T10:20:00','blocos':3,'valor':'15.00'}
            elif path.endswith('/saida'):data={**cobranca,'valor':'15.00','pago_em':'2026-10-20T10:20:00'}
            elif path.endswith('/pagar'):data={**cobranca,'pago_em':'2026-10-20T10:20:00'}
            elif path.endswith('/cancelar'):data={**contrato,'data_fim':'2026-11-15'}
            elif path=='/tarifas':data={'id':1,'valor_hora':'10.00','valor_mensal_vaga':'300.00','criado_em':'2026-10-16T08:00:00'}
            elif request.method=='POST':data={'id':3,**(body or {})};status=201
            elif request.method=='PATCH':data={'id':1,**(body or {})}
            elif path=='/clientes':data=[cliente]
            elif path=='/clientes/1':data=cliente
            elif path=='/veiculos':data=[veiculo]
            elif path.startswith('/veiculos/placa/'):data=veiculo
            elif path=='/vagas':data=vagas
            elif path=='/permanencias':data=[permanencia]
            elif path=='/contratacoes':data=[contrato]
            elif path=='/cobrancas':data=[cobranca]
            elif path=='/usuarios':data=[usuario]
            else:data={'detail':'Rota não simulada: '+path};status=404
            route.fulfill(status=status,content_type='application/json',body=json.dumps(data))

        page.route('**/*',route_handler)
        page.goto('http://mationamento.test/')
        yield page,calls,failures
        assert not failures, failures
        browser.close()


def entrar(page):
    page.get_by_label('Login',exact=True).fill('ana')
    page.get_by_label('Senha',exact=True).fill('senha-teste')
    page.get_by_role('button',name='Entrar no estacionamento').click()
    page.get_by_role('heading',name='Tudo sob controle.').wait_for()


def test_telas_formularios_e_mobile(browser_page):
    page,calls,failures = browser_page
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'login.png'),full_page=True)
    entrar(page)
    page.get_by_role('heading',name='Mapa de vagas').wait_for()
    page.screenshot(path=str(ARTIFACTS/'operacao-desktop.png'),full_page=True)
    # Veículo existente que está fora do pátio e não tem contrato mensal.
    page.route('**/permanencias?*veiculo_id=*',lambda route:route.fulfill(json=[]))
    page.route('**/contratacoes?*vigentes=true*',lambda route:route.fulfill(json=[]))
    page.get_by_role('button',name='Registrar entrada',exact=True).first.click()
    dialog=page.get_by_role('dialog')
    dialog.get_by_label('Placa do veículo').fill('abc-1d23')
    dialog.get_by_role('button',name='Consultar placa',exact=True).click()
    dialog.get_by_role('combobox',name='Veículo / cliente',exact=True).fill('ABC1D23')
    page.get_by_role('option',name='ABC1D23 · Uno · Ana Cliente',exact=True).click()
    dialog.get_by_role('combobox',name='Vaga disponível',exact=True).fill('A-01')
    page.get_by_role('option',name='Vaga A-01',exact=True).click()
    dialog.get_by_role('button',name='Confirmar entrada',exact=True).click()
    page.get_by_text('Entrada registrada: ABC1D23 · vaga A-01.',exact=True).wait_for()
    assert ('POST','/permanencias',{'veiculo_id':1,'vaga_id':1}) in calls

    page.get_by_role('button',name='Registrar saída ↗').click()
    dialog.get_by_text('R$\xa015,00',exact=True).wait_for()
    dialog.get_by_label('Forma de pagamento').select_option('pix')
    dialog.get_by_role('button',name='Confirmar saída e pagamento').click()
    page.get_by_text('Saída registrada: ABC1D23. Pagamento de R$\xa015,00 confirmado.',exact=True).wait_for()
    assert ('POST','/permanencias/1/saida',{'forma_pagamento':'pix'}) in calls

    page.get_by_role('link',name='Clientes',exact=True).click()
    page.get_by_role('heading',name='Clientes',exact=True).wait_for()
    page.get_by_role('button',name='Novo cliente').click()
    dialog.get_by_label('Nome completo').fill('Novo Cliente')
    dialog.get_by_label('Telefone').fill('11912345678')
    dialog.get_by_role('button',name='Salvar',exact=True).click()
    page.get_by_text('Cliente cadastrado. Cadastre o veículo na tela Veículos.',exact=True).wait_for()
    assert ('POST','/clientes',{'nome':'Novo Cliente','telefone':'11912345678'}) in calls

    for route,title in [('veiculos','Veículos'),('vagas','Vagas'),('mensalistas','Mensalistas'),('cobrancas','Cobranças'),('tarifas','Tarifas'),('usuarios','Operadores')]:
        page.locator(f'a[data-page="{route}"]').click()
        page.get_by_role('heading',name=title,exact=True).wait_for()
    assert any(method=='POST' and path=='/cobrancas/atualizar-mensalidades' for method,path,_ in calls)

    page.locator('a[data-page="mensalistas"]').click()
    page.get_by_role('button',name='Consultar placa',exact=True).click()
    dialog.get_by_label('Placa do veículo').fill('ABC1D23')
    dialog.get_by_role('button',name='Consultar acesso',exact=True).click()
    dialog.get_by_role('heading',name='Acesso bloqueado').wait_for()
    dialog.get_by_role('button',name='Fechar',exact=True).click()

    page.set_viewport_size({'width':390,'height':844})
    page.get_by_role('button',name='Abrir menu').click()
    page.locator('a[data-page="operacao"]').click()
    page.get_by_role('heading',name='Mapa de vagas').wait_for()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('#toast-container').evaluate('(el) => el.replaceChildren()')
    page.screenshot(path=str(ARTIFACTS/'operacao-mobile.png'),full_page=True)
    page.get_by_role('button',name='Abrir menu').click()
    page.get_by_role('button',name='Sair da conta').click()
    page.get_by_role('heading',name='Bom ter você por aqui.').wait_for()
    assert page.evaluate("sessionStorage.getItem('mationamento_token')") is None


def test_sessao_encerra_ao_voltar_e_avancar(browser_page):
    page, calls, _ = browser_page
    page.route('**/fora', lambda route: route.fulfill(content_type='text/html', body='<p>Fora</p>'))
    page.goto('http://mationamento.test/fora')
    page.goto('http://mationamento.test/')
    entrar(page)
    page.go_back()
    page.go_forward()
    page.locator('#login-view').wait_for(state='visible')
    assert page.locator('#app-view').is_hidden()
    assert page.evaluate("sessionStorage.getItem('mationamento_token')") is None
    entrar(page)
    page.locator('a[data-page="clientes"]').click()
    page.locator('a[data-page="veiculos"]').click()
    page.go_back()
    assert page.url == 'http://mationamento.test/fora'
    page.go_forward()
    page.locator('#login-view').wait_for(state='visible')
    page.go_back()
    assert page.url == 'http://mationamento.test/fora'


def test_sessao_encerra_ao_atualizar(browser_page):
    page, _, _ = browser_page
    entrar(page)
    page.reload()
    page.locator('#login-view').wait_for(state='visible')
    assert page.locator('#app-view').is_hidden()
    assert page.evaluate("sessionStorage.getItem('mationamento_token')") is None


def test_menus_mantem_sessao_sem_acrescentar_historico(browser_page):
    page, _, _ = browser_page
    entrar(page)
    tamanho = page.evaluate('history.length')
    page.locator('a[data-page="clientes"]').click()
    page.locator('a[data-page="veiculos"]').click()
    page.locator('a[data-page="veiculos"].active').wait_for()
    assert page.url.endswith('#veiculos')
    assert page.evaluate('history.length') == tamanho
    assert page.locator('#app-view').is_visible()
    page.get_by_role('button', name='Sair da conta').click()
    page.reload()
    assert page.locator('#app-view').is_hidden()
    assert page.evaluate("sessionStorage.getItem('mationamento_token')") is None


def test_restauracao_do_cache_encerra_sessao(browser_page):
    page, _, _ = browser_page
    entrar(page)
    # Playwright pode desabilitar o cache do histórico; cobre também seu evento.
    page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    assert page.locator('#login-view').is_visible()
    assert page.locator('#app-view').is_hidden()
    assert page.locator('#main').inner_html() == ''
    assert page.evaluate("sessionStorage.getItem('mationamento_token')") is None


def test_pagamentos_cancelamento_edicao_e_tarifas(browser_page):
    page,calls,_ = browser_page
    entrar(page)
    dialog=page.get_by_role('dialog')
    page.locator('a[data-page="cobrancas"]').click()
    page.get_by_role('button',name='Receber',exact=True).click()
    dialog.get_by_label('Forma de pagamento').select_option('dinheiro')
    dialog.get_by_role('button',name='Confirmar pagamento').click()
    page.get_by_text('Mensalidade recebida.',exact=True).wait_for()
    assert ('POST','/cobrancas/1/pagar',{'forma_pagamento':'dinheiro'}) in calls
    page.locator('a[data-page="mensalistas"]').click()
    page.get_by_role('button',name='Cancelar renovação',exact=True).click()
    dialog.get_by_role('button',name='Confirmar cancelamento',exact=True).click()
    page.get_by_text('Renovação cancelada. Reserva mantida até 15/11/2026.',exact=True).wait_for()
    page.locator('a[data-page="vagas"]').click()
    page.get_by_role('button',name='Editar',exact=True).first.click()
    dialog.get_by_label('Número ou código da vaga').fill('B-01')
    dialog.get_by_label('Situação',exact=True).select_option('false')
    dialog.get_by_role('button',name='Salvar',exact=True).click()
    page.get_by_text('Vaga atualizada.',exact=True).wait_for()
    assert ('PATCH','/vagas/1',{'numero':'B-01','ativa':False}) in calls
    page.locator('a[data-page="tarifas"]').click()
    page.get_by_label('Valor por hora (R$)').fill('12.50')
    page.get_by_role('button',name='Salvar tarifas',exact=True).click()
    page.get_by_text('Tarifas salvas.',exact=True).wait_for()
    assert ('PUT','/tarifas',{'valor_hora':'12.50','valor_mensal_vaga':'300.00'}) in calls


def test_placa_localiza_saida_filtro_e_foco(browser_page):
    page,calls,_=browser_page
    entrar(page)
    placa=page.get_by_label('Placa para atendimento',exact=True)
    placa.fill('abc-1d23')
    placa.press('Enter')
    dialog=page.get_by_role('dialog')
    dialog.get_by_role('heading',name='Registrar saída',exact=True).wait_for()
    dialog.get_by_text('1h 20min',exact=True).wait_for()
    assert dialog.get_by_text('Entrada',exact=True).is_visible()
    assert dialog.get_by_text('Tempo decorrido',exact=True).is_visible()
    assert not any(method=='POST' and path=='/permanencias' for method,path,_ in calls)
    dialog.get_by_role('button',name='Cancelar',exact=True).click()
    assert placa.evaluate('(el)=>document.activeElement===el')
    page.get_by_label('Filtrar veículos no pátio').fill('ZZZ')
    page.get_by_text('Nenhuma placa corresponde à busca.',exact=True).wait_for()
    page.get_by_label('Filtrar veículos no pátio').fill('abc-1')
    page.get_by_role('button',name='Registrar saída ↗').wait_for()
    page.keyboard.press('Alt+p')
    assert placa.evaluate('(el)=>document.activeElement===el')


def test_cadastro_rapido_preserva_dados_no_conflito_e_tenta_novamente(browser_page):
    page,calls,_=browser_page
    page.route('**/veiculos/placa/NEW1A23',lambda route:route.fulfill(status=404,json={'detail':'Veículo não encontrado.'}))
    tentativas=[]
    def cadastrar(route):
        tentativas.append(route.request.post_data_json)
        if len(tentativas)==1:route.fulfill(status=409,json={'detail':'Vaga ocupada por horista.'})
        else:route.fulfill(status=201,json={'id':3,'vaga_id':1})
    page.route('**/permanencias/cadastro-entrada',cadastrar)
    entrar(page)
    page.get_by_label('Placa para atendimento',exact=True).fill('NEW1A23')
    page.get_by_label('Placa para atendimento',exact=True).press('Enter')
    dialog=page.get_by_role('dialog')
    dialog.get_by_role('heading',name='Cadastrar e registrar entrada').wait_for()
    assert dialog.get_by_label('Placa',exact=True).input_value()=='NEW1A23'
    dialog.get_by_label('Modelo',exact=True).fill('Fiat Argo')
    dialog.get_by_label('Cor',exact=True).fill('Branco')
    dialog.get_by_label('Nome do cliente',exact=True).fill('Cliente Novo')
    dialog.get_by_label('Telefone',exact=True).fill('11912345678')
    dialog.get_by_role('button',name='Cadastrar e confirmar entrada').click()
    dialog.get_by_text('Vaga ocupada por horista.',exact=True).wait_for()
    assert dialog.get_by_label('Nome do cliente',exact=True).input_value()=='Cliente Novo'
    dialog.get_by_role('button',name='Atualizar vagas livres').click()
    page.get_by_text('Vagas atualizadas. Confira a seleção antes de confirmar.',exact=True).wait_for()
    assert dialog.get_by_label('Modelo',exact=True).input_value()=='Fiat Argo'
    dialog.get_by_role('button',name='Cadastrar e confirmar entrada').click()
    page.get_by_text('Entrada registrada: NEW1A23 · vaga A-01. Cadastro concluído.',exact=True).wait_for()
    assert tentativas==[{'placa':'NEW1A23','modelo':'Fiat Argo','cor':'Branco','vaga_id':1,
                         'cliente':{'nome':'Cliente Novo','telefone':'11912345678'}}]*2
    assert not any(path in ('/clientes','/veiculos') and method=='POST' for method,path,_ in calls)


def test_mensalista_recebe_pendencia_sem_sair_do_atendimento(browser_page):
    page,calls,_=browser_page
    page.route('**/permanencias?*veiculo_id=*',lambda route:route.fulfill(json=[]))
    pago=[]
    falhas=[]
    def acesso(route):
        if pago and not falhas:
            falhas.append(True)
            route.fulfill(status=503,json={'detail':'Não foi possível conferir o acesso agora.'})
            return
        route.fulfill(json={'liberado':bool(pago),'motivo':'Acesso liberado.' if pago else 'Cliente possui mensalidade vencida e não paga.',
                            'vagas':[1] if pago else [],'cliente_id':1})
    def pagar(route):
        pago.append(route.request.post_data_json)
        route.fulfill(json={'id':1,'pago_em':'2026-10-23T09:00:00'})
    def pendencias(route):
        route.fulfill(json=[] if pago else [{'id':1,'competencia':'2026-10-01','vencimento':'2026-10-16','valor':'300.00'}])
    page.route('**/cobrancas/consultar-acesso',acesso)
    page.route('**/cobrancas?vencidas=true*',pendencias)
    page.route('**/cobrancas/1/pagar',pagar)
    entrar(page)
    page.get_by_label('Placa para atendimento',exact=True).fill('ABC1D23')
    page.get_by_label('Placa para atendimento',exact=True).press('Enter')
    dialog=page.get_by_role('dialog')
    dialog.get_by_role('heading',name='Acesso bloqueado').wait_for()
    dialog.get_by_role('button',name='Receber',exact=True).click()
    dialog.get_by_label('Forma de pagamento').select_option('pix')
    dialog.get_by_role('button',name='Confirmar pagamento').click()
    dialog.get_by_role('heading',name='Pagamento confirmado',exact=True).wait_for()
    page.get_by_text('Não foi possível conferir o acesso agora.',exact=True).wait_for()
    dialog.get_by_role('button',name='Conferir acesso',exact=True).click()
    dialog.get_by_role('heading',name='Acesso liberado').wait_for()
    assert pago==[{'forma_pagamento':'pix'}]
    assert page.locator('a[data-page="operacao"]').get_attribute('aria-current')=='page'


def test_select_busca_teclado_validacao_e_envio_do_id(browser_page):
    page, calls, _ = browser_page
    clientes = [
        {'id': 1, 'nome': 'Ana Cliente', 'telefone': '11999999999', 'ativo': True},
        {'id': 27, 'nome': 'João Ávila', 'telefone': '11988888888', 'ativo': True},
    ]
    page.route('**/clientes?*', lambda route: route.fulfill(json=clientes))
    entrar(page)
    page.locator('a[data-page="veiculos"]').click()
    page.get_by_role('button', name='Novo veículo', exact=True).click()
    dialog = page.get_by_role('dialog')
    cliente = dialog.get_by_role('combobox', name='Cliente responsável', exact=True)
    dialog.get_by_label('Placa', exact=True).fill('NEW1A23')
    dialog.get_by_label('Modelo', exact=True).fill('Argo')
    dialog.get_by_label('Cor', exact=True).fill('Branco')
    # Digitar um nome não substitui a escolha de um registro válido.
    cliente.fill('inexistente')
    page.get_by_text('Nenhum resultado encontrado.', exact=True).wait_for()
    cliente.press('Enter')
    assert not any(method == 'POST' and path == '/veiculos' for method, path, _ in calls)
    dialog.get_by_role('button', name='Salvar', exact=True).click()
    page.get_by_text('Selecione uma opção da lista.', exact=True).wait_for()
    assert cliente.get_attribute('aria-invalid') == 'true'
    # A busca ignora acentos; Enter escolhe sem enviar o formulário.
    cliente.fill('joao avila')
    assert page.get_by_role('option').all_text_contents() == ['João Ávila']
    cliente.press('Enter')
    assert cliente.input_value() == 'João Ávila'
    assert cliente.get_attribute('aria-expanded') == 'false'
    assert not any(method == 'POST' and path == '/veiculos' for method, path, _ in calls)
    # Escape e Tab descartam apenas a busca e preservam o cliente escolhido.
    cliente.fill('nada')
    cliente.press('Escape')
    assert dialog.is_visible()
    assert cliente.input_value() == 'João Ávila'
    cliente.fill('outra busca')
    cliente.press('Tab')
    assert cliente.input_value() == 'João Ávila'
    cliente.click()
    cliente.press('Home')
    cliente.press('ArrowDown')
    cliente.press('Enter')
    dialog.get_by_role('button', name='Salvar', exact=True).click()
    page.get_by_text('Veículo cadastrado.', exact=True).wait_for()
    assert ('POST', '/veiculos', {
        'cliente_id': 27, 'placa': 'NEW1A23', 'modelo': 'Argo', 'cor': 'Branco',
    }) in calls


def test_select_busca_responsavel_atualizacao_de_vagas_e_mobile(browser_page):
    page, calls, _ = browser_page
    page.route('**/veiculos/placa/NEW1A23', lambda route: route.fulfill(
        status=404, json={'detail': 'Veículo não encontrado.'},
    ))
    entrar(page)
    page.set_viewport_size({'width': 390, 'height': 844})
    placa = page.get_by_label('Placa para atendimento', exact=True)
    placa.fill('NEW1A23')
    placa.press('Enter')
    dialog = page.get_by_role('dialog')
    dialog.get_by_role('heading', name='Cadastrar e registrar entrada').wait_for()
    dialog.get_by_label('Modelo', exact=True).fill('Argo')
    dialog.get_by_label('Cor', exact=True).fill('Branco')
    responsavel = dialog.get_by_role('combobox', name='Responsável', exact=True)
    responsavel.fill('119999')
    page.get_by_role('option', name='Ana Cliente · 11999999999', exact=True).click()
    assert responsavel.get_attribute('aria-expanded') == 'false'
    assert not dialog.get_by_label('Nome do cliente', exact=True).is_visible()
    responsavel.fill('novo cliente')
    responsavel.press('Enter')
    assert dialog.get_by_label('Nome do cliente', exact=True).is_visible()
    responsavel.fill('ana')
    responsavel.press('Enter')
    # A vaga anterior deixou de estar livre. A seleção e os resultados devem atualizar.
    page.route('**/vagas?*', lambda route: route.fulfill(json=[{
        'id': 3, 'numero': 'B-02', 'ativa': True, 'disponivel': True,
        'motivo': 'Vaga disponível.',
    }]))
    dialog.get_by_role('button', name='Atualizar vagas livres', exact=True).click()
    page.get_by_text('Vagas atualizadas. Confira a seleção antes de confirmar.', exact=True).wait_for()
    vaga = dialog.get_by_role('combobox', name='Vaga disponível', exact=True)
    assert vaga.input_value() == ''
    vaga.fill('A-01')
    page.get_by_text('Nenhum resultado encontrado.', exact=True).wait_for()
    vaga.fill('b02')
    popup = page.locator('.select-busca-popup:visible')
    box = popup.bounding_box()
    assert 0 <= box['x'] and box['x'] + box['width'] <= 390
    assert 0 <= box['y'] and box['y'] + box['height'] <= 844
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS / 'select-busca-mobile.png'), full_page=True)
    vaga.press('Enter')
    dialog.get_by_role('button', name='Cadastrar e confirmar entrada', exact=True).click()
    page.get_by_text('Entrada registrada: NEW1A23 · vaga B-02. Cadastro concluído.', exact=True).wait_for()
    assert ('POST', '/permanencias/cadastro-entrada', {
        'placa': 'NEW1A23', 'modelo': 'Argo', 'cor': 'Branco', 'vaga_id': 3, 'cliente_id': 1,
    }) in calls


def test_select_busca_filtro_de_clientes(browser_page):
    page, calls, _ = browser_page
    entrar(page)
    page.locator('a[data-page="veiculos"]').click()
    filtro = page.get_by_role('combobox', name='Filtrar por cliente', exact=True)
    filtro.fill('ana')
    page.get_by_role('option', name='Ana Cliente', exact=True).click()
    page.wait_for_function("document.querySelector('#list-filter')?.value === '1'")
    assert filtro.input_value() == 'Ana Cliente'
    filtro.fill('todos')
    filtro.press('Enter')
    page.wait_for_function("document.querySelector('#list-filter')?.value === ''")
    assert filtro.input_value() == 'Todos os clientes'


def test_placa_orienta_correcao_sem_alterar_valor_digitado(browser_page):
    page, calls, _ = browser_page
    entrar(page)
    page.get_by_role('button', name='Registrar entrada', exact=True).first.click()
    dialog = page.get_by_role('dialog')
    placa = dialog.get_by_label('Placa do veículo', exact=True)
    page.get_by_text('Use 7 caracteres:', exact=False).wait_for()
    placa.fill('AOR108961')
    dialog.get_by_role('button', name='Consultar placa', exact=True).click()
    dialog.get_by_text(
        'Você digitou 9 caracteres. A placa deve ter 7, sem contar espaços ou hífens. '
        'Confira a digitação. Exemplos: ABC1234 ou ABC1D23.', exact=True,
    ).wait_for()
    assert placa.input_value() == 'AOR108961'
    assert placa.get_attribute('aria-invalid') == 'true'
    assert placa.evaluate('(el) => document.activeElement === el')
    assert not any(path.startswith('/veiculos/placa/') for _, path, _ in calls)
    placa.fill('ABC12DD')
    assert placa.get_attribute('aria-invalid') is None
    dialog.get_by_role('button', name='Consultar placa', exact=True).click()
    dialog.get_by_text(
        'O formato da placa não foi reconhecido. Use ABC1234 (3 letras e 4 números) '
        'ou ABC1D23 (Mercosul).', exact=True,
    ).wait_for()
    placa.fill('abc-1234')
    dialog.get_by_role('button', name='Consultar placa', exact=True).click()
    dialog.get_by_role('heading', name='Registrar saída', exact=True).wait_for()
    assert any(path == '/veiculos/placa/ABC1234' for _, path, _ in calls)


def test_placa_orientacao_tambem_no_atendimento_rapido(browser_page):
    page, calls, _ = browser_page
    entrar(page)
    placa = page.get_by_label('Placa para atendimento', exact=True)
    placa.fill('ABC12')
    placa.press('Enter')
    page.get_by_text(
        'Você digitou 5 caracteres. A placa deve ter 7, sem contar espaços ou hífens. '
        'Confira a digitação. Exemplos: ABC1234 ou ABC1D23.', exact=True,
    ).wait_for()
    assert placa.input_value() == 'ABC12'
    assert not any(path.startswith('/veiculos/placa/') for _, path, _ in calls)


def test_historico_veiculo_paginacao_pagamento_e_recuperacao_de_erro(browser_page):
    page, calls, _ = browser_page
    base = {
        'entrada': '2026-10-29T09:00:00', 'saida': '2026-10-29T10:20:00',
        'cliente_id': 7, 'cliente_nome': 'Cliente da entrada', 'vaga_numero': 'A-01',
        'operador_entrada': 'Ana Operadora', 'operador_saida': 'Bruno Operador',
        'valor_hora_aplicado': '10.00', 'valor_cobrado': '15.00',
        'pago_em': '2026-10-29T10:20:00', 'forma_pagamento': 'pix',
    }
    rows = [{**base, 'permanencia_id': number} for number in range(13, 2, -1)]
    rows[0].update(entrada='2026-10-30T09:00:00', saida=None, valor_cobrado=None,
                   pago_em=None, forma_pagamento=None, operador_saida=None)
    offsets = []

    def history(route):
        query = parse_qs(urlparse(route.request.url).query)
        offset = int(query['offset'][0])
        offsets.append(offset)
        if offset == 10 and offsets.count(10) == 1:
            route.fulfill(status=503, json={'detail': 'Histórico temporariamente indisponível.'})
        else:
            route.fulfill(json=rows[offset:offset + int(query['limite'][0])])

    page.route('**/veiculos/1/historico?*', history)
    entrar(page)
    page.locator('a[data-page="veiculos"]').click()
    page.get_by_role('textbox', name='Buscar pela placa completa').fill('ABC1D23')
    page.get_by_role('button', name='Buscar', exact=True).click()
    page.get_by_role('button', name='Histórico', exact=True).click()
    dialog = page.get_by_role('dialog')
    dialog.get_by_role('heading', name='Histórico do veículo').wait_for()
    dialog.get_by_text('No pátio', exact=True).wait_for()
    assert dialog.locator('.vehicle-movement').count() == 10
    aberta = dialog.locator('.vehicle-movement').first
    assert aberta.get_by_text('Calculado na saída', exact=True).is_visible()
    encerrada = dialog.locator('.vehicle-movement').nth(1)
    assert encerrada.get_by_text('1h 20min', exact=True).is_visible()
    assert encerrada.get_by_text('Cliente da entrada', exact=True).is_visible()
    assert encerrada.get_by_text('Bruno Operador', exact=True).is_visible()
    assert encerrada.get_by_text('R$\xa015,00', exact=True).is_visible()
    assert encerrada.get_by_text('Pix · 29/10/2026 às 10:20', exact=True).is_visible()
    dialog.get_by_role('button', name='Próxima →', exact=True).click()
    dialog.get_by_text('Histórico temporariamente indisponível.', exact=True).wait_for()
    dialog.get_by_role('button', name='Tentar novamente', exact=True).click()
    dialog.get_by_role('heading', name='Permanência #3', exact=True).wait_for()
    assert dialog.locator('.vehicle-movement').count() == 1
    assert dialog.get_by_role('button', name='Próxima →', exact=True).is_disabled()
    dialog.get_by_role('button', name='← Anterior', exact=True).click()
    dialog.get_by_text('No pátio', exact=True).wait_for()
    assert offsets == [0, 10, 10, 0]
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert dialog.evaluate('(el) => el.scrollWidth <= el.clientWidth')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS / 'historico-veiculo-mobile.png'), full_page=True)
    dialog.get_by_role('button', name='Fechar', exact=True).click()
    assert page.get_by_role('textbox', name='Buscar pela placa completa').input_value() == 'ABC1D23'
    assert not any(method != 'GET' and path.startswith('/veiculos') for method, path, _ in calls)


def test_historico_veiculo_sem_movimentacoes(browser_page):
    page, _, _ = browser_page
    page.route('**/veiculos/1/historico?*', lambda route: route.fulfill(json=[]))
    entrar(page)
    page.locator('a[data-page="veiculos"]').click()
    page.get_by_role('button', name='Histórico', exact=True).click()
    dialog = page.get_by_role('dialog')
    dialog.get_by_text('Nenhuma movimentação registrada.', exact=True).wait_for()
    assert dialog.get_by_role('button', name='← Anterior', exact=True).is_disabled()
    assert dialog.get_by_role('button', name='Próxima →', exact=True).is_disabled()


def test_historico_nao_reabre_apos_fechar_durante_carregamento(browser_page):
    page, _, _ = browser_page
    pending = []
    page.route('**/veiculos/1/historico?*', lambda route: pending.append(route))
    entrar(page)
    page.locator('a[data-page="veiculos"]').click()
    page.get_by_role('button', name='Histórico', exact=True).click()
    page.get_by_text('Carregando movimentações…', exact=True).wait_for()
    page.keyboard.press('Escape')
    assert not page.get_by_role('dialog').is_visible()
    with page.expect_response('**/veiculos/1/historico?*'):
        pending[0].fulfill(json=[])
    page.wait_for_function(
        "document.querySelector('[data-action=vehicle-history]').disabled === false"
    )
    assert not page.get_by_role('dialog').is_visible()


def test_nf_desmarcada_nao_envia_dados_fiscais(browser_page):
    page, calls, _ = browser_page
    entrar(page)
    page.get_by_role('button', name='Registrar saída ↗', exact=True).click()
    dialog = page.get_by_role('dialog')
    solicitar = dialog.get_by_role('checkbox', name='Cliente solicitou nota fiscal')
    assert not solicitar.is_checked()
    assert not dialog.get_by_label('CPF/CNPJ', exact=True).is_visible()
    solicitar.check()
    dialog.get_by_label('Nome ou razão social', exact=True).fill('Dados não enviados')
    dialog.get_by_label('CPF/CNPJ', exact=True).fill('529.982.247-25')
    solicitar.uncheck()
    assert dialog.get_by_label('CPF/CNPJ', exact=True).is_disabled()
    solicitar.check()
    assert dialog.get_by_label('CPF/CNPJ', exact=True).input_value() == '529.982.247-25'
    solicitar.uncheck()
    dialog.get_by_label('Forma de pagamento', exact=True).select_option('pix')
    dialog.get_by_role('button', name='Confirmar saída e pagamento', exact=True).click()
    page.get_by_text('Saída registrada: ABC1D23. Pagamento de R$\xa015,00 confirmado.', exact=True).wait_for()
    assert ('POST', '/permanencias/1/saida', {'forma_pagamento': 'pix'}) in calls


def test_nf_horista_valida_campos_e_preserva_pedido_na_falha(browser_page):
    page, _, _ = browser_page
    tentativas = []

    def sair(route):
        tentativas.append(route.request.post_data_json)
        if len(tentativas) == 1:
            route.fulfill(status=409, json={'detail': 'Falha ao registrar pedido de nota fiscal.'})
        else:
            route.fulfill(json={'valor': '15.00', 'nota_fiscal_solicitada': True})

    page.route('**/permanencias/1/saida', sair)
    entrar(page)
    page.get_by_role('button', name='Registrar saída ↗', exact=True).click()
    dialog = page.get_by_role('dialog')
    dialog.get_by_label('Forma de pagamento', exact=True).select_option('cartao')
    solicitar = dialog.get_by_role('checkbox', name='Cliente solicitou nota fiscal')
    solicitar.check()
    dialog.get_by_role('button', name='Confirmar saída e pagamento', exact=True).click()
    assert tentativas == []
    dialog.get_by_label('Nome ou razão social', exact=True).fill('Cliente Fiscal')
    dialog.get_by_label('CPF/CNPJ', exact=True).fill('123456789012')
    dialog.get_by_role('button', name='Confirmar saída e pagamento', exact=True).click()
    dialog.get_by_text(
        'Confira o CPF/CNPJ: use 11 dígitos para CPF ou 14 caracteres para CNPJ.', exact=True,
    ).wait_for()
    assert tentativas == []
    dialog.get_by_label('CPF/CNPJ', exact=True).fill('529.982.247-25')
    dialog.get_by_label('E-mail para envio (opcional)', exact=True).fill('cliente@example.com')
    dialog.get_by_label('Endereço (opcional)', exact=True).fill('Rua A, 10')
    dialog.get_by_role('button', name='Confirmar saída e pagamento', exact=True).click()
    dialog.get_by_text('Falha ao registrar pedido de nota fiscal.', exact=True).wait_for()
    assert solicitar.is_checked()
    assert dialog.get_by_label('CPF/CNPJ', exact=True).input_value() == '529.982.247-25'
    assert dialog.get_by_label('Nome ou razão social', exact=True).input_value() == 'Cliente Fiscal'
    dialog.get_by_role('button', name='Confirmar saída e pagamento', exact=True).click()
    page.get_by_text('Solicitação de nota fiscal salva para emissão posterior.', exact=False).wait_for()
    assert tentativas == [{'forma_pagamento': 'cartao', 'nota_fiscal': {
        'nome': 'Cliente Fiscal', 'documento': '52998224725',
        'email': 'cliente@example.com', 'endereco': 'Rua A, 10',
    }}] * 2


def test_nf_mensalidade_pode_ser_consultada_em_cobrancas(browser_page):
    page, _, _ = browser_page
    pagamentos = []
    consultas = []
    cobranca = {'id': 1, 'permanencia_id': None, 'contratacao_mensal_id': 1,
                'competencia': '2026-10-01', 'vencimento': '2026-10-16', 'valor': '300.00',
                'pago_em': None, 'forma_pagamento': None, 'nota_fiscal_solicitada': False}

    def pagar(route):
        pagamentos.append(route.request.post_data_json)
        cobranca.update(pago_em='2026-10-30T10:00:00', forma_pagamento='pix',
                        nota_fiscal_solicitada=True)
        route.fulfill(json=cobranca)

    def listar(route):
        consultas.append(route.request.url)
        route.fulfill(json=[cobranca])

    page.route('**/cobrancas?*', listar)
    page.route('**/cobrancas/1/pagar', pagar)
    page.route('**/cobrancas/1/nota-fiscal', lambda route: route.fulfill(json={
        'id': 7, 'cobranca_id': 1, 'nome': 'Empresa Cliente', 'documento': '00000000E08G12',
        'email': None, 'endereco': None, 'criado_em': '2026-10-30T10:00:00', 'criado_por': 1,
    }))
    entrar(page)
    page.locator('a[data-page="cobrancas"]').click()
    page.get_by_role('button', name='Receber', exact=True).click()
    dialog = page.get_by_role('dialog')
    dialog.get_by_role('checkbox', name='Cliente solicitou nota fiscal').check()
    dialog.get_by_label('Nome ou razão social', exact=True).fill('Empresa Cliente')
    dialog.get_by_label('CPF/CNPJ', exact=True).fill('00.000.000/e08g-12')
    dialog.get_by_label('Forma de pagamento', exact=True).select_option('pix')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert dialog.evaluate('(el) => el.scrollWidth <= el.clientWidth')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS / 'nota-fiscal-pagamento-mobile.png'), full_page=True)
    dialog.get_by_role('button', name='Confirmar pagamento', exact=True).click()
    page.get_by_role('button', name='Ver pedido de NF', exact=True).wait_for()
    assert pagamentos == [{'forma_pagamento': 'pix', 'nota_fiscal': {
        'nome': 'Empresa Cliente', 'documento': '00000000E08G12', 'email': None, 'endereco': None,
    }}]
    page.get_by_label('Situação do pagamento', exact=True).select_option('nota-fiscal')
    page.get_by_role('button', name='Ver pedido de NF', exact=True).click()
    dialog.get_by_role('heading', name='Solicitação de nota fiscal', exact=True).wait_for()
    dialog.get_by_text('Empresa Cliente', exact=True).wait_for()
    assert dialog.get_by_text('00000000E08G12', exact=True).is_visible()
    assert dialog.get_by_text('Não informado', exact=True).count() == 2
    assert any('nota_fiscal=true' in url for url in consultas)
