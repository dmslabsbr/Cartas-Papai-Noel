## Plano de Migração para Python (FastAPI + PostgreSQL)

Este documento descreve, em etapas, como migrar o aplicativo Shiny (R) para Python, preservando as funcionalidades descritas nos arquivos de abas e no código fonte atual.

### Tecnologias alvo
- Backend: FastAPI (async), Pydantic, SQLAlchemy + Alembic
- Banco: PostgreSQL (com migrações e otimizações)
- Autenticação: via API externa `ldap-auth-api` + sessões (JWT ou cookie de sessão assinado)
  - Referência: [LDAP Auth API](https://github.com/dmslabsbr/ldap-auth-api)
- UI: FastAPI + Jinja2 (templates) + HTMX/Alpine.js + DataTables (ou alternativa com Tabulator)
- Upload/armazenamento de PDFs/Imagens: Filesystem (padrão) com opção de evoluir para MinIO posteriormente
- Testes: Pytest + HTTPX + Coverage
- Observabilidade: Logging estruturado, endpoints de healthcheck
- Infra: Docker/Docker Compose

### Convenções obrigatórias
- Virtualenv obrigatório
  - Windows: `py -m venv .venv` e `./.venv/Scripts/Activate.ps1`
- Versionamento visível
  - Arquivo `VERSION` na raiz (fonte de verdade)
  - Exibir a versão no HTML base (“versão: x.y.z”)
  - Teste que falha se `VERSION` não existir ou HTML não contiver “versão:”

---

## Etapa 0 — Preparação e Estrutura do Projeto
1) Criar estrutura inicial do repositório Python
   - `app/` (código)
     - `main.py` (FastAPI app)
     - `config.py` (settings via `pydantic-settings`)
     - `db.py` (engine/session SQLAlchemy)
     - `models/` (SQLAlchemy models)
     - `schemas/` (Pydantic models)
     - `routers/` (APIs por módulo/aba)
     - `services/` (regras de negócio)
     - `auth/` (LDAP, sessões)
     - `templates/` (Jinja2, base.html com versão)
     - `static/` (CSS/JS/imagens)
   - `alembic/` (migrações)
   - `tests/`
   - `VERSION` (ex.: 0.1.0)
   - `requirements.txt`
   - `README.md` (instruções, virtualenv, execução)
   - `docker-compose.yml` (app, postgres, minio)
   - `.env` (variáveis sensíveis via env)

2) Virtualenv e dependências
   - `py -m venv .venv`
   - `./.venv/Scripts/Activate.ps1`
   - `pip install -r requirements.txt`

3) Versionamento visível
   - Middleware/dep de leitura do `VERSION`
   - Inserir “versão: {{ version }}” no `templates/base.html`
   - Teste Pytest validando versão e HTML

---

## Etapa 1 — Modelagem de Dados (PostgreSQL)
Basear-se em `banco_de_dados.md` e no dump SQL. Adaptações para PostgreSQL:
- Tabelas: `cartas_diversas`, `usuarios`, `modulo`, `icon_presente`
- Views: `vw_usuarios`, `vw_usuarios_ativos`
- Índices/constraints:
  - `cartas_diversas.id_carta` UNIQUE
  - Índices em `status`, `id_usuario`, `del_bl`
  - FK: `usuarios.id_modulo` → `modulo.id_modulo`
  - Considerar `ENUM` para `status` ou `CHECK`
- Charset/locale: UTF-8

Passos práticos:
1) Definir modelos SQLAlchemy (campos equivalentes do MariaDB → Postgres)
2) Alembic: criar migração inicial com schema completo
3) Scripts de carga (seeds) para `modulo` e `icon_presente`
4) Planejar migração de dados (se houver base legada)

---

## Etapa 2 — Autenticação e Sessões (LDAP)
Requisitos a partir do Shiny:
- Login via LDAP (com fallback para usuários locais em debug)
- Controle de tentativas (anti brute-force) e timeouts
- Sessões com dados do usuário (nome, e-mail, matrícula, cargo, permissões)

