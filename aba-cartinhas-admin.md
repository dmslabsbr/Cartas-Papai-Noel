## Cartinhas (Administração)

### Propósito
Gerenciar registros de cartinhas: criação, edição, exclusão lógica, verificação de integridade e upload de PDFs.

### Funcionalidades
- Edição tabular (DTedit2) de `Cartas_Diversas` (adicionar/editar/excluir registro).
- Verificação de integridade: duplicados, PDFs sem cadastro e cadastros sem PDF.
- Upload de PDFs das cartinhas (campo `file2`, apenas .pdf), cópia para `g.cartas.path`.
- Recarregar dados (`btn.tab1.refresh`).
- Filtros placeholders: `uiFiltroArea`, `uiFiltroTema` (renderização não mostrada no servidor).

### Tabela principal: Cartas_Diversas (campos)
- id (PK), id_carta, Nome, Sexo, Presente, Observacao, NomeAdotante, Lotacao, Ramal, Status,
  id_usuario (matrícula), dt_escolha, del_bl, del_user, del_time, tipo.

### CRUD (DTedit2)
- Visualização: `c_v_cols` → [id_carta, Nome, Sexo, Presente, Observacao, NomeAdotante, Lotacao, Ramal, Status, id_usuario, dt_escolha].
- Edição: `c_ed_cols` → [id_carta, Nome, Sexo, Presente, Observacao, NomeAdotante, Lotacao, Ramal, Status, id_usuario].
- Obrigatórios: `g.req.cols` → [id_carta, Nome, Sexo, Presente, Status].
- Tipos de input: `c_ed_input_t` (Status=select, id_usuario=numeric, Observacao=textArea, Sexo=select).
- Callbacks:
  - Insert: `cartas.insert.callback` (valida duplicados de `id_carta`, INSERT interpolado, recarrega).
  - Update: `cartas.update.callback` (impede alterar `id_carta`, UPDATE completo, recarrega).
  - Delete: `cartas.delete.callback` (soft delete, define `del_bl=TRUE` e `del_time`).

### Ações
- Verificar dados: `btnVerifica` → `verifica_tb_cartas(mostra_alert=TRUE)`.
- Upload PDFs: `file2` (filtra por extensão .pdf, copia para `g.cartas.path`, remove temporários).
- Recarregar: `btn.tab1.refresh` (há um observador com id divergente no código: `btb.tab1.refresh`).

### Status (valores típicos)
- "Não adotada", "Adotada", "Adotada / a entregar", "Presente entregue".

### Observações
- Há `browser()` ativos (debug) que pausam execução se não desativados.
- `url_cartas` e `url_docs` devem estar definidos no ambiente/configuração.


