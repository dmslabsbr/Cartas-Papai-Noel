# 🚀 Guia de Deploy - Sistema Noel

Este guia explica como fazer o deploy do Sistema Noel em um servidor de produção usando Docker.

## 📋 Pré-requisitos

- **Docker** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **Git** (para clonar o repositório)
- **Curl** (para testes de saúde)

## 🔧 Configuração Inicial

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd noel-r
```

### 2. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar configurações
nano .env
```

**Variáveis importantes a configurar:**
- `POSTGRES_PASSWORD`: Senha segura para o banco
- `SESSION_SECRET_KEY`: Chave secreta para sessões
- `MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY`: Credenciais do MinIO

### 3. Gerar Chaves Seguras
```bash
# Gerar chave secreta para sessões
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🐳 Deploy com Docker

### Deploy Básico
```bash
# Construir e iniciar todos os serviços
docker compose up -d --build

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f noel-app
```

### Deploy com Limpeza
```bash
# Parar e remover tudo
docker compose down --rmi all

# Reconstruir do zero
docker compose up -d --build
```

## 🔍 Verificação do Deploy

### 1. Verificar Saúde dos Serviços
```bash
# Aplicação
curl http://localhost:8000/health

# MinIO
curl http://localhost:9000/minio/health/ready

# PostgreSQL
docker compose exec postgres pg_isready -U noel_user -d noel_db
```

### 2. Executar Migrações
```bash
# Executar migrações do banco
docker compose exec noel-app alembic upgrade head
```

### 3. Verificar Logs
```bash
# Logs da aplicação
docker compose logs noel-app

# Logs de todos os serviços
docker compose logs
```

## 🌐 Acessos

Após o deploy bem-sucedido:

- **Aplicação**: http://localhost:8000
- **MinIO Console**: http://localhost:9001
- **PostgreSQL**: localhost:5432

## 🔒 Configuração de Produção

### 1. Nginx (Proxy Reverso)
Para usar o Nginx incluído:
```bash
# Iniciar com Nginx
docker compose --profile production up -d
```

### 2. SSL/HTTPS
1. Coloque seus certificados em `./ssl/`
2. Descomente as linhas HTTPS no `nginx.conf`
3. Configure o domínio no `docker compose.yml`

### 3. Firewall
```bash
# Abrir portas necessárias
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22  # SSH
```

## 📊 Monitoramento

### Health Checks
```bash
# Status detalhado
curl http://localhost:8000/health/debug

# Status básico
curl http://localhost:8000/health
```

### Logs em Tempo Real
```bash
# Aplicação
docker compose logs -f noel-app

# Todos os serviços
docker compose logs -f
```

### Métricas de Recursos
```bash
# Uso de recursos
docker stats

# Espaço em disco
docker system df
```

## 🔄 Backup e Restore

### Backup do Banco
```bash
# Criar backup
docker compose exec postgres pg_dump -U noel_user noel_db > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker compose exec -T postgres psql -U noel_user -d noel_db < backup_20240101.sql
```

### Backup do MinIO
```bash
# Backup via MinIO client
docker compose exec minio-init mc mirror minio/cartas /backup/cartas
```

## 🛠️ Manutenção

### Atualizar Aplicação
```bash
# Parar aplicação
docker compose stop noel-app

# Atualizar código
git pull

# Reconstruir e iniciar
docker compose up -d --build noel-app
```

### Limpeza de Recursos
```bash
# Remover containers parados
docker compose down

# Limpar volumes não utilizados
docker volume prune

# Limpar imagens não utilizadas
docker image prune
```

## 🚨 Troubleshooting

### Problemas Comuns

**1. Porta já em uso**
```bash
# Verificar o que está usando a porta
sudo netstat -tulpn | grep :8000

# Parar processo ou mudar porta no docker compose.yml
```

**2. Erro de permissão**
```bash
# Ajustar permissões
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

**3. Banco não conecta**
```bash
# Verificar logs do PostgreSQL
docker compose logs postgres

# Verificar variáveis de ambiente
docker compose exec noel-app env | grep DATABASE
```

**4. MinIO não acessível**
```bash
# Verificar logs do MinIO
docker compose logs minio

# Verificar se o bucket foi criado
docker compose exec minio-init mc ls minio/
```

### Logs de Debug
```bash
# Logs detalhados da aplicação
docker compose logs --tail=100 noel-app

# Logs de todos os serviços
docker compose logs --tail=50
```

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs: `docker compose logs`
2. Teste a saúde: `curl http://localhost:8000/health`
3. Verifique recursos: `docker stats`
4. Consulte este guia ou a documentação do projeto

---

**Última atualização**: $(date +'%Y-%m-%d')
**Versão**: $(cat VERSION)
