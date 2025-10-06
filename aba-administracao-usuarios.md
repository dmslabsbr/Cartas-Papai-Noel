## Administração de Usuários

### Propósito
Gerenciar permissões e perfis dos usuários do sistema.

### Funcionalidades
- Edição tabular (DTedit2) da tabela `usuarios`.
- Atribuição de perfil (módulo) com permissões derivadas de `modulo`.

### Tabelas
- `usuarios`: id_usuario (PK), matricula, login, bl_ativo, id_modulo.
- `modulo`: id_modulo (PK), cd_modulo (UNIQUE), ds_modulo, bl_admin, bl_grava, bl_visual, bl_visual_tudo.
- Views (uso em autenticação/permissões): `vw_usuarios`, `vw_usuarios_ativos`.

### CRUD (DTedit2)
- Visualização: [id_usuario, matricula, login, bl_ativo, cd_modulo].
- Edição: [matricula, bl_ativo, cd_modulo].
- Tipos de input: `c_user_input_t` (matricula=numeric, bl_ativo=select, cd_modulo=select).
- Callbacks:
  - Insert: `user.insert.callback` → SQL via `monta_sql_user(..., 'insert')`.
  - Update: `user.update.callback` → SQL via `monta_sql_user(..., 'update')`.
  - Delete: `user.delete.callback` → DELETE por `id_usuario`.

### Regras de permissão (refletidas na UI)
- `bl_admin`, `bl_grava`, `bl_visual`, `bl_visual_tudo` controlam quais abas/menus ficam visíveis.


