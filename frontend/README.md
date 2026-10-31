# Interface do Mationamento

HTML, CSS e JavaScript sem etapa de build. O FastAPI serve `index.html` em `/`
e os arquivos estáticos em `/assets`. Abra `http://127.0.0.1:8000` depois de
configurar e iniciar o backend conforme o [guia de instalação](../backend/README.md).
Não abra o HTML diretamente pelo sistema de arquivos.

## Organização do código

O JavaScript usa módulos nativos (`import` e `export`). O navegador carrega
`app.js`, que registra os eventos, inicia o relógio e restaura a sessão. Não é
necessário instalar Node.js ou executar npm para usar o sistema.

```text
frontend/
├── index.html                 Estrutura fixa: login, menu, conteúdo e janela
├── app.js                     Inicialização da aplicação
├── styles.css                 Importação dos arquivos CSS, na ordem de aplicação
├── css/
│   ├── base.css               Paleta, fontes, estilos globais e utilitários
│   ├── layout.css             Menu lateral, cabeçalho e área de trabalho
│   ├── componentes.css        Botões, cartões, tabelas, formulários e janelas
│   ├── login.css              Aparência da tela de login
│   ├── responsivo.css         Ajustes para desktop, tablet e celular
│   ├── atendimento.css        Atendimento por placa e lista de horistas
│   ├── select-busca.css       Campo de seleção com busca integrada
│   ├── historico-veiculo.css  Cartões do histórico de permanências
│   ├── nota-fiscal.css        Campos opcionais do pedido de nota
│   └── validacao.css          Destaques e mensagens de erro por campo
└── js/
    ├── api.js                 Requisições HTTP e tratamento de erros
    ├── autenticacao.js        Login, logout e restauração da sessão
    ├── sessao.js              Leitura e atualização do token da aba
    ├── estado.js              Tela, filtros, paginação e dados em memória
    ├── navegacao.js           Rotas pelo hash e renderização das telas
    ├── eventos.js             Eventos da página e ações dos botões
    ├── telas/                 Consulta de dados e HTML de cada tela
    │   ├── operacao.js
    │   ├── clientes.js
    │   ├── veiculos.js
    │   ├── vagas.js
    │   ├── mensalistas.js
    │   ├── cobrancas.js
    │   ├── tarifas.js
    │   └── operadores.js
    ├── fluxos/                Formulários e operações realizadas pelo usuário
    │   ├── atendimento.js     Consulta de placa, cadastro rápido, entrada e saída
    │   ├── clientes.js        Cadastro e edição de clientes
    │   ├── veiculos.js        Cadastro e edição de veículos
    │   ├── historico-veiculo.js  Histórico paginado de entradas e saídas
    │   ├── nota-fiscal.js     Consulta dos dados para emissão posterior
    │   ├── vagas.js           Cadastro e edição de vagas
    │   ├── mensalistas.js     Contratação, acesso, pagamento e cancelamento
    │   ├── operadores.js      Cadastro e edição de operadores
    │   └── conclusao.js       Fecha a janela, avisa e atualiza a tela
    ├── ui/                    Componentes reutilizáveis da interface
    │   ├── componentes.js     Títulos, tabelas, filtros e paginação
    │   ├── formularios.js     Campos de texto e seletores
    │   ├── modal.js           Abertura, fechamento e envio da janela
    │   ├── select-busca.js    Busca, teclado e seleção de registros
    │   ├── nota-fiscal.js     Campos condicionais e dados do pagamento
    │   ├── validacao-formulario.js  Mensagens locais e erros retornados pela API
    │   ├── notificacoes.js    Mensagens temporárias
    │   └── icones.js          Ícones SVG
    └── utils/
        ├── dom.js            Seleção de elementos e escape de texto HTML
        ├── formatacao.js     Apresentação de dinheiro, datas e duração
        └── validacao-campos.js  Regras de nome, telefone, placa, modelo e cor
```

### Por onde começar a leitura

Leia `app.js` para entender a inicialização. Depois siga `navegacao.js` até um
arquivo em `telas/`. Para entender o que acontece ao clicar em um botão, procure
seu `data-action` em `eventos.js` e siga a função correspondente em `fluxos/`.

Por exemplo, a listagem de clientes fica em `telas/clientes.js`, enquanto o
formulário de cadastro e a requisição para salvar ficam em `fluxos/clientes.js`.
Ambos usam componentes de `ui/` e acessam o backend por `api.js`.

`estado.js` guarda os dados usados pela interface. `sessao.js` centraliza a
gravação do token. Quando a API responde 401, `api.js` emite `session-expired`,
e `autenticacao.js` encerra a sessão e exibe o login.

### Como fazer alterações

- **Mudar o conteúdo de uma tela:** edite seu arquivo em `js/telas/`.
- **Mudar um formulário ou uma operação:** edite seu arquivo em `js/fluxos/`.
- **Mudar um componente compartilhado:** procure em `js/ui/`.
- **Adicionar um botão:** defina `data-action` no HTML e sua ação em `js/eventos.js`.
- **Adicionar uma tela:** crie a função em `js/telas/`, importe-a em
  `js/navegacao.js` e inclua a rota no menu `nav` e no mapa usado por `render()`.
- **Mudar o visual:** edite o CSS da responsabilidade correspondente. A ordem
  dos imports de `styles.css` determina a precedência das regras.

Os comentários `/* HTML */` identificam trechos HTML dentro do JavaScript e
permitem sua formatação pelo editor. A configuração de formatação está em
`.prettierrc.json`. As regras de preço, disponibilidade e permissões continuam
no backend; os módulos do front-end apresentam os dados e enviam as ações.

### Seletores com busca

