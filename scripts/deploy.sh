#!/bin/bash

# ===========================================
# SCRIPT DE DEPLOY PARA PRODUÇÃO
# Sistema Noel - Cartinhas do Papai Noel
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
if [ ! -f "docker compose.yml" ]; then
    error "Execute este script no diretório raiz do projeto (onde está o docker compose.yml)"
    exit 1
fi

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    error "Arquivo .env não encontrado!"
    echo "Copie o arquivo env.example para .env e configure as variáveis:"
    echo "  cp env.example .env"
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

log "Iniciando deploy do Sistema Noel..."

# Parar containers existentes
log "Parando containers existentes..."
docker compose down

# Remover imagens antigas (opcional)
if [ "$1" = "--clean" ]; then
    log "Removendo imagens antigas..."
    docker compose down --rmi all
fi

# Fazer backup do banco (se existir)
if docker compose ps postgres | grep -q "Up"; then
    log "Fazendo backup do banco de dados..."
    mkdir -p backups
    docker compose exec -T postgres pg_dump -U noel_user noel_db > "backups/backup_$(date +%Y%m%d_%H%M%S).sql" || warning "Não foi possível fazer backup do banco"
fi

# Construir e iniciar containers
log "Construindo e iniciando containers..."
docker compose up -d --build

# Aguardar serviços ficarem prontos
log "Aguardando serviços ficarem prontos..."
sleep 30

# Verificar saúde dos serviços
log "Verificando saúde dos serviços..."

# Verificar PostgreSQL
if docker compose exec -T postgres pg_isready -U noel_user -d noel_db > /dev/null 2>&1; then
    success "PostgreSQL está funcionando"
else
    error "PostgreSQL não está respondendo"
    exit 1
fi

# Verificar MinIO
if curl -f http://localhost:9000/minio/health/ready > /dev/null 2>&1; then
    success "MinIO está funcionando"
else
    error "MinIO não está respondendo"
    exit 1
fi

# Verificar aplicação
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    success "Aplicação Noel está funcionando"
else
    error "Aplicação Noel não está respondendo"
    exit 1
fi

# Executar migrações do banco
log "Executando migrações do banco de dados..."
docker compose exec -T noel-app alembic upgrade head

# Verificar logs
log "Verificando logs dos serviços..."
echo ""
echo "=== LOGS DA APLICAÇÃO ==="
docker compose logs --tail=20 noel-app

echo ""
echo "=== STATUS DOS CONTAINERS ==="
docker compose ps

echo ""
success "Deploy concluído com sucesso!"
echo ""
echo "Acesse a aplicação em:"
echo "  - HTTP:  http://localhost:8000"
echo "  - MinIO Console: http://localhost:9001"
echo ""
echo "Para ver logs em tempo real:"
echo "  docker compose logs -f noel-app"
echo ""
echo "Para parar os serviços:"
echo "  docker compose down"
echo ""
