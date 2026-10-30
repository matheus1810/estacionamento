// Cadastro e edição de veículos e vínculo com o cliente.

import { post, patch, all } from '../api.js';
import { state } from '../estado.js';
import { complete } from './conclusao.js';
import { input, select } from '../ui/formularios.js';
import { openModal } from '../ui/modal.js';
import { toast } from '../ui/notificacoes.js';

async function vehicleModal(id) {
  const c = id ? state.cache.rows?.find((v) => v.id === id) : null;
  const clientes = await all('/clientes');
  if (!clientes.length) {
    toast('Cadastre um cliente antes do veículo.', true);
    return;
  }
  openModal(
    c ? 'Editar veículo' : 'Novo veículo',
    /* HTML */ `<div class="form-grid">
        <div class="full">
          ${select(
            'cliente_id',
            'Cliente responsável',
            clientes.map((v) => [v.id, v.nome + (v.ativo ? '' : ' (inativo)')]),
            c?.cliente_id,
          )}
        </div>
        ${input('placa', 'Placa', 'text', c?.placa || '', {
          required: true,
          maxlength: 12,
          placeholder: 'ABC1D23',
        })}${input('modelo', 'Modelo', 'text', c?.modelo || '', {
          required: true,
          maxlength: 80,
        })}${input('cor', 'Cor', 'text', c?.cor || '', { required: true, maxlength: 30 })}
      </div>
      ${c
        ? '<p class="muted" style="font-size:10px;margin-top:18px">Alterar o responsável preserva o cliente histórico das permanências.</p>'
        : ''}`,
    async (values) => {
      const body = { ...values, cliente_id: Number(values.cliente_id) };
      if (c) await patch('/veiculos/' + c.id, body);
      else await post('/veiculos', body);
      await complete(c ? 'Veículo atualizado.' : 'Veículo cadastrado.');
    },
  );
}

export { vehicleModal };
