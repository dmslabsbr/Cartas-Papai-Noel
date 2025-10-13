# Noel (FastAPI)

Aplicativo web para gestão de cartinhas de Natal (adoção, entrega de presentes e administração), desenvolvido em Python com FastAPI, Jinja2, SQLAlchemy (PostgreSQL) e integração com MinIO para anexos (imagens/PDFs).

## Funcionalidades
- Lista pública de cartinhas com filtros (disponíveis, adotadas, entregues, minhas)
- Visualização de detalhes da cartinha
- Adoção e cancelamento (com confirmações)
- Administração de cartinhas (criar, editar, excluir, marcar/desmarcar entregue)
- Upload de anexo (imagem/PDF) com integração MinIO
- Relatórios:
  - Agregador de relatórios: `/relatorios/`
  - Anexos órfãos (arquivos no bucket sem referência em cartinhas): `/relatorios/anexos-orfaos`
  - Todas as cartinhas (tabela com filtros, ordenação, ações e resumo): `/relatorios/cartas`
- Controle de acesso por papéis (ex.: ADMIN) e dependências por rota
- Versionamento visível: a versão do app é lida do arquivo `VERSION` e exibida no rodapé

### Miniaturas e PDFs
- Geração de miniaturas (página: `/cartas/admin/miniaturas`) com feedback via Toasts
- Suporte a miniatura de imagens (JPEG/PNG/WEBP)
- Suporte a PDFs: extração da primeira imagem embutida da 1ª página usando PyMuPDF (fitz) para gerar a miniatura
- Na listagem pública:
  - Exibe miniatura quando disponível
  - Para PDFs sem miniatura, exibe `static/pdf128.png`
  - Para cartas sem anexo, exibe `static/sem-imagem128.png`

### Acesso e UX
- Botões de filtro “Adotadas” e “Presente Entregue” visíveis apenas para usuários com roles `ADMIN` ou `RH`
- Login: se o usuário digitar apenas o usuário (sem @domínio), o cliente completa automaticamente e o backend também normaliza

## Estrutura do Projeto
```
app/
  main.py           # ponto de entrada FastAPI e configuração de templates
  config.py         # Settings via pydantic-settings (.env)
  db.py             # engine/session do SQLAlchemy
  models/           # modelos SQLAlchemy
  schemas/          # modelos Pydantic
  repositories/     # acesso a dados
  services/         # regras de negócio (ex.: StorageService/MinIO)
  routers/          # rotas (cartas, relatórios)
  templates/        # Jinja2 (base.html + páginas)
  static/           # assets estáticos
alembic/            # migrações
requirements.txt    # dependências
VERSION             # versão semântica (fonte de verdade)
```

## Requisitos
- Python 3.12+
- PostgreSQL
- MinIO (ou compatível S3) para anexos

## Instalação (Windows)
```powershell
py -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Variáveis de Ambiente (.env)
Crie um arquivo `.env` na raiz com as chaves abaixo (exemplo):
```
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/noel

MINIO_ENDPOINT=http://127.0.0.1:9000
MINIO_BUCKET=cartas
# Use um dos pares abaixo
MINIO_ACCESS_KEY=seu_access_key
MINIO_SECRET_KEY=sua_secret_key
# ou
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=adminsecret

LDAP_API_URL=http://auth-api.example.com
SESSION_SECRET_KEY=mude_esta_chave_em_producao
SESSION_MAX_AGE=86400

# Domínio padrão para completar e-mails de login quando omitido pelo usuário
LOGIN_EMAIL_DEFAULT_DOMAIN=mpgo.mp.br

# Tamanho da miniatura gerada (LxA)
THUMB_SIZE=200x300
```

## Migrações de Banco
```powershell
. .venv\Scripts\Activate.ps1
alembic upgrade head
```

## Executar o App (dev)
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Página pública de cartinhas: `http://127.0.0.1:8000/cartas/`
- Administração: `http://127.0.0.1:8000/cartas/admin` (requer ADMIN)
- Relatórios (agregador): `http://127.0.0.1:8000/relatorios/`
- Relatório Anexos Órfãos: `http://127.0.0.1:8000/relatorios/anexos-orfaos`

## Testes
```powershell
pytest -q
```

## Versionamento Visível
- A versão é lida do arquivo `VERSION` (ex.: `0.1.15`)
- O rodapé exibe “versão: x.y.z” via partial `templates/_version.html`

## Rotas Principais
- Cartinhas (público):
  - GET `/cartas/` (HTML)
  - GET `/cartas/{id_carta}` (HTML)
- Cartinhas (API autenticada):
  - GET `/cartas/api`
  - GET `/cartas/api/{id_carta}`
  - POST `/cartas/api/adopt`
  - POST `/cartas/api/cancel/{id_carta}`
- Administração (ADMIN):
  - HTML: `/cartas/admin`
  - API: POST `/cartas/api/admin/create`, PUT `/cartas/api/admin/{id_carta}`
  - API Anexo: POST `/cartas/api/admin/{id_carta}/anexo`
  - Entrega: POST `/cartas/deliver/{id_carta}`, POST `/cartas/undeliver/{id_carta}`
- Relatórios (ADMIN):
  - `/relatorios/` (agregador)
  - `/relatorios/anexos-orfaos` (HTML)
  - `/relatorios/api/object-url?object_name=...` (GET URL assinada)
  - `/relatorios/api/delete-object` (POST apagar objeto)

## Boas Práticas / Segurança
- Nunca faça commit de `.env`, `.venv/`, dumps `.sql` e planilhas `.xlsx`
- Mantenha `SESSION_SECRET_KEY` forte em produção
- Restrinja CORS/hosts em produção (ver `app/main.py`)
- Controle de acesso por papéis usando dependencies (`require_roles`)

## Docker (opcional)
O repositório inclui `Dockerfile`. Para Compose, ajuste conforme seu ambiente (PostgreSQL/MinIO) e aponte variáveis via `.env`.

### Dependências de build
- As dependências Python são instaladas a partir de `requirements.txt` (inclui `pymupdf` para miniaturas de PDFs). Para garantir que a nova lib esteja disponível no container, reconstrua a imagem:
```bash
docker compose build --no-cache noel-app
docker compose up -d noel-app
```

---

Contribuições são bem-vindas. Abra issues/PRs com melhorias e correções.

