## Informações do Sistema

### Propósito
Exibir informações de sessão, tentativas de login, tokens e utilitários administrativos.

### Funcionalidades
- Tabelas (DT):
  - `ui.tab.sys1`: `logins.conta` (id, user.name, user.try, user.time, token).
  - `ui.tab.sys2`: `g.logins.sessions` (user.name, user.time, token).
  - `ui.tab.sys3`: `gTokens2data(g.tokens)` (token, user.name, user.time).
- Texto: `ui.version` (Versão dtedit2, versão do app, token atual).
- Ações e utilitários:
  - `btn.tab5.refresh`: recarrega dados e re-renderiza as três tabelas.
  - `file1` (.xlsx): upload da planilha de cartinhas para `getwd()+g.arquivo.cartas`.
  - `btn.tab5.lercartas`: importa cartinhas do XLSX (3 abas), valida layout e duplicados.
  - `btn.tab5.apagaCartas`: apaga todas as cartinhas (DELETE em `Cartas_Diversas`, com confirmação).

### CRUD
- Não há CRUD de tabelas de negócio nesta aba; são consultas e utilitários administrativos.