Implementação proposta (consumindo `ldap-auth-api`):
1) Configurar `AUTH_API_BASE_URL` (ex.: `http://ldap-auth-api:8000`) via `.env`.
2) Rota `/auth/login` (POST) do nosso app:
   - Encaminha `{username, password}` para `POST {AUTH_API_BASE_URL}/auth/check`.
   - Em caso de sucesso, cria sessão local (JWT/cookie) contendo: `email`, `display_name`, `matricula` (se houver), `roles`.
3) Rota `/auth/logout`: invalida sessão local.
4) Middleware/dependency `current_user` para proteger rotas e injetar contexto do usuário.
5) Rate limiting: utilizar limites já providos pela `ldap-auth-api`; opcionalmente adicionar limites locais por rota.

Referência da API externa: [ldap-auth-api](https://github.com/dmslabsbr/ldap-auth-api)

Permissões (ver Controle de Acesso abaixo):
- Papel do usuário determina visibilidade de menus e autorização de ações de negócio.

### Controle de Acesso (RBAC com e-mail como chave principal)
Modelo recomendado:
- Tabela `users` (PK `email`), campos: `email`, `display_name`, `matricula` (opcional), `is_active` (bool), `created_at`.
- Tabela `roles` (lista de papéis): `id`, `code` (ADMIN, RH, USER), `description`.
- Tabela `user_roles`: `user_email` FK → `users.email`, `role_id` FK → `roles.id` (composta única).

Permissões por papel (mínimo viável):
- ADMIN: incluir/editar/excluir criança; incluir cartas; marcar/desmarcar carta como adotada; marcar/desmarcar presente como entregue; administrar usuários.
- RH: incluir cartas; marcar/desmarcar presente como entregue; visualizar tudo.
- USER: visualizar cartinhas, adotar/desistir (dentro de regras), listar “Minhas Cartinhas”.

Observações:
- E-mail é a chave primária para acesso; vincular matrícula quando disponível (para compatibilidade).
- Autorização via dependencies por rota (ex.: `require_roles('ADMIN')`).
- Para granularidade futura, pode-se adicionar tabela `permissions` e `role_permissions`.

---

## Etapa 3 — Módulos (Abas) e Funcionalidades
Mapeamento dos arquivos de abas para rotas/templates e operações.

### 3.1 Cartinhas (Administração)
- Rotas:
  - GET `/admin/cartinhas` (HTML) — tabela com DataTables/Tabulator
  - API REST `/api/cartas` (GET/POST/PUT/DELETE)
    - DELETE = soft delete (marca `del_bl=true`, `del_time=now()`)
- Regras:
  - Validar `id_carta` único
  - Campos obrigatórios: id_carta, Nome, Sexo, Presente, Status
  - Tipos e choices (Sexo, Status)
- Upload de PDFs/Imagens:
  - POST `/admin/upload-cartas` (múltiplos) — validar extensões permitidas: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.webp`.
  - Armazenar no filesystem: `storage/cartas/{id_carta}.{ext}` (padrão). Planejar evolução opcional para MinIO.
- Verificação de integridade (equivalente a `verifica_tb_cartas`)

### 3.2 Instruções
- GET `/instrucoes` — renderiza HTML estático (converter `docs/instrucoes.xhtml` para template ou servir como estático)

### 3.3 Minhas Cartinhas
- GET `/minhas-cartinhas` — filtra por e-mail do usuário logado (ou matricula mapeada, se aplicável)
- Colunas: Nº Carta, Criança, Sexo, Presente, Observação, Status (ícone), Adotante, Cartinha (link)

### 3.4 Administração de Usuários
- GET `/admin/usuarios` (HTML)
- API REST `/api/usuarios` (CRUD)
- Integração com `modulo`
- Regras: `bl_ativo` e `id_modulo` determinam permissões

### 3.5 Informações do Sistema
- GET `/sistema` (HTML)
- Tabelas:
  - Tentativas de login
  - Sessões ativas
  - Tokens/sessões sumarizados
- Ações:
  - Recarregar dados (reprocessar/resumo)
  - Upload `.xlsx` → Importação de cartinhas (3 abas, valida cabeçalhos)
  - Apagar todas as cartinhas (confirmação)

### 3.6 Cartinhas (Lista Geral)
- GET `/cartinhas` (HTML)
- Ações por linha:
  - Visualizar: serve arquivo estático via rota protegida `/files/cartas/{id_carta}` (filesystem), com verificação de existência; opcional: headers de cache.
  - Adotar: POST `/api/cartas/{id_carta}/adotar` (confirmação)
- Concurrency/lock simples (equivalente a `verifica_carta`)

### 3.7 Marcar Presentes
- GET `/presentes` (HTML)
- POST `/api/cartas/{id_carta}/presente` — atualiza `Status='Presente entregue'`
- Regras: require login; irreversível

---

## Etapa 4 — Importação XLSX e Ícones
1) Importação XLSX (3 abas)
   - Endpoint: POST `/admin/importar-cartas` (arquivo `.xlsx`)
   - Validar cabeçalhos (duas variações), normalizar tipos e strings
   - Inserir/atualizar, checar duplicados, reportar inconsistências
2) Ícones de presente (`icon_presente`)
   - Serviço para mapear palavras-chave → fa-icons (construir HTML com classes)
   - Reutilizar a semântica de mapeamento existente no R (normalização e tokenização de texto)

---

## Etapa 5 — UI e Templates
1) Base HTML com navbar/sidebar (papéis do usuário controlam visibilidade)
2) Tabelas com DataTables/Tabulator (colunas, ações, ícones)
3) SweetAlert2 para confirmações (equivalente ao `shinyalert`)
4) Exibir “versão: x.y.z” no rodapé/header
5) Acessibilidade e responsividade

---

## Etapa 6 — Observabilidade, Segurança e Performance
1) Logging estruturado (request/response, erros SQL, auditoria básica)
2) Healthchecks: `/health` (DB + storage)
3) Rate limiting (login), proteção CSRF (se sessões com cookie), validação estrita de inputs Pydantic
4) Índices e tuning SQL (analisar consultas mais frequentes)
5) Cache leve (se necessário) para listas estáticas (ex.: `modulo`, `icon_presente`)
6) Auditoria mínima: registrar quem (email) realizou ações de adoção/entrega/edição

---

## Etapa 7 — Testes
1) Testes unitários (serviços, validações Pydantic)
2) Testes de API (HTTPX): CRUD de cartas/usuários, adoção, presentes, importação XLSX
3) Testes de integração: PostgreSQL, Filesystem (armazenamento), LDAP via `ldap-auth-api` (mockado com test double ou subindo container no compose)
4) Teste de versionamento visível
   - Falha se `VERSION` ausente
   - Falha se HTML base não contém “versão:”

---

## Etapa 8 — Docker e Deploy
1) Docker Compose com serviços:
   - app (FastAPI)
   - postgres
   - ldap-auth-api (opcional: como dependência local)
2) Variáveis via `.env`
3) Scripts de inicialização: migrações Alembic, criação da pasta `storage/` com subpastas (`storage/cartas/`)
4) CI/CD (lint, testes, build)
5) Volumes/mounts: mapear `./storage` → `/app/storage` (persistência dos arquivos)

---

## Tarefas por Módulo (Checklist de Implementação)

### Cartinhas (Admin)
- [ ] Models/CRUD `cartas_diversas`
- [ ] Upload múltiplo de PDFs/Imagens (filesystem)
- [ ] Verificação de integridade (duplicados, PDFs)
- [ ] Tabela HTML com edição inline ou modal

### Instruções
- [ ] Template com conteúdo de `docs/instrucoes.xhtml`

### Minhas Cartinhas
- [ ] Filtro por e-mail do usuário (ou matrícula mapeada)
- [ ] Colunas e ícones conforme regras

### Administração de Usuários
- [ ] CRUD `usuarios` com vínculo a `modulo`
- [ ] Views ou consultas equivalentes para permissões

### Informações do Sistema
- [ ] Tabelas de tentativas/sessões
- [ ] Importador XLSX
- [ ] Botão de apagar cartas (confirmação)

### Cartinhas (Lista Geral)
- [ ] Listagem
- [ ] Visualizar PDF
- [ ] Adoção (com confirmação e lock simples)

### Marcar Presentes
- [ ] Marcação “Presente entregue” (com confirmação)

### Transversais
- [ ] Login/logout via `ldap-auth-api` + sessão
- [ ] Versionamento visível (VERSION + template)
- [ ] Logs + healthcheck
- [ ] Docker Compose (app, postgres, ldap-auth-api)

---

## Mapeamento R → Python (conceitual)
- `g.tokens` (sessões) → sessões HTTP (JWT/cookie) + tabela/sessão em memória/Redis para tentativas
- `reactiveValues` e observers → eventos/rotas HTTP + atualizações via POST/PUT
- `DTedit2` (UI) → DataTables/Tabulator + APIs REST
- `shinyalert` → SweetAlert2 (JS)
- Arquivos XLSX/PDF/Imagens → endpoints FastAPI (upload), armazenamento em filesystem (rota de download); evolução para MinIO opcional
- Verificações (`verifica_tb_cartas`) → serviços Python com respostas JSON e exibição via alert

---

## Notas de Compatibilidade e Riscos
- Substituição de MariaDB por PostgreSQL: revisar tipos e queries.
- LDAP: a autenticação será delegada à `ldap-auth-api`. Definir base URL e estratégia de mocking para testes.
- Concurrency de adoção: garantir idempotência e lock transacional simples (UPDATE com condição).
- Charset/acentuação: tratar normalização (equivalente a `converteUTF`/`ASCII` do R).
- Remover breakpoints (`browser()`) do fluxo migrado; usar logs.

---

## Próximos Passos Imediatos
1) Criar skeleton do projeto (Etapa 0) com `VERSION`, `requirements.txt`, `README.md` e estrutura de diretórios
2) Provisionar Docker Compose com PostgreSQL e `ldap-auth-api`; criar volume `storage/`
3) Definir modelos SQLAlchemy e gerar migração inicial (Alembic)
4) Implementar base HTML (Jinja2) com “versão:”
5) Implementar login via `ldap-auth-api` e sessão
6) Entregar primeiro módulo: Cartinhas (Lista Geral) com Visualizar/Adotar

---

## Lacunas de Especificação (a confirmar antes da implementação)
- URL e política de disponibilidade da `ldap-auth-api` (ambiente local vs. externo) e atributos retornados (para obter e-mail e display name).
- Mapeamento entre LDAP e e-mail canônico (domínio, alias). Confirmar se o `username` é o e-mail ou `sAMAccountName@dominio`.
- Estrutura exata do controle de acesso: papéis finais (ADMIN, RH, USER) e eventuais permissões adicionais.
- Nome e formato do campo de vínculo na tabela de cartinhas: armazenar `adotante_email` (FK users.email) e/ou manter `matricula` para migração.
- Diretórios e políticas de armazenamento local (`storage/cartas/`): limites de tamanho, extensões permitidas, convenção de nomes e limpeza.
- Como servir arquivos (privado/público): exigir login para visualizar PDFs/Imagens? Cache headers necessários?
- Regras de concorrência para adoção/desistência e marcação de presente (tempo de lock, idempotência, retries).
- Layout final dos templates (tema, branding) e interações (DataTables vs. Tabulator, HTMX/Alpine).
- Estratégia de migração de dados do MariaDB para PostgreSQL (ETL, scripts, validações).
- Variáveis de ambiente e secrets definitivos (`AUTH_API_BASE_URL`, `DATABASE_URL`, storage path, etc.).


