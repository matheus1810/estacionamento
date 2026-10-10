-- MATIONAMENTO - Estrutura inicial
-- Destino: MySQL 8.0.16 ou superior (CHECK efetivamente validado).
-- Executar uma unica vez, em um banco novo, com usuario autorizado a criar banco.
-- Este arquivo nao apaga dados nem altera tabelas preexistentes.
-- Se alguma tabela ja existir, interrompa a execucao e confira o banco.
-- DDL no MySQL faz commit implicito: este script nao e uma migracao atomica.
-- Charset utf8mb4 e engine InnoDB para todas as tabelas.
--
-- Auditoria:
--   criado_em tem preenchimento automatico.
--   criado_por deve receber o ID do usuario autenticado.
--   atualizado_em e atualizado_por devem ser preenchidos JUNTOS pelo backend.
--   Nao usamos ON UPDATE CURRENT_TIMESTAMP: a data deve acompanhar o autor.
--   O backend preserva os campos de criacao e preenche a auditoria em todo UPDATE.
--   Somente o primeiro usuario pode ser criado com criado_por NULL (regra da aplicacao).
--   Auditoria registra apenas criacao e ultima edicao, nao o historico de valores.
--
-- Datas: configurar as conexoes da aplicacao no mesmo fuso horario.
-- DATETIME nao guarda fuso. Usar consistentemente o horario do estacionamento.
--
-- Sem INSERT de usuarios ou precos ficticios. Apos criar:
-- 1. Cadastrar o primeiro usuario com hash de senha gerado pelo backend.
-- 2. Cadastrar tarifas (id=1) e vagas, informando criado_por.
-- Excecao deliberada: tarifas.id nao e AUTO_INCREMENT, pois so admite id=1.

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS mationamento
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mationamento;

