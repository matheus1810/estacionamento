# Mationamento

Backend síncrono em Python **3.12.10**, FastAPI, SQLModel, MySQL e PyMySQL.
O frontend em HTML, CSS e JavaScript é servido pelo próprio FastAPI.
O SQL original na raiz continua sendo a referência para as oito tabelas principais.
A migração em `migrations/` adiciona os pedidos de nota fiscal.

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
nas tabelas principais e na tabela de pedidos de nota. Não há necessidade de
permissões de exclusão ou DDL para a API. O servidor não executa `create_all`,
não altera o esquema e não remove constraints.

### Preparar solicitações de nota fiscal

Depois de importar o SQL inicial, execute uma vez, dentro de `backend`, com
acesso autorizado a criar tabelas no banco configurado:

```bash
python -m scripts.preparar_notas_fiscais
```

O comando executa apenas `migrations/001_solicitacoes_nota_fiscal.sql`. Ele cria
`solicitacoes_nota_fiscal` caso ela ainda não exista, sem alterar ou excluir os
registros atuais. Em instalações existentes, execute somente esse comando;
não reimporte o SQL inicial. A API precisa de SELECT e INSERT na nova tabela.

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

Se algum dado for inválido, o comando indica o campo (Nome, Login ou Senha) e
a correção necessária, sem mostrar a senha digitada. A senha deve ter de 8 a
128 caracteres e não pode conter apenas espaços. Erros do `.env` são apresentados
separadamente, com o nome da configuração e sem exibir seus valores.

Abra **http://127.0.0.1:8000** para usar as telas ou **http://127.0.0.1:8000/docs**
para explorar a API. A interface não precisa de npm ou de um servidor separado.

No `/docs`, execute `POST /auth/login` com JSON:

```json
{"login": "seu-login", "senha": "sua-senha"}
```

Copie `access_token`, clique **Authorize** e cole somente o token no campo Bearer.
Execute `GET /auth/me` para conferir. Cada requisição revalida se o operador
continua ativo. Não há cadastro público nem recuperação por e-mail.

## Recuperar a senha do próprio usuário

Com acesso autorizado ao terminal local e ao banco configurado no `.env`, execute
dentro de `backend` (substitua o login, se necessário):

```bash
python -m scripts.redefinir_senha --login matheus
```

Digite e confirme uma nova senha de 8 a 128 caracteres. Os caracteres não aparecem
no terminal. A senha recebe hash Argon2 e a atualização da própria conta preenche
a auditoria com seu ID. O comando não cria usuários nem reativa contas inativas.
Este procedimento é uma recuperação administrativa local, autorizada por quem
tem acesso à configuração do banco; não há endpoint público de recuperação.

## Teste manual do rotativo

### Pedido opcional de nota fiscal

Na saída horista ou no recebimento de mensalidade, marque **Cliente solicitou
nota fiscal**. Nome ou razão social e CPF/CNPJ são obrigatórios apenas quando
marcado; e-mail e endereço são opcionais. Ao desmarcar, os campos ficam
desabilitados e não são enviados.

Os endpoints de pagamento aceitam `nota_fiscal` opcional:

```json
{
  "forma_pagamento": "pix",
  "nota_fiscal": {
    "nome": "Cliente",
    "documento": "52998224725",
    "email": null,
    "endereco": null
  }
}
```

O pedido e o pagamento são gravados na mesma transação. Uma falha no pedido
reverte também o pagamento e a saída. A cobrança retorna
`nota_fiscal_solicitada`; sua listagem permite filtrar por `nota_fiscal=true`.
`GET /cobrancas/{id}/nota-fiscal` consulta os dados para emissão posterior,
com autenticação de operador. A listagem de cobranças não expõe documento,
e-mail ou endereço: esses dados aparecem somente na consulta do pedido.

Em **Cobranças**, use **Com solicitação de NF** e **Ver pedido de NF**. O pedido
não emite nota, não envia e-mail e não representa confirmação de emissão.
A validação confere formato e tamanho do documento, sem consultar o cadastro
fiscal nem confirmar sua titularidade. O CNPJ aceita letras nas primeiras
12 posições, conforme a [documentação da Receita Federal](https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/documentos-tecnicos/cnpj/manual-dv-cnpj.pdf).

### Histórico do veículo

Na tela **Veículos**, consulte a placa e clique em **Histórico**. A consulta usa
`GET /veiculos/{veiculo_id}/historico?offset=0&limite=20`, com autenticação de
operador, limite máximo de 100 e ordenação por entrada e ID decrescentes.

