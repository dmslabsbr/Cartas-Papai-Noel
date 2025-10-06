import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.auth_service import AuthService

client = TestClient(app)

# Mock para sessões
@pytest.fixture
def mock_session():
    with patch("app.dependencies.auth.Request") as mock_request:
        # Criar um mock para a sessão
        session_mock = {}
        # Configurar o mock da requisição para retornar a sessão mock
        mock_request.session = session_mock
        yield session_mock

# Mock para o serviço de autenticação
@pytest.fixture
def mock_auth_service():
    with patch("app.services.auth_service.AuthService.authenticate") as mock_auth:
        yield mock_auth

# Testes para a página de login
def test_login_page():
    """Teste para verificar se a página de login é carregada corretamente."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text
    assert '<form method="post" action="/login">' in response.text

# Testes para o processo de login
@pytest.mark.asyncio
async def test_login_success(mock_auth_service):
    """Teste para verificar se o login é bem-sucedido com credenciais válidas."""
    # Configurar o mock para retornar sucesso
    mock_auth_service.return_value = (True, {
        "email": "usuario@example.com",
        "display_name": "Usuário Teste",
        "roles": [{"code": "USER", "description": "Usuário comum"}]
    })
    
    # Fazer login
    response = client.post(
        "/login",
        data={"username": "usuario@example.com", "password": "senha123"}
    )
    
    # Verificar redirecionamento após login bem-sucedido
    assert response.status_code == 302
    assert response.headers["location"] == "/"

@pytest.mark.asyncio
async def test_login_invalid_credentials(mock_auth_service):
    """Teste para verificar se o login falha com credenciais inválidas."""
    # Configurar o mock para retornar falha
    mock_auth_service.return_value = (False, None)
    
    # Tentar login com credenciais inválidas
    response = client.post(
        "/login",
        data={"username": "usuario@example.com", "password": "senha_errada"}
    )
    
    # Verificar redirecionamento para página de login com erro
    assert response.status_code == 302
    assert "error=invalid_credentials" in response.headers["location"]

# Testes para rotas protegidas
def test_dashboard_unauthenticated():
    """Teste para verificar se usuários não autenticados são redirecionados."""
    response = client.get("/dashboard", allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("/login")

def test_admin_page_unauthorized():
    """Teste para verificar se usuários sem permissão são bloqueados."""
    # Simular um usuário autenticado, mas sem permissão de admin
    with patch("app.dependencies.auth.get_current_user") as mock_user:
        mock_user.return_value = {
            "email": "usuario@example.com",
            "display_name": "Usuário Teste",
            "roles": [{"code": "USER", "description": "Usuário comum"}]
        }
        
        response = client.get("/admin", allow_redirects=False)
        assert response.status_code == 403  # Forbidden

# Testes para API de autenticação
@pytest.mark.asyncio
async def test_api_login_success(mock_auth_service):
    """Teste para verificar se a API de login retorna token para credenciais válidas."""
    # Configurar o mock para retornar sucesso
    mock_auth_service.return_value = (True, {
        "email": "usuario@example.com",
        "display_name": "Usuário Teste",
        "roles": [{"code": "USER", "description": "Usuário comum"}]
    })
    
    # Fazer login via API
    response = client.post(
        "/api/auth/login",
        data={"username": "usuario@example.com", "password": "senha123"}
    )
    
    # Verificar resposta bem-sucedida
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "usuario@example.com"

@pytest.mark.asyncio
async def test_api_login_invalid_credentials(mock_auth_service):
    """Teste para verificar se a API de login retorna erro para credenciais inválidas."""
    # Configurar o mock para retornar falha
    mock_auth_service.return_value = (False, None)
    
    # Tentar login via API com credenciais inválidas
    response = client.post(
        "/api/auth/login",
        data={"username": "usuario@example.com", "password": "senha_errada"}
    )
    
    # Verificar resposta de erro
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Credenciais inválidas" in data["detail"]

# Testes para logout
def test_logout():
    """Teste para verificar se o logout limpa a sessão e redireciona."""
    with patch("app.main.Request") as mock_request:
        # Criar um mock para a sessão
        session_mock = {"user": {"email": "usuario@example.com"}}
        # Configurar o mock da requisição para retornar a sessão mock
        mock_request.session = session_mock
        
        response = client.get("/logout", allow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/"
        assert "user" not in session_mock  # Verificar se a sessão foi limpa
