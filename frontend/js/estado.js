// Estado compartilhado da interface; não contém regras de negócio.

const state = {
  user: null,
  page: 'operacao',
  offset: 0,
  limit: 20,
  query: '',
  filter: '',
  cache: {},
  renderId: 0,
  atendimento: null,
};

export { state };
