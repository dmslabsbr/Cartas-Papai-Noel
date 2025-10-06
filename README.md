# noel
R language program to control Santa's letters.

1 - Clone este repositorio

git clone https://github.com/dmslabsbr/noel.git

2 - Inicie os containers

docker-compose up

3 - Crie o banco de dados.

-------

Para ver o aplicativo rodando, abra a porta 3839
Para administrar o banco de dados, abra a porta 9000

## Análise do Aplicativo Shiny (Noel)

### Resumo executivo
- **Objetivo**: Gerir a adoção de cartinhas (crianças e presentes) com autenticação, administração de usuários, importação via Excel e marcação de presentes entregues.
- **Público**: Usuários autenticados (LDAP) e administradores.
- **Stack**: R, Shiny, Shinydashboard, DT, pool/DBI, RMariaDB, openxlsx, shinyjs, shinyalert, RCurl, pacotes internos `dtedit2` e `shinyldap`.

### Arquitetura e arquivos
- **`ui.R`**: Layout e componentes visuais com `shinydashboard`, abas e menus dinâmicos.
- **`server.R`**: Sessão Shiny, autenticação LDAP, observers, renderizações DT, upload de arquivos, ações por linha, callbacks de edição e operações SQL.
- **`global.R`**: Carga de bibliotecas, variáveis globais e secrets, conexão com MariaDB (pool), pré-carga de dados/metadados e helpers globais.
- **`fcomum.R`**: Funções utilitárias (fatores, busca de IDs, helpers diversos de UI/strings).

Trecho da página principal do dashboard:
```164:170:ui.R
ui_dashboard <- shinydashboard::dashboardPage(
  shinydashboard::dashboardHeader(title = "Cartinhas Papai Noel - Natal 2021",
                         shiny::tags$li(class = 'dropdown', style = 'padding: 8px;', ui_logout, ui_modal)),
  shinydashboard::dashboardSidebar(ui_sidebar),
  shinydashboard::dashboardBody(shinyjs::useShinyjs(), shinyalert::useShinyalert(), icon,
                ui_head, ui_body)
)
```

### Fluxo de inicialização
1. `global.R` carrega libs, define globais, lê `secrets.R` (se existir), cria pool MariaDB, valida tabelas esperadas, carrega metadados (`g.icon`, `g.type.fields`) e define `carrega_dados()` e utilitários.
2. `server.R` define `version`, registra versões dos pacotes, chama `carrega_dados()` e inicia `shinyServer` configurando sessão, login, observers e renders.
3. `ui.R` monta o `dashboardPage` (header, sidebar e body com as abas).

Chamada de carga inicial e registro de versões:
```4:16:server.R
version <- 'v0.0.26'
app.name <- 'Noel'
# ...
message('dtEdit2 Versão: ', dtedit2::version())
message('shinyldap Versão: ', shinyldap::version())
carrega_dados()
```

### Interface (UI)
- **Abas (menu lateral dinâmico por permissão)**:
  - Cartinhas (administração) — filtros, verificação, upload de PDFs.
  - Instruções — exibe `docs/instrucoes.xhtml`.
  - Minhas cartinhas — cartinhas do usuário logado.
  - Administração de Usuários — CRUD via DTedit2.
  - Informações do Sistema — tabelas (logins/sessões/tokens), versão do app; import XLSX e apagar cartas.
  - Cartinhas (lista geral) — visualizar PDF e adotar.
  - Marcar Presentes — marcar presente como entregue.

- **Seção de sistema e importação**:
```55:76:ui.R
ui_tab5.1 <- box(title = "Informações do Sistema",
  # ...
  shiny::div(textOutput('ui.version')), shiny::br(),
  shiny::div(style = 'overflow-x: scroll', DT::dataTableOutput('ui.tab.sys1')), # ...
  actionButton('btn.tab5.refresh', 'Recarregar dados', # ...
  fileInput("file1", "Escolha um arquivo xlsx:", multiple = FALSE, accept = '.xlsx'),
  # ...
  actionButton('btn.tab5.lercartas', 'Ler Cartas', # ...
  actionButton('btn.tab5.apagaCartas', 'Apaga Todas às Cartas', # ...
)
```