`ui/select-busca.js` transforma selects marcados com `data-searchable` em
campos com busca local. A inicialização acontece ao renderizar uma tela ou abrir
uma janela. `formularios.js` marca os campos de cliente, veículo e vaga; filtros
podem ativar a busca com o terceiro argumento de `selectFilter()`.

O select original guarda o ID enviado ao backend e mantém a validação de campo
obrigatório. O texto digitado serve apenas para filtrar as opções. Ao substituir
as opções de um select já renderizado, chame `refreshSearchableSelect(select)`
para atualizar o campo, como faz o fluxo de atualização de vagas.

## Telas

- Login e identificação do operador, com saída da conta.
- Clientes, veículos e cadastro rápido validam os campos antes do envio. O
  telefone aceita fixo ou celular com DDD, com pontuação e prefixo `+55`
  opcionais; é salvo como DDD e número, apenas dígitos. Nomes de clientes aceitam
  apenas letras, espaços, apóstrofos e hífens, com acentos e sem números;
  modelos aceitam letras e números, como `F-150` e `208`; cores são informadas
  por extenso. Erros aparecem junto ao campo, sem apagar os dados, e o foco vai
  para o primeiro campo inválido. Mensagens da API seguem o mesmo comportamento.
- Pagamentos de horistas e mensalistas permitem marcar **Cliente solicitou nota
  fiscal**. Os campos aparecem apenas quando marcado. Nome ou razão social e
  CPF/CNPJ são obrigatórios; e-mail e endereço são opcionais. O pedido é salvo
  com o pagamento para emissão posterior. Em **Cobranças**, filtre por **Com
  solicitação de NF** e use **Ver pedido de NF** para consultar os dados.
- Na tela **Veículos**, busque a placa e clique em **Histórico** para consultar
  entradas, saídas, vaga, cliente da entrada, operadores, tarifa e pagamento.
  As movimentações aparecem da mais recente para a mais antiga, em páginas de
  10 registros. Permanências abertas aparecem como **No pátio**. A consulta
  preserva a busca e os filtros da lista de veículos.
- Seletores de clientes, veículos, vagas e responsável do cadastro rápido com
  busca integrada. Digite parte do nome, placa, código ou telefone quando
  exibido na opção. A busca ignora acentos, espaços e hífens. Use as setas e
  Enter para escolher; Escape ou Tab descartam a busca e mantêm a seleção.
  O filtro de clientes na tela Veículos também permite buscar.
- Visão geral: indicadores reais, mapa das primeiras 24 vagas, lista de horistas,
  entrada, prévia de cobrança e confirmação da saída com pagamento.
- Atendimento por placa na visão geral (Enter para consultar; Alt + P para focar).
  Um veículo no pátio abre a saída; um mensalista abre o acesso e suas pendências;
  um horista cadastrado abre a entrada com o veículo selecionado.
- Placa nova abre cadastro de cliente e veículo junto com a entrada. É possível
  escolher um cliente existente. Tudo é salvo em uma transação; conflitos
  preservam os campos na tela e não deixam cadastros parciais no banco.
- A lista de horistas mostra todos os carros presentes em uma área com rolagem
  e filtro por placa. Após concluir uma operação, o foco volta ao atendimento.
- Clientes: busca por nome, filtro de situação, cadastro, edição e desativação.
- Veículos: consulta pela placa completa, filtro por cliente, cadastro e edição.
- Vagas: cadastro, disponibilidade, edição, ativação e desativação.
- Mensalistas: contratação, consulta de acesso pela placa e cancelamento da renovação.
- Cobranças: atualização explícita das mensalidades antes de listar, filtros e recebimento.
  Na consulta mensalista, cobranças vencidas podem ser recebidas sem trocar de
  tela. Cada recebimento é integral e provoca uma nova verificação do acesso.
- Tarifas: cadastro inicial e alteração dos valores gerais.
- Operadores: cadastro autenticado, edição, troca de senha e desativação.

As listagens de cadastros e cobranças usam páginas de 20 registros. Os seletores carregam as páginas
necessárias para mostrar os cadastros disponíveis. O mapa e os indicadores
atualizam ao abrir a visão geral ou após uma operação. Não há atualização automática
em segundo plano. A API sempre revalida disponibilidade, permissões e valores.

O token fica em `sessionStorage`, restrito à sessão da aba. Senhas não são salvas
pelo código da interface. Ao sair do documento (inclusive ao atualizar a página),
o evento `pagehide` encerra a sessão e limpa o conteúdo autenticado. Retornar pelo
histórico exige novo login, inclusive quando o navegador restaura o documento do
cache. Navegar pelos menus internos mantém a sessão e substitui o hash da URL
com `history.replaceState`, sem acrescentar entradas ao histórico. Assim, Voltar
retorna ao site anterior mesmo após usar vários menus. O encerramento remove o
token da interface; o JWT emitido continua válido no servidor até sua expiração.
Nenhum dado de demonstração é inserido no sistema.
Campos de auditoria e valores finais são controlados pelo backend.

O layout se adapta a celular, tablet e desktop. Formulários possuem labels,
diálogos nativos, foco de teclado e mensagens de erro. As fontes externas são
opcionais; o sistema usa Arial quando não há internet.

## Verificação no navegador

O teste opcional `backend/tests/test_frontend.py` usa Playwright e o Edge local,
com respostas de API simuladas somente no teste. Isso verifica a interface e
o contrato das requisições; não valida persistência ou concorrência MySQL.

```bash
cd backend
python -m pip install -r requirements-browser.txt
python -m pytest tests/test_frontend.py -q
```

Defina `BROWSER_EXECUTABLE` para testar outro Chromium instalado. Não é necessário
instalar Node.js, npm ou um navegador adicional.