Cada registro inclui entrada, saída, vaga, operadores, tarifa aplicada, valor
cobrado e pagamento. O cliente vem da permanência, preservando o vínculo da
entrada após uma troca de responsável pelo veículo. Valores cobrados são lidos
da cobrança gravada; permanências abertas não exibem estimativa de preço.

O histórico consulta as tabelas existentes e não exige alteração do banco.
Inclui permanências horistas já registradas. A consulta de acesso de mensalistas
não registra passagens físicas, portanto não aparece como entrada ou saída.

### Atendimento

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

### Validação dos cadastros

`validacao_campos.py` centraliza as regras aplicadas pelos schemas de criação,
edição e cadastro rápido. Telefone deve ter DDD e número de fixo (10 dígitos ao
todo) ou celular (11 dígitos ao todo). Pontuação e o prefixo `+55` são aceitos;
o armazenamento usa apenas DDD e número. A regra de formato segue o
[plano de numeração da Anatel](https://www.gov.br/anatel/pt-br/regulado/numeracao/plano-de-numeracao-brasileiro)
e não confirma se o número está ativo.

Nomes de clientes aceitam apenas letras, espaços, apóstrofos e hífens, incluindo
acentos. Números são rejeitados também na edição e no cadastro rápido. A razão
social da solicitação de nota fiscal mantém sua regra própria. Modelo deve conter letras ou números (por exemplo,
`F-150` ou `208`); cor deve ser escrita por extenso, sem números. As duas formas
brasileiras de placa continuam aceitas. Limites de tamanho e campos obrigatórios
também são conferidos pelo servidor, independentemente da interface.

Respostas 422 mantêm `detail` e `campos` e incluem `erros`, com pares `campo` e
`mensagem` em português. Caminhos aninhados como `cliente.telefone` permitem
destacar o campo do cadastro rápido. As mensagens não reproduzem valores de
entrada, senhas, exceções internas ou detalhes SQL. `erros_validacao.py` faz a
conversão das falhas para essas mensagens.

### Mapa dos arquivos

```text
backend/
├── app/
│   ├── main.py                   Inicialização, rotas e arquivos do front-end
│   ├── config.py                 Configuração do .env e relógio local
│   ├── database.py               Conexão, sessão e transações
│   ├── auth.py                   Login, senhas e validação do token
│   ├── models.py                 Tabelas principais e pedidos de nota fiscal
│   ├── schemas.py                Campos e validações das entradas e respostas
│   ├── validacao_campos.py        Regras dos campos de cadastro
│   ├── erros_validacao.py         Respostas de validação sem expor valores
│   ├── regras_estacionamento.py   Cálculos e regras compartilhadas
│   ├── notas_fiscais.py           Pedidos de nota na transação do pagamento
│   └── routers/                  Endpoints separados por recurso
│       ├── clientes.py
│       ├── veiculos.py
│       ├── vagas.py
│       ├── usuarios.py
│       ├── tarifas.py
│       ├── permanencias.py
│       ├── contratacoes.py
│       └── cobrancas.py
├── scripts/                      Comandos administrativos executados no terminal
├── migrations/                   Extensões do esquema para bancos existentes
└── tests/                        Testes unitários, de integração e de navegador
```

Para acompanhar uma operação, comece pela rota em `app/routers/`. O parâmetro
`dados` usa um schema de `schemas.py`, `session` permite consultar e gravar os
modelos de `models.py`, e `usuario` vem da autenticação em `auth.py`. As regras
compartilhadas ficam em `regras_estacionamento.py`. A rota confirma a operação
com `salvar(session)`, definido em `database.py`.

Por exemplo, uma entrada horista começa em `routers/permanencias.py`; os campos
permitidos estão em `PermanenciaCriar`, e a disponibilidade da vaga é verificada
pelas regras compartilhadas. Para acompanhar o mesmo atendimento no navegador,
consulte o [mapa do front-end](../frontend/README.md#organização-do-código).

### Regras de transação

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
mysql -u root -p mationamento_test < migrations/001_solicitacoes_nota_fiscal.sql
```

Configure `TEST_DATABASE_URL` somente no terminal, com driver `mysql+pymysql` e
nome terminando em `_test`. Use credenciais do banco de teste e escape caracteres
especiais nessa URL (diferente do `.env`, que usa campos separados). Então:

```bash
python -m pytest -m mysql -q
```

Sem TEST_DATABASE_URL, os testes MySQL são pulados. Eles usam o SQL original
e a migração de pedidos de nota, savepoints para commits da API e rollback externo por teste, sem
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
