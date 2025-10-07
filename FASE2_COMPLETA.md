# Fase 2 — Plano de Implementação (Autenticação, RBAC e CRUDs)

## Objetivo
Consolidar autenticação, autorização por papéis (RBAC) e estruturar os CRUDs principais de forma incremental (um CRUD por vez), garantindo testes, migrações e documentação.

## Regras de Visibilidade e Permissão (aplicadas nesta fase)
1. Público (sem login): pode listar e ver detalhes das cartinhas; vê apenas se está adotada (sim/não), nunca quem adotou.
2. Administradores: veem todas as cartinhas, incluindo quem adotou e quem entregou o presente.
3. Somente administradores podem marcar um presente como entregue.
4. Somente usuários logados podem adotar uma cartinha.
5. Usuários logados podem ver as cartinhas e presentes atribuídos ao próprio usuário.

## Escopo da Fase 2
- Autenticação e sessões (integração com serviço externo, p.ex. LDAP API já prevista) e dependências de autorização.
- Modelos ORM (SQLAlchemy) consistentes com o banco atual.
- Migrações Alembic (baseline + ajustes).
- Repositórios e serviços.
- CRUDs implementados incrementalmente: Cartas → Usuários (admin) → Roles/UserRoles (admin).
- Templates mínimos e endpoints REST correspondentes.
- Testes unitários e de integração.

## Sequenciamento (um CRUD por vez)
1) CRUD Cartas (inclui regras de adoção/liberação/entrega e visibilidade por papel)
2) CRUD Usuários (admin)
3) CRUD Roles/UserRoles (admin)

---

## CRUD 1 — Cartas

### Ajustes de Modelo de Dados (Migração)
Tabela `cartas_diversas` (já existente):
- Adições para rastreio de entrega:
  - `entregue_bl BOOLEAN NOT NULL DEFAULT FALSE`
  - `entregue_por_email TEXT NULL REFERENCES usuarios(email)`
  - `entregue_em TIMESTAMPTZ NULL`
- Índices sugeridos:
  - `CREATE INDEX IF NOT EXISTS idx_cartas_entregue ON cartas_diversas(entregue_bl);`
- Status operacionais tratados em serviço (mantendo TEXT com validação): `DISPONIVEL`, `ADOTADA`, `ENTREGUE`.

### ORM e Relacionamentos
- `CartaDiversa` mapeando campos atuais + novos de entrega.
- FK: `adotante_email → usuarios.email`.
- Relações convenientes (opcional): `adotante: Usuario`.

### Schemas Pydantic (respostas por papel)
- `CartaPublic`: campos públicos + `adotada: bool` (derivado de `adotante_email is not null`), sem `adotante_email`.
- `CartaUser`: igual à pública; pode incluir campos adicionais próprios se a carta for do usuário.
- `CartaAdmin`: inclui `adotante_email`, `entregue_bl`, `entregue_por_email`, `entregue_em`.

### Repositório de Cartas (operações)
- `list_public(filters)`; `get_public(id)`
- `list_admin(filters)`; `get_admin(id)`
- `list_by_user(user_email)`
- `adopt(id, user_email)`
- `release(id, by_user_email, is_admin)`
- `mark_delivered(id, admin_email)`

### Serviço de Cartas (regras)
- Adoção: apenas se `status='DISPONIVEL'`, `adotante_email IS NULL`, `entregue_bl=FALSE` → seta `adotante_email`, `status='ADOTADA'`, atualiza `updated_at`.
- Liberação: ADMIN sempre; usuário comum somente se for o adotante → zera adotante e entrega, volta `status='DISPONIVEL'`.
- Entrega: apenas ADMIN e somente se já `status='ADOTADA'` → seta `entregue_bl=TRUE`, `entregue_por_email=admin`, `entregue_em=now()`, (opcional) `status='ENTREGUE'`.

### Endpoints
- Públicos
  - GET `/cartas` (paginação, filtros: `status`, `sexo`, `q`) → `CartaPublic[]`
  - GET `/cartas/{id}` → `CartaPublic`
- Autenticados (USER/ADMIN)
  - POST `/cartas/{id}/adotar` → 200/409/403
  - POST `/cartas/{id}/liberar` → 200/403 (usuário não dono)/permite ADMIN
  - GET `/me/cartas` → cartas adotadas pelo usuário
