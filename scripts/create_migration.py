"""
Script para criar uma migração inicial do Alembic.

Este script configura o ambiente Alembic diretamente, sem depender
de variáveis de ambiente ou do arquivo alembic.ini.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from alembic import command
from alembic.config import Config
from app.config import get_settings
from app.db import Base
from app.models import *  # Importar todos os modelos


def create_migration():
    """Cria uma migração inicial do Alembic."""
    # Obter as configurações da aplicação
    settings = get_settings()
    
    # Criar o objeto de configuração do Alembic
    alembic_cfg = Config(str(root_dir / "alembic.ini"))
    
    # Configurar o diretório de scripts do Alembic
    alembic_cfg.set_main_option("script_location", str(root_dir / "alembic"))
    
    # Configurar a URL do banco de dados (manter o driver psycopg3 se presente)
    db_url = settings.database_url

    # Escapar o caractere % duplicando-o para evitar erro de interpolação
    db_url = db_url.replace("%", "%%")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    masked = db_url
    try:
        if "@" in db_url and "://" in db_url:
            proto_userpass, hostpart = db_url.split("@", 1)
            proto, userpass = proto_userpass.split("://", 1)
            user = userpass.split(":")[0]
            masked = f"{proto}://{user}:***@{hostpart}"
    except Exception:
        pass

    print(f"Criando migração inicial usando URL: {masked}")
    
    try:
        # Criar a revisão
        command.revision(
            alembic_cfg,
            message="Initial migration",
            autogenerate=True
        )
        print("Migração criada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar migração: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_migration()
