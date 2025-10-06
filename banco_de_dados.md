## Banco de Dados — Noel (Shiny)

### Visão geral
- **SGBD**: MariaDB (compatível MySQL), usado via `DBI`/`pool` no app.
- **Schema principal**: `noel`
- **Tabelas**: `Cartas_Diversas`, `usuarios`, `modulo`, `icon_presente`
- **Views**: `vw_usuarios`, `vw_usuarios_ativos`
- **Soft delete**: campo `del_bl` em `Cartas_Diversas` para marcação lógica de exclusão.

### Modelagem (lógica)
- **Cartas_Diversas**: catálogo de cartinhas com status, adotante, matrícula do adotante (quando houver) e metadados.
- **usuarios**: usuários autorizados, vinculados a um perfil/modulo.
- **modulo**: perfis e permissões (admin, gravação, visualização, ver tudo).
- **icon_presente**: mapeia palavras-chave de presentes para ícones (usado para exibição na UI).
- **vw_usuarios**: join entre `usuarios` e `modulo` expondo permissões.
- **vw_usuarios_ativos**: filtro de `vw_usuarios` para `bl_ativo = 1`.

Relacionamentos (recomendados):
- `usuarios.id_modulo` → `modulo.id_modulo` (FK)
- `Cartas_Diversas.id_usuario` referencia matrícula do adotante; não há FK (por design), pois matrícula vem de LDAP. Opcionalmente, pode referenciar `usuarios.matricula` se forem síncronos.

### Tabelas e campos (resumo)
- `Cartas_Diversas`
  - `id` INT PK, auto-incremento
  - `id_carta` INT(4) único (recomendado UNIQUE)
  - `Nome` VARCHAR(50)
  - `Sexo` VARCHAR(9)
  - `Presente` VARCHAR(100)
  - `Observacao` VARCHAR(100)
  - `NomeAdotante` VARCHAR(50)
  - `Lotacao` VARCHAR(30)
  - `Ramal` VARCHAR(15)
  - `Status` VARCHAR(20) — valores previstos: "Não adotada", "Adotada", "Adotada / a entregar", "Presente entregue"
  - `id_usuario` INT(11) — matrícula
  - `dt_escolha` VARCHAR(30)
  - `del_bl` TINYINT(1)
  - `del_user` VARCHAR(50)
  - `del_time` VARCHAR(20)
  - `tipo` VARCHAR(10)

- `usuarios`
  - `id_usuario` INT PK, auto-incremento
  - `matricula` INT NOT NULL
  - `login` VARCHAR(30)
  - `bl_ativo` TINYINT(1) NOT NULL
  - `id_modulo` INT — FK para `modulo`

- `modulo`
  - `id_modulo` INT PK, auto-incremento
  - `cd_modulo` VARCHAR(14) UNIQUE
  - `ds_modulo` VARCHAR(50)
  - `bl_admin`, `bl_grava`, `bl_visual`, `bl_visual_tudo` TINYINT(1)

- `icon_presente`
  - `id` INT PK, auto-incremento
  - `icon` VARCHAR(30)
  - `palavras` VARCHAR(150)

### Considerações de collation/charset
- Recomenda-se `utf8mb4`/`utf8mb4_unicode_ci` (o dump original usa `utf8`).
- Ajuste conforme necessidade de compatibilidade com dados legados.

### Comandos SQL recomendados (criação do schema)

```sql
-- 1) Criar base e usuário (ajuste a senha)
CREATE DATABASE IF NOT EXISTS noel
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'noel_user'@'%'
  IDENTIFIED BY 'troque-esta-senha';
GRANT ALL PRIVILEGES ON noel.* TO 'noel_user'@'%';
FLUSH PRIVILEGES;

USE noel;

-- 2) Tabelas
CREATE TABLE IF NOT EXISTS `Cartas_Diversas` (
  `id` INT(11) NOT NULL COMMENT 'id primario',
  `id_carta` INT(4) DEFAULT NULL,
  `Nome` VARCHAR(50) DEFAULT NULL,
  `Sexo` VARCHAR(9) DEFAULT NULL,
  `Presente` VARCHAR(100) DEFAULT NULL,
  `Observacao` VARCHAR(100) DEFAULT NULL,
  `NomeAdotante` VARCHAR(50) DEFAULT NULL,
  `Lotacao` VARCHAR(30) DEFAULT NULL,
  `Ramal` VARCHAR(15) DEFAULT NULL,
  `Status` VARCHAR(20) DEFAULT NULL,
  `id_usuario` INT(11) DEFAULT NULL COMMENT 'matrícula',
  `dt_escolha` VARCHAR(30) DEFAULT NULL,
  `del_bl` TINYINT(1) DEFAULT NULL COMMENT 'está deletado?',
  `del_user` VARCHAR(50) DEFAULT NULL COMMENT 'usuário que apagou',
  `del_time` VARCHAR(20) DEFAULT NULL COMMENT 'quando apagou',
  `tipo` VARCHAR(10) DEFAULT NULL COMMENT 'Correios ou outros?',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `icon_presente` (
  `id` INT(11) NOT NULL,
  `icon` VARCHAR(30) NOT NULL,
  `palavras` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `modulo` (
  `id_modulo` INT(11) NOT NULL,
  `cd_modulo` VARCHAR(14) DEFAULT NULL COMMENT 'Código Modulo',
  `ds_modulo` VARCHAR(50) NOT NULL COMMENT 'Descrição Modulo',
  `bl_admin` TINYINT(1) DEFAULT NULL COMMENT 'Administração Geral',
  `bl_grava` TINYINT(1) DEFAULT NULL COMMENT 'Permite Gravar na área',
  `bl_visual` TINYINT(1) DEFAULT NULL COMMENT 'Permite visualizar área',
  `bl_visual_tudo` TINYINT(1) DEFAULT NULL COMMENT 'Permite visualizar tudo',
  PRIMARY KEY (`id_modulo`),
  UNIQUE KEY `cd_modulo` (`cd_modulo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` INT(11) NOT NULL,
  `matricula` INT(11) NOT NULL,
  `login` VARCHAR(30) DEFAULT NULL COMMENT 'Login Usuário',
  `bl_ativo` TINYINT(1) NOT NULL,
  `id_modulo` INT(11) DEFAULT NULL COMMENT 'atividades permitidas',
  PRIMARY KEY (`id_usuario`),
  KEY `idx_usuarios_matricula` (`matricula`),
  KEY `idx_usuarios_id_modulo` (`id_modulo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) Auto-incrementos
