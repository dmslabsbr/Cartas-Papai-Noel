# 🚀 Deploy Apenas da Aplicação - Sistema Noel

Este guia explica como fazer o deploy apenas da aplicação Noel, conectando a serviços externos de PostgreSQL e MinIO.

## 📋 Pré-requisitos

- **Docker** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **PostgreSQL** rodando em servidor externo
- **MinIO** rodando em servidor externo
- **Curl** (para testes de saúde)

## 🔧 Configuração

### 1. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp env.app-only.example .env

# Editar configurações
nano .env
```

### 2. Configurar Conexões Externas

**PostgreSQL:**
```bash
DB_HOST=seu-servidor-postgres.com
DB_PORT=5432
DB_NAME=noel_db
DB_USER=noel_user
DB_PASSWORD=sua_senha
```

**MinIO:**
```bash
MINIO_ENDPOINT=https://seu-servidor-minio.com:9000
MINIO_ACCESS_KEY=seu_usuario
MINIO_SECRET_KEY=sua_senha
MINIO_BUCKET=cartas
MINIO_SECURE=true
```

## 🐳 Deploy da Aplicação

### Deploy Básico
```bash
# Construir e iniciar apenas a aplicação
docker compose -f docker-compose.app-only.yml up -d --build

# Verificar status
docker compose -f docker-compose.app-only.yml ps

# Ver logs
docker compose -f docker-compose.app-only.yml logs -f noel-app
```

### Deploy com Script
```bash
# Usar script automatizado
chmod +x scripts/deploy-app-only.sh
./scripts/deploy-app-only.sh
```

## 🔍 Verificação

### 1. Verificar Saúde da Aplicação
```bash
# Health check básico
curl http://localhost:8000/health

# Health check detalhado
curl http://localhost:8000/health/debug
```

### 2. Verificar Conectividade
```bash
# Verificar conexão com PostgreSQL
docker compose -f docker-compose.app-only.yml exec noel-app python -c "from app.db import get_db; db = next(get_db()); print('PostgreSQL: OK' if db else 'PostgreSQL: ERRO')"

# Verificar conexão com MinIO
docker compose -f docker-compose.app-only.yml exec noel-app python -c "from app.services.storage_service import StorageService; storage = StorageService(); print('MinIO: OK' if storage._client() else 'MinIO: ERRO')"
```

### 3. Executar Migrações
```bash
# Executar migrações do banco
docker compose -f docker-compose.app-only.yml exec noel-app alembic upgrade head
```

## 🌐 Acesso

Após o deploy bem-sucedido:
- **Aplicação**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 🔧 Configurações Avançadas

### 1. Porta Personalizada
```yaml
# No docker compose.app-only.yml
ports:
  - "8080:8000"  # Aplicação na porta 8080
```

### 2. Variáveis de Ambiente Adicionais
```bash
# No arquivo .env
THUMB_SIZE=200x300
SESSION_MAX_AGE=43200  # 12 horas
LOGIN_EMAIL_DEFAULT_DOMAIN=mpgo.mp.br
```

### 3. Volumes Personalizados
```yaml
# No docker compose.app-only.yml
volumes:
  - ./logs:/app/logs
  - ./uploads:/app/uploads
```

## 📊 Monitoramento

### Logs em Tempo Real
```bash
# Logs da aplicação
docker compose -f docker-compose.app-only.yml logs -f noel-app

# Logs com timestamps
docker compose -f docker-compose.app-only.yml logs -f -t noel-app
```

### Métricas de Recursos
```bash
# Uso de recursos
docker stats noel-app

# Informações do container
docker inspect noel-app
```

### Health Check Detalhado
```bash
# Status completo
curl -s http://localhost:8000/health | python3 -m json.tool

# Apenas status
curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"'
```

## 🔄 Atualizações

### Atualizar Aplicação
```bash
# Parar aplicação
docker compose -f docker-compose.app-only.yml stop noel-app

# Atualizar código
git pull

# Reconstruir e iniciar
docker compose -f docker-compose.app-only.yml up -d --build noel-app
```

### Atualizar com Zero Downtime
```bash
# Build da nova imagem
docker compose -f docker-compose.app-only.yml build noel-app

# Recriar container
docker compose -f docker-compose.app-only.yml up -d --no-deps noel-app
```

## 🛠️ Manutenção

### Backup da Aplicação
```bash
# Backup do código
tar -czf noel-app-backup-$(date +%Y%m%d).tar.gz app/ alembic/ alembic.ini VERSION

# Backup dos logs
docker compose -f docker-compose.app-only.yml exec noel-app tar -czf /app/logs-backup.tar.gz /app/logs
```

### Limpeza
```bash
# Parar e remover container
docker compose -f docker-compose.app-only.yml down

# Remover imagem
docker compose -f docker-compose.app-only.yml down --rmi all

# Limpar volumes
docker volume prune
```

## 🚨 Troubleshooting

### Problemas Comuns

**1. Erro de conexão com PostgreSQL**
```bash
# Verificar conectividade
docker compose -f docker-compose.app-only.yml exec noel-app ping seu-servidor-postgres.com

# Verificar variáveis
docker compose -f docker-compose.app-only.yml exec noel-app env | grep DB_
```

**2. Erro de conexão com MinIO**
```bash
# Verificar conectividade
docker compose -f docker-compose.app-only.yml exec noel-app curl -I https://seu-servidor-minio.com:9000

# Verificar variáveis
docker compose -f docker-compose.app-only.yml exec noel-app env | grep MINIO_
```

**3. Aplicação não inicia**
```bash
# Ver logs detalhados
docker compose -f docker-compose.app-only.yml logs noel-app

# Verificar health check
curl -v http://localhost:8000/health
```

**4. Porta já em uso**
```bash
# Verificar o que está usando a porta
sudo netstat -tulpn | grep :8000

# Mudar porta no docker compose.app-only.yml
```

### Logs de Debug
```bash
# Logs detalhados
docker compose -f docker-compose.app-only.yml logs --tail=100 noel-app

# Logs com timestamps
docker compose -f docker-compose.app-only.yml logs -f -t noel-app

# Health check debug
curl http://localhost:8000/health/debug
```

## 📞 Comandos Úteis

```bash
# Status do container
docker compose -f docker-compose.app-only.yml ps

# Logs em tempo real
docker compose -f docker-compose.app-only.yml logs -f noel-app

# Entrar no container
docker compose -f docker-compose.app-only.yml exec noel-app bash

# Reiniciar aplicação
docker compose -f docker-compose.app-only.yml restart noel-app

# Parar aplicação
docker compose -f docker-compose.app-only.yml down

# Health check
curl http://localhost:8000/health
```

---

**Última atualização**: $(date +'%Y-%m-%d')
**Versão**: $(cat VERSION)