### Entradas (inputs) principais
- Autenticação: `btnLogin`, `btnLogout`, módulo `shinyldap` (`login_space-*`).
- Sistema: `btn.tab5.refresh`, `btn.tab5.lercartas`, `btn.tab5.apagaCartas`, `btnVerifica`, `btn.tab1.refresh` (verificar id no servidor).
- Uploads: `file1` (.xlsx) e `file2` (.pdf).
- Tabelas (ações por linha): `select_adotar`, `select_presente`.
- Navegação/estado: `tabs`, `shinyalert`, `count` (keep-alive JS).

Criação de botões nas tabelas:
```1049:1058:server.R
my_table$adotar <- shinyInput(actionButton, nrow(my_table),
  'buttonAdt_',
  label = "Adotar",
  icon = icon("hand-holding-heart", lib = "font-awesome"),
  onclick = paste0('Shiny.setInputValue( \"select_adotar\" , this.id.concat("_", new Date().getTime()))'))
```
```1005:1010:server.R
myTb$Marcar <- shinyInput(actionButton, nrow(myTb),
  'buttonPre_',
  label = "Marcar Presente Entregue",
  icon = icon("gifts", lib = "font-awesome"),
  onclick = paste0('Shiny.setInputValue( \"select_presente\" , this.id.concat("_", new Date().getTime()))'))
```

### Saídas (outputs) principais
- Tabelas: `ui.tab.cartinhas`, `ui.tab.presentes`, `ui.tab.tab3`, `ui.tab.sys1`, `ui.tab.sys2`, `ui.tab.sys3`.
- Textos/HTML: `ui.version`, `ui.resumo`, `pdfviewer`, `keepAlive`, `ui.txtUser`, `ui.txtCargo`.
- Menus: `uiSideBarMenu`.

Exemplos de renderizações:
```418:425:server.R
output$ui.version <- renderText(paste0('Versão dtedit2: ', dtedit2::version(), '       app: ', version, '    token: ', session$token))
output$keepAlive <- renderText({
  req(input$count)
  if (!pool::dbIsValid(pool)) {
    warning('DB is invalid: ', token)
    stop()
  }
})
```

### Lado do servidor (principais observers e callbacks)
- Upload XLSX (importação de cartinhas):
```226:248:server.R
observeEvent(input$file1, {
  inFile <- input$file1
  # valida extensão e copia para caminho definido em g.arquivo.cartas
  validate(need(ext == "xlsx", "Envie um arquivo XLSX do Excel"))
  caminho <- paste0(getwd(), g.arquivo.cartas)
  file.copy(inFile$datapath, caminho, overwrite = TRUE)
  file.remove(inFile$datapath)
})
```
- Upload de PDFs:
```250:274:server.R
observeEvent(input$file2, {
  # filtra por PDFs, copia para g.cartas.path e informa quantidade adicionada
})
```
- Ações por linha: adotar e marcar presente (com confirmação via `shinyalert`):
```569:609:server.R
observeEvent(input$select_adotar, {
  # valida login e dispara confirmação
  # em caso afirmativo, chama trataShinyAlert → pegaCarta
})
```
```536:567:server.R
observeEvent(input$select_presente, {
  # valida login e dispara confirmação
  # em caso afirmativo, chama trataShinyAlert → pegaPresente
})
```
- Renderizações de tabelas:
```1049:1083:server.R
showCartinhas <- function(input, output, session, my_table) { # prepara colunas, ícones, botões e nomes e publica em ui.tab.cartinhas }
```
```998:1047:server.R
showPresentes <- function (input, output, session, myTb) { # monta colunas, remove itens já entregues e publica em ui.tab.presentes }
```
- Callbacks (DTedit2) para `Cartas_Diversas` e `usuarios`:
```1120:1181:server.R
cartas.insert.callback <- function(data, row, callb = 1) { # valida duplicados, monta INSERT interpolado e recarrega dados }
```

- Ações de negócio no banco:
```866:927:server.R
pegaCarta <- function (cartinha, user.id, user.name) { # UPDATE Cartas_Diversas: adota carta, sincroniza tb_cartas/g.react.cartas e exibe alerta }
```
```930:968:server.R
pegaPresente <- function (cartinha, user.id) { # UPDATE Cartas_Diversas: marca presente entregue e sincroniza estados }
```

