// Token mantido somente durante a sessão da aba.

const TOKEN_KEY = 'mationamento_token';
let token = sessionStorage.getItem(TOKEN_KEY);

function saveToken(value) {
  token = value;
  if (value) sessionStorage.setItem(TOKEN_KEY, value);
  else sessionStorage.removeItem(TOKEN_KEY);
}

export { token, saveToken };
