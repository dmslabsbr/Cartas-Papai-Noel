# Multi-stage build para produção

# ========= STAGE 1: builder =========
FROM python:3.12-slim as builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Configurar ambiente Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) COPIE SOMENTE OS MANIFESTS DE DEPENDÊNCIAS (ANTES do código)
# Se usa requirements.txt:
COPY requirements.txt ./

# 2) INSTALE AS DEPENDÊNCIAS (gera wheels cacheáveis)
RUN pip install --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage de produção
FROM python:3.12-slim as production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pacotes de RUNTIME (não de build): libpq5, curl p/ HEALTHCHECK etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*  \
    && apt-get clean

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app


# Configurar ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# 3) COPIE E INSTALE AS WHEELS GERADAS NO BUILDER
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-deps /wheels/*

# Copiar dependências instaladas do stage anterior
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 4) SÓ AGORA COPIE O CÓDIGO DA APLICAÇÃO (invalidará APENAS esta camada)
#    (Essa ordem é o "pulo do gato" do cache!)
# Copiar código da aplicação
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser VERSION ./
COPY --chown=appuser:appuser docker/entrypoint.sh /app/entrypoint.sh
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser VERSION ./app/VERSION
RUN chmod +x /app/entrypoint.sh
#COPY app ./app


# Criar diretórios necessários
RUN mkdir -p /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Expor porta
EXPOSE 8000

# Healthcheck (precisa do curl instalado acima)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint realiza checagens (ex.: manual.html) antes de iniciar
# (se usar um script, não esqueça do exec "$@")
ENTRYPOINT ["/app/entrypoint.sh"]
# Comando de produção (passado ao entrypoint)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info", "--access-log"]
