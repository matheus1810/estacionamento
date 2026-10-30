// Consulta os dados e monta a tela de tarifas.

import { api } from '../api.js';
import { state } from '../estado.js';
import { heading } from '../ui/componentes.js';
import { input } from '../ui/formularios.js';
import { icon } from '../ui/icones.js';
import { timestamp } from '../utils/formatacao.js';

async function rates() {
  let tarifa;
  try {
    tarifa = await api('/tarifas');
  } catch (error) {
    if (error.message === 'Registro não encontrado.') tarifa = null;
    else throw error;
  }
  state.cache.tarifa = tarifa;
  return (
    heading(
      'CONFIGURAÇÃO',
      'Tarifas',
      'Preços gerais para novas permanências e novas mensalidades.',
    ) +
    /* HTML */ `<section class="panel settings-card">
      <h3>${tarifa ? 'Tarifas do estacionamento' : 'Configure seus primeiros valores'}</h3>
      <p class="muted" style="font-size:12px;margin-top:8px">
        ${tarifa
          ? 'Atualize os valores quando precisar. O histórico fica preservado.'
          : 'Nenhum preço é definido automaticamente.'}
      </p>
      <form id="rates-form">
        <div class="form-grid">
          ${input('valor_hora', 'Valor por hora (R$)', 'number', tarifa?.valor_hora || '', {
            min: '0.01',
            max: '99999999.99',
            step: '.01',
            required: true,
          })}${input(
            'valor_mensal_vaga',
            'Mensalidade por vaga (R$)',
            'number',
            tarifa?.valor_mensal_vaga || '',
            { min: '0.01', max: '99999999.99', step: '.01', required: true },
          )}
        </div>
        <button class="button primary" type="submit">
          ${icon('check')}${tarifa ? 'Salvar tarifas' : 'Cadastrar tarifas'}
        </button>
      </form>
      <div class="notice">
        Horistas são cobrados em blocos de 30 minutos, arredondados para cima, com mínimo de um
        bloco. A tarifa da entrada vale até a saída.
      </div>
      ${tarifa
        ? /* HTML */ `<p class="muted" style="font-size:10px;margin:18px 0 0">
            Último registro: ${timestamp(tarifa.atualizado_em || tarifa.criado_em)}
          </p>`
        : ''}
    </section>`
  );
}

export { rates };
