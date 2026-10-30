// Finaliza uma operação e atualiza os dados exibidos na tela.

import { state } from '../estado.js';
import { render } from '../navegacao.js';
import { closeModal } from '../ui/modal.js';
import { toast } from '../ui/notificacoes.js';

async function complete(message) {
  state.atendimento = null;
  closeModal();
  toast(message);
  await render();
}

export { complete };
