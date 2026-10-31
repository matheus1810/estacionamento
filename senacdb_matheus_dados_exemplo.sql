-- MATIONAMENTO - Dados ficticios para o banco senacdb_matheus (Alwaysdata).
-- Importe senacdb_matheus.sql e cadastre um operador antes deste arquivo.
-- Adiciona cinco clientes, cinco veiculos e cinco vagas livres.
-- Nao cria usuarios, senhas, tarifas, permanencias, contratos ou cobrancas.
-- Nao apaga nem atualiza cadastros existentes.
-- Se faltar operador ou algum exemplo ja existir, nenhum registro sera inserido.
-- Se ocorrer outro erro, interrompa e execute ROLLBACK; nao prossiga ate COMMIT.

SET NAMES utf8mb4;
USE `senacdb_matheus`;
SET SESSION time_zone = '-03:00';

START TRANSACTION;

SET @operador_id = (SELECT id FROM usuarios WHERE ativo = 1 ORDER BY id LIMIT 1);
SET @agora = CURRENT_TIMESTAMP;

-- Evita repetir ou misturar os exemplos com cadastros de mesmo nome/placa/vaga.
SET @exemplos_existem = (
    EXISTS (SELECT 1 FROM clientes WHERE nome IN (
        'Ana Silva Exemplo', 'Bruno Costa Exemplo', 'Carla Souza Exemplo',
        'Diego Lima Exemplo', 'Elisa Santos Exemplo'
    ))
    OR EXISTS (SELECT 1 FROM veiculos WHERE placa IN (
        'EXP1A01', 'EXP1A02', 'EXP1A03', 'EXP1A04', 'EXP1A05'
    ))
    OR EXISTS (SELECT 1 FROM vagas WHERE numero IN (
        'EX-01', 'EX-02', 'EX-03', 'EX-04', 'EX-05'
    ))
);
SET @importar = (@operador_id IS NOT NULL AND NOT @exemplos_existem);

-- Nomes sem numeros e telefones normalizados, de acordo com a validacao da API.
INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
SELECT 'Ana Silva Exemplo', '11900000001', TRUE, @agora, @operador_id WHERE @importar;
SET @cliente_ana = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
SELECT 'Bruno Costa Exemplo', '11900000002', TRUE, @agora, @operador_id WHERE @importar;
SET @cliente_bruno = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
SELECT 'Carla Souza Exemplo', '11900000003', TRUE, @agora, @operador_id WHERE @importar;
SET @cliente_carla = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
SELECT 'Diego Lima Exemplo', '11900000004', TRUE, @agora, @operador_id WHERE @importar;
SET @cliente_diego = LAST_INSERT_ID();

INSERT INTO clientes (nome, telefone, ativo, criado_em, criado_por)
SELECT 'Elisa Santos Exemplo', '11900000005', TRUE, @agora, @operador_id WHERE @importar;
SET @cliente_elisa = LAST_INSERT_ID();

-- IDs obtidos de cada INSERT: nao depende de IDs fixos nem de sequencia contigua.
INSERT INTO veiculos (cliente_id, placa, modelo, cor, criado_em, criado_por)
SELECT exemplos.cliente_id, exemplos.placa, exemplos.modelo, exemplos.cor, @agora, @operador_id
FROM (
    SELECT @cliente_ana AS cliente_id, 'EXP1A01' AS placa, 'Fiat Argo' AS modelo, 'Branco' AS cor
    UNION ALL SELECT @cliente_bruno, 'EXP1A02', 'Volkswagen Gol', 'Prata'
    UNION ALL SELECT @cliente_carla, 'EXP1A03', 'Chevrolet Onix', 'Preto'
    UNION ALL SELECT @cliente_diego, 'EXP1A04', 'Hyundai HB20', 'Azul'
    UNION ALL SELECT @cliente_elisa, 'EXP1A05', 'Toyota Corolla', 'Cinza'
) AS exemplos
WHERE @importar;

-- As vagas ficam livres. O vinculo com o veiculo ocorre ao registrar uma entrada.
INSERT INTO vagas (numero, ativa, criado_em, criado_por)
SELECT exemplos.numero, TRUE, @agora, @operador_id
FROM (
    SELECT 'EX-01' AS numero
    UNION ALL SELECT 'EX-02'
    UNION ALL SELECT 'EX-03'
    UNION ALL SELECT 'EX-04'
    UNION ALL SELECT 'EX-05'
) AS exemplos
WHERE @importar;

COMMIT;

SELECT CASE
    WHEN @operador_id IS NULL THEN 'Nenhum dado inserido: cadastre um operador ativo antes de importar.'
    WHEN @exemplos_existem THEN 'Nenhum dado inserido: ja existe cliente, placa ou vaga reservado para estes exemplos.'
    ELSE 'Exemplos inseridos: cinco clientes, cinco veiculos e cinco vagas.'
END AS resultado;

SELECT c.nome AS cliente, c.telefone, v.placa, v.modelo, v.cor
FROM clientes AS c
JOIN veiculos AS v ON v.cliente_id = c.id
WHERE v.placa IN ('EXP1A01', 'EXP1A02', 'EXP1A03', 'EXP1A04', 'EXP1A05')
ORDER BY v.placa;

SELECT numero, ativa
FROM vagas
WHERE numero IN ('EX-01', 'EX-02', 'EX-03', 'EX-04', 'EX-05')
ORDER BY numero;
