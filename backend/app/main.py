from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, OperationalError

from .auth import router as auth_router
from .config import get_settings
from .routers import clientes, cobrancas, contratacoes, permanencias, tarifas, usuarios, vagas, veiculos


@asynccontextmanager
async def lifespan(app):
    get_settings()  # Falha cedo se a configuração obrigatória estiver ausente.
    yield


app = FastAPI(title='Mationamento', version='1.0.0', lifespan=lifespan,
              description='Controle de estacionamento rotativo e mensalistas.')
for router in (auth_router, usuarios.router, clientes.router, veiculos.router,
               vagas.router, tarifas.router, contratacoes.router,
               permanencias.router, cobrancas.router):
    app.include_router(router)

frontend_dir = Path(__file__).resolve().parents[2] / 'frontend'
if frontend_dir.is_dir():
    app.mount('/assets', StaticFiles(directory=frontend_dir), name='assets')

    @app.get('/', include_in_schema=False)
    def interface():
        return FileResponse(frontend_dir / 'index.html')


@app.exception_handler(RequestValidationError)
def entrada_invalida(request: Request, exc: RequestValidationError):
    # Não reproduz valores de entrada: podem conter senha ou outros dados privados.
    return JSONResponse(status_code=422, content={
        'detail': 'Dados inválidos. Confira os campos e formatos documentados.',
        'campos': ['.'.join(str(p) for p in e['loc']) for e in exc.errors()],
    })


@app.exception_handler(IntegrityError)
def conflito(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={'detail': 'Operação em conflito com os dados cadastrados.'})


@app.exception_handler(OperationalError)
def banco_indisponivel(request: Request, exc: OperationalError):
    if exc.orig.args[0] in (1205, 1213):
        return JSONResponse(status_code=409, content={'detail': 'Operação concorrente. Tente novamente.'})
    return JSONResponse(status_code=503, content={'detail': 'Banco de dados indisponível.'})


@app.exception_handler(Exception)
def erro_interno(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={'detail': 'Erro interno ao processar a operação.'})