- Administrativos (ADMIN)
  - GET `/admin/cartas` → `CartaAdmin[]`
  - GET `/admin/cartas/{id}` → `CartaAdmin`
  - POST `/cartas/{id}/entregar` → marcar entregue

### Templates/UI (mínimo)
- Lista pública: coluna “Adotada” (sim/não), sem nome do adotante.
- “Minhas cartinhas” (usuário logado): lista apenas do próprio usuário.
- Admin: lista com “Adotada por”, “Entregue por”, “Entregue em” e ação “Marcar entregue”.

### Testes (obrigatórios para regras 1–5)
- Público não vê `adotante_email`; vê `adotada` corretamente.
- Usuário logado adota carta disponível; usuário não logado recebe 403.
- Usuário vê somente suas cartas em `/me/cartas`.
- Usuário comum não consegue marcar entregue (403).
- Admin vê `adotante_email` e consegue marcar entregue.
- Conflitos: adoção dupla retorna 409.

### Critérios de Aceite (CRUD Cartas)
- Endpoints e templates implementados conforme acima.
- Regras 1–5 atendidas.
- Testes unitários e de integração passando.

---

## CRUD 2 — Usuários (Admin)

### Escopo
- Listar usuários, obter detalhes, ativar/inativar.

### Endpoints (ADMIN)
- GET `/usuarios` (filtros: ativo, busca)
- GET `/usuarios/{email}`
- PATCH `/usuarios/{email}` (payload mínimo: `bl_ativo: bool`)

### Testes
- RBAC: somente ADMIN.
- Atualização de `bl_ativo` reflete na listagem e nas permissões.

### Critérios de Aceite
- Operações funcionando e protegidas por role.

---

## CRUD 3 — Roles e UserRoles (Admin)

### Escopo
- Listar roles; atribuir/revogar role a usuário.

### Endpoints (ADMIN)
- GET `/roles`
- POST `/usuarios/{email}/roles/{role}` (atribuir)
- DELETE `/usuarios/{email}/roles/{role}` (revogar)

### Testes
- RBAC: somente ADMIN.
- Idempotência nas operações (sem duplicar vínculos).

### Critérios de Aceite
- Atribuições refletidas nas dependências de autorização.

---

## Autenticação, Sessão e RBAC
- Integração com serviço de autenticação externo (p.ex. LDAP API já prevista no projeto).
- `SessionMiddleware` com cookie seguro (HttpOnly; Secure em produção; TTL via env).
- Dependências de autorização:
  - `require_user()` para rotas autenticadas.
  - `require_role('ADMIN')` para rotas administrativas.

## Alembic (Migrações)
- Criar baseline a partir do banco atual.
- Criar migração para campos de entrega em `cartas_diversas` e índices.
- Política: sem autogenerate cego; revisar diffs; nomear por feature; rollback validado em dev.

## Observabilidade e Segurança
- Logs estruturados (request_id, user_email, ação: adotar/liberar/entregar).
- CORS restrito às origens do front.
- Validação de dados com Pydantic; sanitização básica.

## Versionamento Visível (continuidade)
- Manter arquivo `VERSION` como fonte de verdade e renderização “versão:” no HTML base.
- Testes que falham se `VERSION` não existir ou se o HTML base não contiver “versão:”.

## Entregáveis da Fase 2
- CRUD Cartas concluído (com regras 1–5), depois CRUD Usuários (admin), depois CRUD Roles/UserRoles (admin), todos com testes e documentação.

## Checklist de Conclusão (para quando finalizar a fase)
- [x] Autenticação e sessão configuradas (dev e prod) — sessão e dependências ativas; integração externa em uso
- [x] Migrações Alembic aplicadas (baseline + entrega) — campos de entrega e `urlcarta`
- [x] CRUD Cartas implementado e testado — adoção/liberação/entrega + upload de anexos
- [x] CRUD Usuários (admin) implementado (API)
- [x] CRUD Roles/UserRoles (admin) implementado (API)
- [x] Documentação atualizada (OpenAPI e README) — `docs/api_reference.md` e `README.md`
