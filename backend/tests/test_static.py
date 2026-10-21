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
    assert 'senha_hash' not in app.openapi()['components']['schemas']['UsuarioSaida']['properties']