-- usuarios
CREATE TABLE usuarios (
    id INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    login VARCHAR(80) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NULL DEFAULT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuarios_login (login),
    CONSTRAINT ck_usuarios_ativo CHECK (ativo IN (0, 1)),
    CONSTRAINT fk_usuarios_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_usuarios_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_usuarios_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- clientes
CREATE TABLE clientes (
    id INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_clientes_ativo CHECK (ativo IN (0, 1)),
    CONSTRAINT fk_clientes_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_clientes_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_clientes_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- veiculos
CREATE TABLE veiculos (
    id INT NOT NULL AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    placa VARCHAR(7) NOT NULL,
    modelo VARCHAR(80) NOT NULL,
    cor VARCHAR(30) NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_veiculos_placa (placa),
    CONSTRAINT fk_veiculos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_veiculos_placa CHECK (CHAR_LENGTH(placa) = 7),
    CONSTRAINT fk_veiculos_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_veiculos_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_veiculos_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- vagas
CREATE TABLE vagas (
    id INT NOT NULL AUTO_INCREMENT,
    numero VARCHAR(10) NOT NULL,
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_vagas_numero (numero),
    CONSTRAINT ck_vagas_ativa CHECK (ativa IN (0, 1)),
    CONSTRAINT fk_vagas_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_vagas_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_vagas_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- tarifas
CREATE TABLE tarifas (
    id INT NOT NULL DEFAULT 1,
    valor_hora DECIMAL(10,2) NOT NULL,
    valor_mensal_vaga DECIMAL(10,2) NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_tarifas_unica CHECK (id = 1),
    CONSTRAINT ck_tarifas_valores CHECK (valor_hora > 0 AND valor_mensal_vaga > 0),
    CONSTRAINT fk_tarifas_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_tarifas_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_tarifas_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- contratacoes_mensais
CREATE TABLE contratacoes_mensais (
    id INT NOT NULL AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    vaga_id INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NULL DEFAULT NULL,
    dia_vencimento TINYINT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_contratacoes_vaga_periodo (vaga_id, data_inicio, data_fim),
    CONSTRAINT fk_contratacoes_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_contratacoes_vaga FOREIGN KEY (vaga_id) REFERENCES vagas (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_contratacoes_periodo CHECK (data_fim IS NULL OR data_fim >= data_inicio),
    CONSTRAINT ck_contratacoes_vencimento CHECK (dia_vencimento BETWEEN 1 AND 31),
    CONSTRAINT fk_contratacoes_mensais_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_contratacoes_mensais_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_contratacoes_mensais_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- permanencias
CREATE TABLE permanencias (
    id INT NOT NULL AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    veiculo_id INT NOT NULL,
    vaga_id INT NOT NULL,
    entrada DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    saida DATETIME NULL DEFAULT NULL,
    valor_hora_aplicado DECIMAL(10,2) NOT NULL,
    usuario_entrada_id INT NOT NULL,
    usuario_saida_id INT NULL DEFAULT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_permanencias_vaga_saida (vaga_id, saida),
    KEY ix_permanencias_veiculo_saida (veiculo_id, saida),
    CONSTRAINT fk_permanencias_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_permanencias_veiculo FOREIGN KEY (veiculo_id) REFERENCES veiculos (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_permanencias_vaga FOREIGN KEY (vaga_id) REFERENCES vagas (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_permanencias_entrada_usuario FOREIGN KEY (usuario_entrada_id) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_permanencias_saida_usuario FOREIGN KEY (usuario_saida_id) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_permanencias_periodo CHECK (saida IS NULL OR saida >= entrada),
    CONSTRAINT ck_permanencias_tarifa CHECK (valor_hora_aplicado > 0),
    CONSTRAINT ck_permanencias_saida CHECK ((saida IS NULL AND usuario_saida_id IS NULL) OR (saida IS NOT NULL AND usuario_saida_id IS NOT NULL)),
    CONSTRAINT fk_permanencias_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_permanencias_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_permanencias_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- cobrancas
CREATE TABLE cobrancas (
    id INT NOT NULL AUTO_INCREMENT,
    permanencia_id INT NULL DEFAULT NULL,
    contratacao_mensal_id INT NULL DEFAULT NULL,
    competencia DATE NULL DEFAULT NULL,
    vencimento DATE NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    pago_em DATETIME NULL DEFAULT NULL,
    forma_pagamento ENUM('pix', 'dinheiro', 'cartao') NULL DEFAULT NULL,
    usuario_recebimento_id INT NULL DEFAULT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INT NOT NULL,
    atualizado_em DATETIME NULL DEFAULT NULL,
    atualizado_por INT NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_cobrancas_permanencia (permanencia_id),
    UNIQUE KEY uq_cobrancas_contratacao_competencia (contratacao_mensal_id, competencia),
    KEY ix_cobrancas_pendencias (pago_em, vencimento),
    CONSTRAINT fk_cobrancas_permanencia FOREIGN KEY (permanencia_id) REFERENCES permanencias (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_cobrancas_contratacao FOREIGN KEY (contratacao_mensal_id) REFERENCES contratacoes_mensais (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_cobrancas_recebimento_usuario FOREIGN KEY (usuario_recebimento_id) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_cobrancas_origem CHECK ((permanencia_id IS NOT NULL AND contratacao_mensal_id IS NULL AND competencia IS NULL) OR (permanencia_id IS NULL AND contratacao_mensal_id IS NOT NULL AND competencia IS NOT NULL)),
    CONSTRAINT ck_cobrancas_competencia CHECK (competencia IS NULL OR DAYOFMONTH(competencia) = 1),
    CONSTRAINT ck_cobrancas_valor CHECK (valor >= 0),
    CONSTRAINT ck_cobrancas_pagamento CHECK ((pago_em IS NULL AND forma_pagamento IS NULL AND usuario_recebimento_id IS NULL) OR (pago_em IS NOT NULL AND forma_pagamento IS NOT NULL AND forma_pagamento IN ('pix', 'dinheiro', 'cartao') AND usuario_recebimento_id IS NOT NULL)),
    CONSTRAINT fk_cobrancas_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_cobrancas_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_cobrancas_auditoria CHECK ((atualizado_em IS NULL AND atualizado_por IS NULL) OR (atualizado_em IS NOT NULL AND atualizado_por IS NOT NULL AND atualizado_em >= criado_em))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- REGRAS DO BACKEND (nao implementadas automaticamente por este DDL)
--
-- 1. Normalizar placa: 7 caracteres alfanumericos, maiusculos, sem hifen/espaco.
--    Validar nome, telefone, login, modelo e cor (nao aceitar texto vazio).
-- 2. Impedir duas permanencias abertas para o mesmo veiculo ou vaga.
--    Impedir entrada em vaga inativa ou reservada para mensalista.
-- 3. Impedir sobreposicao de contratacoes da mesma vaga e reserva com horista presente.
--    Vigencia: data_inicio <= data consultada e data_fim NULL ou >= data consultada.
--    data_fim inclui o ultimo dia da reserva.
-- 4. Usar transacoes e SELECT ... FOR UPDATE nos registros de vaga e veiculo
--    antes das verificacoes e da gravacao, seguindo a mesma ordem de bloqueio.
--    Entrada e contratacao devem bloquear a mesma vaga para evitar conflito.
-- 5. Na entrada horista, copiar tarifas.valor_hora para valor_hora_aplicado
--    e copiar o cliente responsavel para permanencias.cliente_id.
-- 6. Na saida: blocos = GREATEST(1, CEIL(segundos_de_permanencia / 1800.0)).
--    total = ROUND(blocos * valor_hora_aplicado / 2, 2).
--    Exemplo: 1h20 com hora a R$10 = 3 blocos = R$15.
--    Usar Decimal no Python; nunca float para dinheiro.
--    Gravar saida + cobranca + quitacao na MESMA transacao.
--    Vencimento horista = data da saida; competencia = NULL.
-- 7. Gerar uma cobranca por contratacao e competencia, copiando a tarifa mensal.
--    Competencia usa dia 01. Vencimento usa dia_vencimento, limitado ao ultimo
--    dia do mes. Nao gerar competencias duplicadas nem fora do periodo contratado.
--    Mudancas de tarifa so afetam novas cobrancas; valores antigos sao preservados.
--    Geracao mensal nao e automatica pelo banco: implementar no Python.
--    Cobranca proporcional de primeiro/ultimo mes nao foi definida neste escopo.
-- 8. Consulta mensalista: placa -> cliente -> contratacoes vigentes.
--    Sem contratacao vigente nao ha liberacao como mensalista.
--    Havendo qualquer mensalidade desse cliente com pago_em NULL e vencimento
--    anterior a data de hoje, informar bloqueado; no dia do vencimento nao ha atraso.
--    Garantir geracao das mensalidades antes de avaliar pendencias.
-- 9. Mensalistas nao registram entrada/saida. A quantidade de veiculos presentes
--    e controlada presencialmente pelo atendente.
-- 10. Preferir desativacao de clientes/usuarios/vagas e encerramento de contratos.
--     FKs RESTRICT preservam referencias, mas nao impedem excluir registros folha:
--     a aplicacao deve proibir exclusao de cobrancas e permanencias historicas.
--
-- Conferencia apos a importacao:
SHOW TABLES;

