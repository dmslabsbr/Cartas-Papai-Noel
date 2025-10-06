## Marcar Presentes

### Propósito
Marcar presentes como entregues para cartinhas já adotadas.

### Funcionalidades
- Lista com ação "Marcar Presente Entregue" por cartinha.
- Itens já entregues exibem indicação e não permitem nova marcação.

### Fluxo de marcação
1. Clique em "Marcar Presente Entregue" → dispara `select_presente`.
2. Confirmação via `shinyalert`.
3. `trataShinyAlert` → `pegaPresente(id_carta, matricula)` → UPDATE `Status='Presente entregue'` e sincronização da lista.

### Tabela e campos
- Base: `Cartas_Diversas` (leitura para montar a lista; update em `Status`).
- Colunas incluem: Nº Carta, Nome, Sexo, Presente (com ícones), Adotante, Lotação, Marcação (ações/estado).

### CRUD
- Não há criação/edição/remoção de registros; apenas atualização do campo `Status` via ação confirmada.


