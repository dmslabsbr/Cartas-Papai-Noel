"""Database connection and session management for SQLAlchemy."""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from .config import get_settings

logger = logging.getLogger("uvicorn")
settings = get_settings()

# Log database connection details (masked password)
try:
    db_url_display = settings.database_url
    if "@" in db_url_display:
        # Formato esperado: postgresql+psycopg://username:password@host:port/dbname
        parts = db_url_display.split("@")
        if len(parts) >= 2:
            protocol_user_pass = parts[0]  # postgresql+psycopg://username:password
            host_port_db = parts[1]        # host:port/dbname
            
            # Extrair o protocolo e o usuário
            if "://" in protocol_user_pass:
                protocol_parts = protocol_user_pass.split("://")
                protocol = protocol_parts[0]  # postgresql+psycopg
                
                if len(protocol_parts) > 1 and ":" in protocol_parts[1]:
                    username = protocol_parts[1].split(":")[0]  # username
                    masked_url = f"{protocol}://{username}:***@{host_port_db}"
                    logger.info(f"Connecting to database: {masked_url}")
                else:
                    logger.info(f"Connecting to database (URL format not recognized)")
            else:
                logger.info(f"Connecting to database (URL format not recognized)")
        else:
            logger.info(f"Connecting to database (URL format not recognized)")
    else:
        logger.info(f"Connecting to database (URL format not recognized)")
except Exception as e:
    logger.error(f"Error parsing database URL: {str(e)}")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True,  # Check connection validity before using
    poolclass=QueuePool,
    echo=settings.environment == "development",  # Log SQL in development
    connect_args={"options": "-c search_path=public"}  # Forçar o uso do esquema public
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Verificar a conexão e as tabelas existentes
def check_database_connection():
    """Verifica a conexão com o banco de dados e lista as tabelas existentes."""
    try:
        # Verificar conexão
        with engine.connect() as conn:
            # Testar uma consulta simples
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("Database connection test successful")
            
            # Verificar o esquema atual
            result = conn.execute(text("SHOW search_path"))
            search_path = result.fetchone()[0]
            logger.info(f"Current search_path: {search_path}")
            
            # Listar tabelas no esquema public
            inspector = inspect(engine)
            tables = inspector.get_table_names(schema="public")
            logger.info(f"Tables in public schema: {tables}")
            
            # Verificar se a tabela usuarios existe
            if "usuarios" in tables:
                # Verificar estrutura da tabela
                columns = [col["name"] for col in inspector.get_columns("usuarios", schema="public")]
                logger.info(f"Columns in usuarios table: {columns}")
            else:
                logger.warning("Table 'usuarios' not found in public schema!")
                
            # Verificar permissões do usuário
            result = conn.execute(text("SELECT current_user"))
            current_user = result.fetchone()[0]
            logger.info(f"Connected as user: {current_user}")
            
            # Tentar acessar a tabela usuarios diretamente
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM public.usuarios"))
                count = result.fetchone()[0]
                logger.info(f"Number of users in public.usuarios: {count}")
            except Exception as e:
                logger.error(f"Error accessing public.usuarios table: {str(e)}")
                
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

# Executar verificação na inicialização
try:
    check_database_connection()
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")


def get_db():
    """
    Dependency for FastAPI routes that need database access.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(models.Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
