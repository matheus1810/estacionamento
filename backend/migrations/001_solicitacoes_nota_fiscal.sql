-- Execute no banco já configurado. Cria somente a tabela adicional, sem alterar dados.
CREATE TABLE IF NOT EXISTS solicitacoes_nota_fiscal (
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
