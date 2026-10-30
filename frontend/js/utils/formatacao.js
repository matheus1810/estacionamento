// Apresentação de valores e datas. Os preços são calculados pelo backend.

const money = (value) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value));
const localDate = (value) =>
  value ? value.split('T')[0].split('-').reverse().join('/') : 'Sem encerramento';
const localTime = (value) => (value ? value.slice(11, 16) : '—');
const timestamp = (value) => (value ? `${localDate(value)} às ${localTime(value)}` : '—');
const today = () =>
  new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());

function duration(entrada, instante) {
  // As strings do banco representam o mesmo relógio local. Não usa o fuso do navegador.
  const asLocal = (value) => Date.parse(value.endsWith('Z') ? value : value + 'Z');
  const minutes = Math.max(0, Math.floor((asLocal(instante) - asLocal(entrada)) / 60000));
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, '0')}min`;
}

export { money, localDate, localTime, timestamp, today, duration };
