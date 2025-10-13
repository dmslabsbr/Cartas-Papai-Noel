#!/usr/bin/env python3
"""
Script para testar a conexão com o banco de dados PostgreSQL
"""
import os
import sys
import psycopg
from urllib.parse import urlparse

def test_db_connection():
    """Testa a conexão com o banco de dados"""
    
    # Obter URL do banco das variáveis de ambiente
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ ERRO: Variável DATABASE_URL não encontrada")
        return False
    
    print(f"🔍 Testando conexão com banco de dados...")
    print(f"📊 URL: {db_url.split('@')[0]}@***" if "@" in db_url else f"📊 URL: {db_url}")
    
    try:
        # Converter formato SQLAlchemy para formato direto do psycopg
        if db_url.startswith('postgresql+psycopg://'):
            db_url = db_url.replace('postgresql+psycopg://', 'postgresql://')
        
        # Testar conexão
        with psycopg.connect(db_url, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS test")
                result = cur.fetchone()
                
                if result and result[0] == 1:
                    print("✅ Conexão com banco de dados: OK")
                    
                    # Testar algumas queries básicas
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    print(f"📋 Versão PostgreSQL: {version}")
                    
                    # Verificar se o schema existe
                    cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'public'")
                    schema = cur.fetchone()
                    if schema:
                        print("✅ Schema 'public': OK")
                    else:
                        print("❌ Schema 'public': NÃO ENCONTRADO")
                    
                    # Verificar tabelas
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        ORDER BY table_name
                    """)
                    tables = cur.fetchall()
                    print(f"📊 Tabelas encontradas: {len(tables)}")
                    for table in tables[:5]:  # Mostrar apenas as primeiras 5
                        print(f"   - {table[0]}")
                    if len(tables) > 5:
                        print(f"   ... e mais {len(tables) - 5} tabelas")
                    
                    return True
                else:
                    print("❌ ERRO: Query de teste falhou")
                    return False
                    
    except psycopg.OperationalError as e:
        print(f"❌ ERRO de conexão: {e}")
        return False
    except psycopg.Error as e:
        print(f"❌ ERRO do PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ ERRO inesperado: {e}")
        return False

def test_network_connectivity():
    """Testa conectividade de rede"""
    import socket
    
    # Extrair host e porta da URL
    db_url = os.getenv('DATABASE_URL', '')
    if not db_url:
        return False
    
    try:
        # Parse da URL
        if db_url.startswith('postgresql+psycopg://'):
            db_url = db_url.replace('postgresql+psycopg://', 'postgresql://')
        
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port or 5432
        
        print(f"🌐 Testando conectividade de rede...")
        print(f"📍 Host: {host}")
        print(f"🔌 Porta: {port}")
        
        # Testar conexão TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ Conectividade de rede: OK")
            return True
        else:
            print(f"❌ Conectividade de rede: FALHOU (código: {result})")
            return False
            
    except Exception as e:
        print(f"❌ ERRO no teste de rede: {e}")
        return False

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE CONEXÃO COM BANCO DE DADOS")
    print("=" * 50)
    
    # Testar conectividade de rede primeiro
    network_ok = test_network_connectivity()
    print()
    
    # Testar conexão com banco
    db_ok = test_db_connection()
    print()
    
    # Resultado final
    if network_ok and db_ok:
        print("🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("💥 ALGUNS TESTES FALHARAM!")
        sys.exit(1)
