"""Navegador real, API simulada: verifica telas e requisições, não o MySQL."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse

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
    dialog.get_by_label('Veículo / cliente').select_option('1')
    dialog.get_by_label('Vaga disponível').select_option('1')
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
