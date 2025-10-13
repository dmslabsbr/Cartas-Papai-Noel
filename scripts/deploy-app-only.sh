#!/bin/bash

# ===========================================
# SCRIPT DE DEPLOY - APENAS APLICAÇÃO
# Sistema Noel - Serviços Externos
# ===========================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar se está no diretório correto
if [ ! -f "docker-compose.app-only.yml" ]; then
    error "Execute este script no diretório raiz do projeto (onde está o docker-compose.app-only.yml)"
    exit 1
fi

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    error "Arquivo .env não encontrado!"
    echo "Copie o arquivo env.app-only.example para .env e configure as variáveis:"
    echo "  cp env.app-only.example .env"
    echo "  nano .env"
    exit 1
fi

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    error "Docker não está instalado!"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! docker compose version &> /dev/null; then
    error "Docker Compose não está instalado!"
    exit 1
fi

log "Iniciando deploy da aplicação Noel (serviços externos)..."

# Parar container existente
log "Parando container existente..."
docker compose -f docker-compose.app-only.yml down

# Remover imagem antiga (opcional)
if [ "$1" = "--clean" ]; then
    log "Removendo imagem antiga..."
    docker compose -f docker-compose.app-only.yml down --rmi all
fi

# Construir e iniciar container
log "Construindo e iniciando container da aplicação..."
docker compose -f docker-compose.app-only.yml up -d --build

# Aguardar aplicação ficar pronta
log "Aguardando aplicação ficar pronta..."
sleep 20

# Verificar saúde da aplicação
log "Verificando saúde da aplicação..."

# Verificar aplicação
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    success "Aplicação Noel está funcionando"
else
    error "Aplicação Noel não está respondendo"
    log "Verificando logs..."
    docker compose -f docker-compose.app-only.yml logs noel-app
    exit 1
fi

# Verificar conectividade com serviços externos
log "Verificando conectividade com serviços externos..."

# Testar conexão com banco (via health check da aplicação)
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q '"db_ok":true'; then
    success "Conexão com PostgreSQL OK"
else
    warning "Problema na conexão com PostgreSQL"
fi

# Testar conexão com MinIO
if echo "$HEALTH_RESPONSE" | grep -q '"minio_ok":true'; then
    success "Conexão com MinIO OK"
else
    warning "Problema na conexão com MinIO"
fi

# Testar conexão com LDAP
if echo "$HEALTH_RESPONSE" | grep -q '"ldap_ok":true'; then
    success "Conexão com LDAP OK"
else
    warning "Problema na conexão com LDAP"
fi

# Executar migrações do banco (se necessário)
log "Verificando migrações do banco de dados..."
docker compose -f docker-compose.app-only.yml exec noel-app alembic current || warning "Não foi possível verificar migrações"

# Verificar logs
log "Verificando logs da aplicação..."
echo ""
echo "=== LOGS DA APLICAÇÃO ==="
docker compose -f docker-compose.app-only.yml logs --tail=20 noel-app

echo ""
echo "=== STATUS DO CONTAINER ==="
docker compose -f docker-compose.app-only.yml ps

echo ""
echo "=== HEALTH CHECK DETALHADO ==="
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health

echo ""
success "Deploy da aplicação concluído!"
echo ""
echo "Acesse a aplicação em:"
echo "  - HTTP:  http://localhost:8000"
echo ""
echo "Para ver logs em tempo real:"
echo "  docker compose -f docker-compose.app-only.yml logs -f noel-app"
echo ""
echo "Para parar a aplicação:"
echo "  docker compose -f docker-compose.app-only.yml down"
echo ""
echo "Para verificar saúde:"
echo "  curl http://localhost:8000/health"
echo ""
