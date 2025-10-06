## Cartinhas (Lista Geral)

### Propósito
Listar cartinhas e permitir adoção por usuários autenticados.

### Funcionalidades
- Tabela com ações por linha:
  - "Visualizar": abre PDF (se existir) em `pdfviewer`.
  - "Adotar": botão que aciona confirmação (`shinyalert`).
- Ícones e marcações de status conforme situação.

### Fluxo de adoção
1. Clique em "Adotar" → dispara `select_adotar`.
2. Confirmação via `shinyalert`.
3. `trataShinyAlert` → `pegaCarta(id_carta, matricula, displayName)` → UPDATE em `Cartas_Diversas` e sincronização de `tb_cartas`/`g.react.cartas`.

### Tabela e campos
- Base: `Cartas_Diversas` (leitura).
- Colunas exibidas (variam conforme `showCartinhas()`): incluem Nº Carta, Nome, Sexo, Presente(s), Observações, Status (com ícone), Visualizar, Adotar.

### CRUD
- Não há criação/edição direta nesta aba; adoção atualiza `Cartas_Diversas`.


