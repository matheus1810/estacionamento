// Regras compartilhadas pelos formulários de cliente, veículo e cadastro rápido.

const phoneMessage = 'Telefone: informe um fixo ou celular com DDD. Ex.: (11) 91234-5678.';

function normalizePhone(value) {
  const text = value.trim();
  if (!/^\+?[0-9() .-]+$/.test(text) || (text.startsWith('+') && !text.startsWith('+55'))) {
    throw new Error(phoneMessage);
  }
  let digits = text.replace(/\D/g, '');
  if ([12, 13].includes(digits.length) && digits.startsWith('55')) digits = digits.slice(2);
  if (!/^[1-9]{2}(?:[2-5][0-9]{7}|9[0-9]{8})$/.test(digits) || new Set(digits).size === 1) {
    throw new Error(phoneMessage);
  }
  return digits;
}

function registrationError(name, value, rule = '') {
  if (rule === 'nome-cliente') {
    const normalized = value.normalize('NFC');
    if (!/\p{L}/u.test(normalized) || !/^[\p{L} '’\-]+$/u.test(normalized)) {
      return 'Nome: use apenas letras, espaços, apóstrofos e hífens. Números não são permitidos.';
    }
  }
  if (name === 'telefone') {
    try {
      normalizePhone(value);
    } catch (error) {
      return error.message;
    }
  }
  if (name === 'nome' && (!/\p{L}/u.test(value) || /[\x00-\x1f\x7f]/.test(value))) {
    return 'Nome: informe um nome com letras; números ou símbolos sozinhos não são aceitos.';
  }
  if (name === 'modelo' && (!/[\p{L}\p{N}]/u.test(value) || /[\x00-\x1f\x7f]/.test(value))) {
    return 'Modelo: informe o modelo do veículo. Ex.: Fiat Argo ou 208.';
  }
  if (name === 'cor' && (!/\p{L}/u.test(value) || !/^[\p{L} /'’\-]+$/u.test(value))) {
    return 'Cor: informe a cor por extenso, sem números. Ex.: Branco ou Prata/Preto.';
  }
  if (name === 'placa') {
    const plate = value.replace(/[\s-]/g, '').toUpperCase();
    if (plate.length !== 7) {
      return `Você digitou ${plate.length} caracteres. A placa deve ter 7, sem contar espaços ou hífens. Confira a digitação. Exemplos: ABC1234 ou ABC1D23.`;
    }
    if (!/^[A-Z]{3}(?:\d{4}|\d[A-Z]\d{2})$/.test(plate)) {
      return 'O formato da placa não foi reconhecido. Use ABC1234 (3 letras e 4 números) ou ABC1D23 (Mercosul).';
    }
  }
  return '';
}

export { normalizePhone, registrationError };