### Banco de dados e integrações
- Conexão MariaDB via pool, credenciais em `secrets.R` (se presente):
```303:313:global.R
pool <- pool::dbPool(
  drv = RMariaDB::MariaDB(),
  username = secrets.db.username,
  password = secrets.db.password,
  host = secrets.db.host,
  port = secrets.db.port,
  dbname = 'noel',
  enconding = 'latin1',   # teste
  group = "my-db")
```
- Validação de schema mínimo ao subir:
```317:323:global.R
if (! all(pool::dbListTables(pool) == c("icon_presente", "Cartas_Diversas", "vw_usuarios_ativos", "usuarios",
                              "vw_usuarios", "modulo"))) {
  stop('Erro ao acessar tabela no banco de dados.')
}
```
- Metadados e dados iniciais:
```375:422:global.R
carrega_dados <- function() { # lê Cartas_Diversas (não deletadas), ajusta fatores, prepara g.react.cartas, carrega ícones de brinquedos e resumo }
```

### Regras de negócio (resumo)
- Adoção de cartinha: bloqueio simples para evitar corrida, `UPDATE` da carta, sincronização reativa e feedback ao usuário.
- Presente entregue: atualização de `Status` e reflexão nas tabelas com ícones.
- Importação: validações de layout de planilha (várias abas), normalização e inserção linha a linha; alerta para duplicidades.
- Exclusão: soft-delete marcando `del_bl = TRUE`.

### Logs e monitoramento
- Mensagens de versão e tempo, eventos de login/logout, SQLs, erros exibidos com `shinyalert`.
- Keep-alive periódico por JS (input `count`) validando a conexão do pool.

### Pontos de atenção
- `debug_mode <<- TRUE` e diversos `browser()` ativos — pausarão a execução em produção.
- Variáveis externas: `url_docs`/`url_cartas` devem ser definidas (provavelmente em `sql.R`/config).
- Possível divergência de id: UI define `btn.tab1.refresh`, enquanto o servidor observa `btb.tab1.refresh`.
- Placeholders `uiFiltroArea`/`uiFiltroTema` (UI) não têm `renderUI` visível aqui.
- Charset: locale `pt_BR.utf8`, banco setado com `latin1` — atenção a conversões.

### Referências rápidas
- Versão/app e carga inicial:
```4:16:server.R
version <- 'v0.0.26'
# carrega dados e registra versões dos pacotes
```
- Tabelas do sistema (dashboard Sistema):
```413:419:server.R
output$ui.tab.sys1 <- DT::renderDataTable({logins.conta})
output$ui.tab.sys2 <- DT::renderDataTable({g.logins.sessions})
output$ui.tab.sys3 <- DT::renderDataTable({gTokens2data(g.tokens)})
output$ui.version <- renderText(paste0('Versão dtedit2: ', dtedit2::version(), '       app: ', version, '    token: ', session$token))
```

## Índice de Abas (Módulos)

- [Cartinhas (Administração)](aba-cartinhas-admin.md)
- [Instruções](aba-instrucoes.md)
- [Minhas Cartinhas](aba-minhas-cartinhas.md)
- [Administração de Usuários](aba-administracao-usuarios.md)
- [Informações do Sistema](aba-informacoes-sistema.md)
- [Cartinhas (Lista Geral)](aba-lista-cartinhas.md)
- [Marcar Presentes](aba-marcar-presentes.md)
---

## FastAPI (Migração — Fase 1)

### Ambiente virtual (Windows)
```powershell
py -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Variáveis de ambiente
Crie um arquivo `.env` baseado nos valores de `.env.example`.

### Subir infraestrutura (opcional)
```powershell
docker compose -f docker-compose.app.yml up -d postgres minio
```

### Rodar a aplicação (dev)
```powershell
uvicorn app.main:app --reload --port 8000
```

### Testes
````powershell
pytest -q
````

### Versionamento visível
- Fonte de verdade: arquivo `VERSION` (renderizado no HTML como `versão: x.y.z`).
- Testes garantem a presença de `VERSION` e da string `"versão:"` no HTML base.