ALTER TABLE `Cartas_Diversas`
  MODIFY `id` INT(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `icon_presente`
  MODIFY `id` INT(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `modulo`
  MODIFY `id_modulo` INT(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `usuarios`
  MODIFY `id_usuario` INT(11) NOT NULL AUTO_INCREMENT;

-- 4) Índices adicionais (performance/consistência)
CREATE UNIQUE INDEX IF NOT EXISTS `ux_cartas_id_carta`
  ON `Cartas_Diversas` (`id_carta`);
CREATE INDEX IF NOT EXISTS `idx_cartas_status`
  ON `Cartas_Diversas` (`Status`);
CREATE INDEX IF NOT EXISTS `idx_cartas_id_usuario`
  ON `Cartas_Diversas` (`id_usuario`);
CREATE INDEX IF NOT EXISTS `idx_cartas_del_bl`
  ON `Cartas_Diversas` (`del_bl`);

-- 5) Chaves estrangeiras (recomendadas)
ALTER TABLE `usuarios`
  ADD CONSTRAINT `fk_usuarios_modulo`
  FOREIGN KEY (`id_modulo`) REFERENCES `modulo` (`id_modulo`)
  ON UPDATE CASCADE ON DELETE SET NULL;

-- 6) Seeds mínimos
INSERT INTO `modulo` (`cd_modulo`, `ds_modulo`, `bl_admin`, `bl_grava`, `bl_visual`, `bl_visual_tudo`) VALUES
  ('Admin', 'Administração Geral', 1, 1, 1, 1),
  ('User',  'Usuário normal',       0, 1, 1, 0),
  ('Rh',    'RH',                   0, 1, 1, 1)
ON DUPLICATE KEY UPDATE `ds_modulo`=VALUES(`ds_modulo`);

-- Opcional: alguns ícones de exemplo (complete conforme necessidade)
INSERT INTO `icon_presente` (`icon`, `palavras`) VALUES
  ('female', 'barbie, boneca'),
  ('futbol', 'bola, futebol'),
  ('truck',  'caminhão, carretas, carrinho, carro'),
  ('robot',  'robô, transformer');

-- 7) Views (compatíveis com as usadas no app)
DROP VIEW IF EXISTS `vw_usuarios`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `vw_usuarios` AS
SELECT u.id_usuario,
       u.matricula,
       u.login,
       u.bl_ativo,
       u.id_modulo,
       m.cd_modulo,
       m.ds_modulo,
       m.bl_admin,
       m.bl_grava,
       m.bl_visual,
       m.bl_visual_tudo
FROM `usuarios` u
LEFT JOIN `modulo` m ON u.id_modulo = m.id_modulo
ORDER BY u.matricula;

DROP VIEW IF EXISTS `vw_usuarios_ativos`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_usuarios_ativos` AS
SELECT * FROM `vw_usuarios` WHERE `bl_ativo` = 1 ORDER BY `matricula`;
```

Observações:
- O app verifica a existência destas tabelas/views: `icon_presente`, `Cartas_Diversas`, `vw_usuarios_ativos`, `usuarios`, `vw_usuarios`, `modulo`.
- O `Status` é usado intensamente em filtros/contagens; indexá-lo ajuda na performance.
- `id_carta` deve ser único para evitar duplicidade na importação; o app já valida, mas o índice UNIQUE garante no banco.
- `id_usuario` armazena a matrícula (inteiro) do adotante; não necessariamente corresponde a uma linha de `usuarios` (pois o login vem de LDAP). Caso deseje referenciar `usuarios`, adeque processo de sincronização.

### Operações típicas
- Cartas não deletadas (soft delete):
```sql
SELECT * FROM Cartas_Diversas WHERE del_bl IS NULL OR del_bl = FALSE;
```
- Marcar carta como adotada:
```sql
UPDATE Cartas_Diversas
   SET id_usuario = ?matricula,
       Status = 'Adotada',
       NomeAdotante = ?nome,
       dt_escolha = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')
 WHERE id_carta = ?id_carta;
```
- Confirmar presente entregue:
```sql
UPDATE Cartas_Diversas
   SET Status = 'Presente entregue'
 WHERE id_carta = ?id_carta;
```
- Soft delete de uma carta:
```sql
UPDATE Cartas_Diversas
   SET del_bl = TRUE,
       del_time = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')
 WHERE id_carta = ?id_carta;
```

### Dicas de administração
- Backup/restauração: use `mysqldump`/`mysql` com `--routines --triggers --single-transaction`.
- Conexão do app: configure host/porta/usuário/senha em `secrets.R` conforme `global.R`.
- Charset: se houver dados legados em `latin1`, ajuste `CHARSET`/`COLLATE` das tabelas para alinhar com a aplicação.



