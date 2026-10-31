-- MATIONAMENTO - Instalacao no banco senacdb_matheus (Alwaysdata).
-- Crie o banco pelo painel Alwaysdata antes de importar este arquivo.
-- Execute somente em um banco vazio, com permissao para criar tabelas.
-- Cria as nove tabelas, incluindo solicitacoes de nota fiscal.
-- Nao cria banco, nao apaga tabelas e nao insere usuarios ou dados de exemplo.
-- Se houver erro, interrompa o import e confira o estado antes de tentar novamente.
-- DDL faz commit implicito; a criacao das tabelas nao e uma transacao atomica.

SET NAMES utf8mb4;
USE `senacdb_matheus`;

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

-- Pedidos de nota fiscal para emissao posterior.
CREATE TABLE solicitacoes_nota_fiscal (
    id INT NOT NULL AUTO_INCREMENT,
    cobranca_id INT NOT NULL,
    nome VARCHAR(120) NOT NULL,
    documento VARCHAR(14) NOT NULL,
    email VARCHAR(254) NULL DEFAULT NULL,
    endereco VARCHAR(250) NULL DEFAULT NULL,
    criado_em DATETIME NOT NULL,
    criado_por INT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_solicitacoes_nf_cobranca (cobranca_id),
    CONSTRAINT fk_solicitacoes_nf_cobranca FOREIGN KEY (cobranca_id)
        REFERENCES cobrancas (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_solicitacoes_nf_usuario FOREIGN KEY (criado_por)
        REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
