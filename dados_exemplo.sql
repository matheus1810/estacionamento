-- Mationamento: cinco clientes ficticios, seus veiculos e cinco vagas.
-- Execute UMA VEZ, depois de importar mationamento.sql e criar um operador.
-- Compativel com o MySQL e o MariaDB do XAMPP.
-- Nao cria usuarios, tarifas, permanencias, contratos ou cobrancas.
-- Nao apaga nem atualiza cadastros existentes.
-- Se ocorrer erro, interrompa a importacao; nao use a opcao --force.
-- A transacao so e confirmada se todos os INSERTs terminarem com sucesso.

SET NAMES utf8mb4;
USE mationamento;
SET SESSION time_zone = '-03:00';

START TRANSACTION;

-- Usa o primeiro operador ativo existente, sem presumir que seu ID seja 1.
-- Se nao houver operador ativo, criado_por sera NULL e o banco recusara
-- o primeiro INSERT. Nesse caso, crie o operador antes de importar este arquivo.
SET @operador_id = (SELECT id FROM usuarios WHERE ativo = 1 ORDER BY id LIMIT 1);
SET @agora = CURRENT_TIMESTAMP;

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
VALUES ('Ana Silva (exemplo)', '(11) 90000-0001', TRUE, @agora, @operador_id);
SET @cliente_ana = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
VALUES ('Bruno Costa (exemplo)', '(11) 90000-0002', TRUE, @agora, @operador_id);
SET @cliente_bruno = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
VALUES ('Carla Souza (exemplo)', '(11) 90000-0003', TRUE, @agora, @operador_id);
SET @cliente_carla = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
VALUES ('Diego Lima (exemplo)', '(11) 90000-0004', TRUE, @agora, @operador_id);
SET @cliente_diego = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
VALUES ('Elisa Santos (exemplo)', '(11) 90000-0005', TRUE, @agora, @operador_id);
SET @cliente_elisa = LAST_INSERT_ID();

-- Placas ficticias no formato Mercosul, unicas e normalizadas.
INSERT INTO veiculos
    (cliente_id, placa, modelo, cor, criado_em, criado_por)
VALUES
    (@cliente_ana,   'EXP1A01', 'Fiat Argo',          'Branco', @agora, @operador_id),
    (@cliente_bruno, 'EXP1A02', 'Volkswagen Gol',     'Prata',  @agora, @operador_id),
    (@cliente_carla, 'EXP1A03', 'Chevrolet Onix',     'Preto',  @agora, @operador_id),
    (@cliente_diego, 'EXP1A04', 'Hyundai HB20',       'Azul',   @agora, @operador_id),
    (@cliente_elisa, 'EXP1A05', 'Toyota Corolla',     'Cinza',  @agora, @operador_id);

-- Vagas livres: nao se vincula uma vaga ao veiculo no cadastro.
-- O vinculo acontece na entrada horista ou na contratacao mensal do cliente.
INSERT INTO vagas (numero, ativa, criado_em, criado_por)
VALUES
    ('EX-01', TRUE, @agora, @operador_id),
    ('EX-02', TRUE, @agora, @operador_id),
    ('EX-03', TRUE, @agora, @operador_id),
    ('EX-04', TRUE, @agora, @operador_id),
    ('EX-05', TRUE, @agora, @operador_id);

COMMIT;

-- Conferencia dos exemplos importados.
SELECT c.nome AS cliente, c.telefone, v.placa, v.modelo, v.cor
FROM clientes AS c
JOIN veiculos AS v ON v.cliente_id = c.id
WHERE v.placa IN ('EXP1A01', 'EXP1A02', 'EXP1A03', 'EXP1A04', 'EXP1A05')
ORDER BY v.placa;

SELECT numero, ativa
FROM vagas
WHERE numero IN ('EX-01', 'EX-02', 'EX-03', 'EX-04', 'EX-05')
ORDER BY numero;
