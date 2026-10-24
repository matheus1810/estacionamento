# Mationamento

Backend síncrono em Python **3.12.10**, FastAPI, SQLModel, MySQL e PyMySQL.
O frontend em HTML, CSS e JavaScript é servido pelo próprio FastAPI.
O SQL original na raiz continua sendo a referência para as oito tabelas.

## Instalação no Windows com Git Bash

Pré-requisitos: Python 3.12, Git Bash e MySQL **8.0.16 ou superior** com InnoDB.
Abra o Git Bash na raiz do projeto:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Se o Windows bloquear `ensurepip`, crie com `python -m venv --without-pip .venv`
e use o pip do Python instalado:

```bash
python -m pip --python .venv/Scripts/python.exe install -r requirements-dev.txt
source .venv/Scripts/activate
```

Edite `backend/.env` com host, porta, nome, usuário e senha reais do banco.
Defina `JWT_SECRET` com pelo menos 32 caracteres aleatórios, por exemplo com
`python -c "import secrets; print(secrets.token_urlsafe(48))"`. Guarde o resultado
apenas no `.env`, sem compartilhá-lo. Não existem usuários, senhas ou preços padrão.
Use aspas no `.env` para valores contendo `#`, espaços ou outros caracteres especiais.
A URL usa `URL.create`, então a senha do `.env` não deve ser escapada como URL.

O arquivo `.env` é resolvido a partir de `backend/`, independentemente da pasta
do terminal. Variáveis de ambiente têm precedência. Configurações são lidas
no início; reinicie o servidor após alterá-las.

## Preparar o MySQL

Importe uma única vez em banco novo. O script cria e seleciona `mationamento`;
não o execute sobre uma instalação existente sem verificar o estado do banco.
No cliente MySQL:

```bash
mysql -u root -p < ../mationamento.sql
```

Se `mysql` não estiver no PATH, use o executável instalado ou abra o script no
MySQL Workbench. Configure um usuário de aplicação com SELECT, INSERT e UPDATE
nas oito tabelas. Não há necessidade de permissões de exclusão ou DDL para a API.
O backend não executa `create_all`, não altera o esquema e não remove constraints.

Todas as datas DATETIME escritas pela aplicação usam `APP_TIMEZONE`, por padrão
`America/Sao_Paulo`, sem informação de fuso no MySQL. O relógio do host deve estar
correto. O JWT usa UTC. Valores monetários usam Decimal e DECIMAL(10,2).

## Primeiro operador e servidor

Com a virtualenv ativa, dentro de `backend`:

