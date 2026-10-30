from fastapi.testclient import TestClient

from app.main import app


def test_interface_e_assets_sao_servidos_pelo_fastapi():
    # Não inicia lifespan, não abre banco e não precisa de credenciais.
    client = TestClient(app)
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'Mationamento' in resposta.text
    assert client.get('/assets/app.js').status_code == 200
    assert client.get('/assets/styles.css').status_code == 200
    # Módulos nativos exigem um tipo JavaScript válido na resposta HTTP.
    assert 'type="module"' in resposta.text
    modulo = client.get('/assets/js/navegacao.js')
    assert modulo.status_code == 200
    assert modulo.headers['content-type'].split(';')[0] in (
        'text/javascript',
        'application/javascript',
    )
    estilo = client.get('/assets/css/base.css')
    assert estilo.status_code == 200
    assert estilo.headers['content-type'].startswith('text/css')
    assert (
        'senha_hash'
        not in app.openapi()['components']['schemas']['UsuarioSaida']['properties']
    )
