# Interface do Mationamento

HTML, CSS e JavaScript sem etapa de build. O FastAPI serve `index.html` em `/`
e os arquivos estáticos em `/assets`. Abra `http://127.0.0.1:8000` depois de
configurar e iniciar o backend conforme o [guia de instalação](../backend/README.md).
Não abra o HTML diretamente pelo sistema de arquivos.

## Telas

- Login e identificação do operador, com saída da conta.
- Visão geral: indicadores reais, mapa das primeiras 24 vagas, lista de horistas,
  entrada, prévia de cobrança e confirmação da saída com pagamento.
- Clientes: busca por nome, filtro de situação, cadastro, edição e desativação.
- Veículos: consulta pela placa completa, filtro por cliente, cadastro e edição.
- Vagas: cadastro, disponibilidade, edição, ativação e desativação.
- Mensalistas: contratação, consulta de acesso pela placa e cancelamento da renovação.
- Cobranças: atualização explícita das mensalidades antes de listar, filtros e recebimento.
- Tarifas: cadastro inicial e alteração dos valores gerais.
- Operadores: cadastro autenticado, edição, troca de senha e desativação.

As listagens usam páginas de 20 registros. Os seletores carregam as páginas
necessárias para mostrar os cadastros disponíveis. O mapa e os indicadores
atualizam ao abrir a visão geral ou após uma operação. Não há atualização automática
em segundo plano. A API sempre revalida disponibilidade, permissões e valores.

O token fica em `sessionStorage`, restrito à sessão da aba. Senhas não são salvas
pelo código da interface. Nenhum dado de demonstração é inserido no sistema.
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