```bash
python -m scripts.criar_usuario
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O script pede nome, login e senha sem exibi-la. Recusa quando já existe qualquer
usuário e serializa execuções concorrentes com um lock nomeado MySQL. Somente
esse primeiro registro aceita `criado_por` vazio. Depois use a tela Operadores
ou `POST /usuarios` autenticado. Senhas são protegidas com Argon2.

Abra **http://127.0.0.1:8000** para usar as telas ou **http://127.0.0.1:8000/docs**
para explorar a API. A interface não precisa de npm ou de um servidor separado.

No `/docs`, execute `POST /auth/login` com JSON:

```json
{"login": "seu-login", "senha": "sua-senha"}
```

Copie `access_token`, clique **Authorize** e cole somente o token no campo Bearer.
Execute `GET /auth/me` para conferir. Cada requisição revalida se o operador
continua ativo. Não há cadastro público nem recuperação por e-mail.

## Teste manual do rotativo

O atendimento diário agora começa pelo campo de placa na visão geral. Digite a
placa e pressione Enter; Alt + P devolve o foco ao campo. Veículos no pátio abrem
a saída, mensalistas abrem a consulta de acesso e os demais abrem a entrada com
o veículo selecionado. A lista de horistas possui filtro por placa e rolagem.

Para uma placa nova, o formulário cadastra cliente e veículo e registra a entrada
por `POST /permanencias/cadastro-entrada`. Envie `cliente: {nome, telefone}` ou
`cliente_id` existente, além de placa, modelo, cor e vaga_id. As três gravações
acontecem em uma transação, com rollback em caso de conflito. Não aceita os dois
tipos de responsável simultaneamente. O botão Atualizar vagas livres mantém os
outros campos preenchidos para tentar novamente quando a disponibilidade mudar.

1. Crie o primeiro usuário e entre na tela de login (ou autorize no `/docs`).
2. Cadastre as tarifas em **Tarifas** (`POST /tarifas`). Ambos os valores devem ser positivos.
3. Cadastre uma vaga em **Vagas** (`POST /vagas`).
4. Cadastre um cliente em **Clientes**, com nome e telefone (`POST /clientes`).
5. Cadastre seu veículo em **Veículos** (`POST /veiculos`), com placa, modelo e cor.
6. Em **Visão geral**, registre a entrada selecionando o veículo e uma vaga disponível
   (`POST /permanencias`). Horário, cliente histórico, tarifa e operador vêm do backend.
7. Clique **Registrar saída**: a tela consulta `GET /permanencias/{id}/previa`.
8. Escolha Pix, dinheiro ou cartão e confirme (`POST /permanencias/{id}/saida`).
   A confirmação recalcula o valor e grava saída, cobrança e pagamento juntos.
9. Confira o registro em **Cobranças**. Uma segunda saída ou pagamento deve retornar 409.

Blocos de 30 minutos, mínimo de um bloco, sem tolerância: hora de R$10 e duração
de 1h20 resulta em R$15. A duração usa segundos e frações; dinheiro é arredondado
explicitamente em duas casas com ROUND_HALF_UP. O frontend nunca envia preço,
horário, duração ou operador para determinar a cobrança.

## Teste manual do mensalista

1. Cadastre tarifas, cliente ativo, veículo e vaga ativa.
2. Em **Mensalistas**, crie a contratação (`POST /contratacoes`). O dia de início
   define os vencimentos. Contratos futuros só geram cobrança quando o período começa.
3. Abra **Cobranças**. A tela executa `POST /cobrancas/atualizar-mensalidades`
   antes do `GET /cobrancas`. Repetir a atualização não duplica contratação + competência.
4. Consulte o acesso pela placa (`POST /cobrancas/consultar-acesso`). No dia do
   vencimento, uma cobrança pendente ainda não bloqueia; no dia seguinte bloqueia.
5. Receba a mensalidade por `POST /cobrancas/{id}/pagar`, com uma forma de pagamento.
   Atraso não desloca os períodos. Qualquer dívida mensal do cliente bloqueia
   o acesso, inclusive dívida em outra vaga ou contrato encerrado.
   A consulta mostra as mensalidades vencidas e permite recebê-las ali mesmo.
   Depois de cada recebimento o acesso é reavaliado. Se essa nova consulta falhar,
   o pagamento continua confirmado e a tela permite conferir o acesso novamente.
6. Tente registrar entrada horista na vaga reservada: deve retornar 409, mesmo vazia.
7. Cancele a renovação por `POST /contratacoes/{id}/cancelar`. A reserva termina
   no fim do último período já iniciado, inclusive quando há dívida ou nenhum
   pagamento, conforme decisão aprovada. Todas as cobranças são preservadas.
8. Atualize novamente as mensalidades e confira: não devem existir novos períodos
   começando depois da data final. Ainda é possível quitar as dívidas existentes.

Exemplo: início 16/10, vencimento 16/10, cobertura até 15/11 e próxima renovação
em 16/11. Cancelar em 30/10 mantém a reserva até 15/11, sem devolução ou crédito.
O dia 31 é limitado ao último dia de fevereiro e volta a 31 em março. Competência
usa dia 01 do mês do início do período. Cada vaga contratada tem sua própria cobrança.
Sem pedido de cancelamento, a contratação continua renovando mesmo em atraso;
a dívida não libera a vaga automaticamente.

Cancelamento antes do início do contrato permanece recusado com 409: o SQL exige
`data_fim >= data_inicio` e não possui campo de cancelamento antecipado. Esse caso
de negócio não foi definido. Não há edição arbitrária ou exclusão de contratos,
permanências ou cobranças.

## Organização e transações

`config.py`: configurações e relógio local. `database.py`: engine, sessão por
requisição, commit e rollback. `models.py`: tabelas. `schemas.py`: entradas e
respostas explícitas. `auth.py`: Argon2, JWT e operador autenticado.
`regras_estacionamento.py`: períodos, geração, disponibilidade e cobrança.
Rotas contêm consultas e alterações simples, sem camada genérica de CRUD.

Ordem de bloqueios: vaga → veículo (quando houver) → cliente → contratos por id
→ permanência/cobranças. Operações que usam apenas parte dessa sequência seguem
a mesma ordem relativa. Entrada e contratação bloqueiam a mesma vaga; entrada
também bloqueia o veículo. A geração bloqueia os contratos por id; pagamento
bloqueia a cobrança. Desativações de usuários bloqueiam os usuários por id para
proteger o último ativo. Usa-se READ COMMITTED e revalidação após bloqueio.

Consultas de autenticação compartilham a sessão da requisição. As rotas aproveitam
a transação implícita, sem `session.begin()` sobre uma transação já iniciada.
Auxiliares não fazem commits. Falhas têm rollback; operações finalizadas fazem
um commit. Deadlock ou timeout de bloqueio retorna conflito e permite nova tentativa.
As listagens GET não gravam. Limite máximo: 100; paginação por `offset` e `limite`.

Usuários, clientes e vagas são desativados por PATCH; o histórico permanece.
Campos desconhecidos e de auditoria são recusados nas entradas. Campos obrigatórios
não aceitam texto vazio nem apenas espaços. Edições não aceitam null. A atualização
preenche data e autor juntos e mantém os campos de criação.

## Testes

```bash
python -m pytest -m 'not browser' -q
```

Testes unitários cobrem blocos, frações de segundo, dinheiro, vencimentos,
competência, cancelamento com/sem dívida, atraso, validações e autenticação.
Os testes de autenticação usam sessão simulada; não afirmam validar o MySQL.

Para integração, crie um banco **separado**, por exemplo `mationamento_test`.
Gere uma cópia do SQL apenas para esse banco:

```bash
python -c "from pathlib import Path; p=Path('../mationamento.sql').read_text(encoding='utf-8'); Path('schema_test.sql').write_text(p.replace('CREATE DATABASE IF NOT EXISTS mationamento', 'CREATE DATABASE IF NOT EXISTS mationamento_test').replace('USE mationamento;', 'USE mationamento_test;'), encoding='utf-8')"
mysql -u root -p < schema_test.sql
```

Configure `TEST_DATABASE_URL` somente no terminal, com driver `mysql+pymysql` e
nome terminando em `_test`. Use credenciais do banco de teste e escape caracteres
especiais nessa URL (diferente do `.env`, que usa campos separados). Então:

```bash
python -m pytest -m mysql -q
```

Sem TEST_DATABASE_URL, os testes MySQL são pulados. Eles usam o SQL original
importado, savepoints para commits da API e rollback externo por teste, sem
excluir tabelas nem usar SQLite. Não aponte para desenvolvimento. Os cenários
cobrem vaga ocupada/reservada, mensalidade única, acesso, saída e pagamento
repetidos, histórico do cliente e cancelamento preservando dívidas. Essa suíte
funcional não substitui um ensaio de concorrência com conexões independentes.

Para verificar as telas com API simulada no Edge instalado:

```bash
python -m pip install -r requirements-browser.txt
python -m pytest -m browser -q
```

Os screenshots ficam em `backend/.artifacts/` e não são versionados. O teste
não cadastra dados no MySQL. Consulte também [frontend/README.md](../frontend/README.md).

## Versões e verificação neste ambiente

Dependências instaladas e verificadas com `pip check`: FastAPI 0.156.4,
SQLModel 0.0.48, SQLAlchemy 2.1.5, PyMySQL 1.2.3, Pydantic 2.14.1,
Pydantic Settings 2.16.1, Argon2 CFFI 25.1.0, PyJWT 2.15.1,
Uvicorn 0.54.0, tzdata 2026.5, cryptography 50.0.2, pytest 9.1.1 e httpx 0.28.1.
Os arquivos requirements registram essas versões. Playwright 1.64.0 é opcional.

Na primeira entrega, o banco ainda não estava configurado. Na atualização de
atendimento do operador, foram executados **32 testes unitários e de interface**
e **4 testes de integração** em um banco temporário exclusivo do MariaDB 10.4.32
do XAMPP, com o SQL original. O banco temporário foi removido após os testes;
os dados do banco da aplicação foram preservados. Isso não valida um servidor
MySQL 8 separado nem substitui um teste de concorrência com conexões independentes.

As telas foram verificadas no Edge em desktop e celular com API simulada.
O serviço real do FastAPI também foi verificado para entrega do HTML, CSS e JS
por TestClient. O ambiente emitiu um aviso de depreciação do httpx no TestClient;
as verificações concluíram normalmente.
