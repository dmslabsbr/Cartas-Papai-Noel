## Minhas Cartinhas

### Propósito
Exibir as cartinhas adotadas pelo usuário atualmente autenticado.

### Funcionalidades
- Lista filtrada por matrícula do usuário (obtida de `g.tokens[[token]]$user.id`).
- Link "Visualizar" para abrir o PDF da cartinha (quando existente).
- Ícones indicativos de status (adotada/presente entregue/pendente).

### Fonte de dados
- Base: `Cartas_Diversas` (somente leitura nesta aba).
- Renderização: `showMyCards()` prepara colunas e publica em `ui.tab.tab3`.

### Colunas exibidas (padrão)
- Nº Carta, Criança (Nome), Sexo, Presente, Observação, Status (com ícone), Adotante, Cartinha (link).

### CRUD
- Não há criação/edição/remoção nesta aba; alterações ocorrem nas abas de Administração/Lista/Presentes.


