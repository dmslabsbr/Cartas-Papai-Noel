import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.main import app
from app.models import CartaDiversa
from app.repositories import CartasRepository

client = TestClient(app)

# Mock para o usuário autenticado
@pytest.fixture
def mock_auth_user():
    with patch("app.dependencies.auth.get_current_user") as mock_user:
        mock_user.return_value = {
            "email": "usuario@example.com",
            "display_name": "Usuário Teste",
            "roles": [{"code": "USER", "description": "Usuário comum"}]
        }
        yield mock_user

# Mock para o usuário administrador
@pytest.fixture
def mock_admin_user():
    with patch("app.dependencies.auth.get_current_user") as mock_user:
        mock_user.return_value = {
            "email": "admin@example.com",
            "display_name": "Admin Teste",
            "roles": [{"code": "ADMIN", "description": "Administrador"}]
        }
        yield mock_user

# Mock para o repositório de cartinhas
@pytest.fixture
def mock_cartas_repo():
    with patch("app.routers.cartas.CartasRepository") as mock_repo:
        # Criar um mock para o repositório
        repo_instance = MagicMock()
        mock_repo.return_value = repo_instance
        yield repo_instance

# Testes para listagem de cartinhas
def test_list_cartas_authenticated(mock_auth_user, mock_cartas_repo):
    """Teste para verificar se usuários autenticados podem ver a lista de cartinhas."""
    # Configurar o mock para retornar uma lista de cartinhas
    mock_cartas_repo.get_active_cartas.return_value = [
        MagicMock(
            id=1,
            id_carta=101,
            nome="Criança 1",
            sexo="M",
            presente="Brinquedo",
            status="disponível",
            adotante_email=None,
            del_bl=False
        ),
        MagicMock(
            id=2,
            id_carta=102,
            nome="Criança 2",
            sexo="F",
            presente="Boneca",
            status="adotada",
            adotante_email="outro@example.com",
            del_bl=False
        )
    ]
    # Configurar o mock para retornar a contagem total
    mock_cartas_repo.db.query().filter().count.return_value = 2
    
    response = client.get("/cartas/")
    assert response.status_code == 200
    assert "Criança 1" in response.text
    assert "Criança 2" in response.text
    assert "Brinquedo" in response.text
    assert "Boneca" in response.text

def test_list_cartas_unauthenticated():
    """Teste para verificar se usuários não autenticados são redirecionados."""
    response = client.get("/cartas/", allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("/login")

# Testes para visualização de cartinha
def test_view_carta_authenticated(mock_auth_user, mock_cartas_repo):
    """Teste para verificar se usuários autenticados podem ver detalhes de uma cartinha."""
    # Configurar o mock para retornar uma cartinha específica
    mock_cartas_repo.get_by_id_carta.return_value = MagicMock(
        id=1,
        id_carta=101,
        nome="Criança 1",
        sexo="M",
        presente="Brinquedo",
        status="disponível",
        adotante_email=None,
        del_bl=False,
        observacao="Observação de teste",
        created_at=MagicMock(strftime=lambda fmt: "01/01/2023 10:00"),
        updated_at=MagicMock(strftime=lambda fmt: "01/01/2023 10:00")
    )
    
    response = client.get("/cartas/101")
    assert response.status_code == 200
    assert "Criança 1" in response.text
    assert "Brinquedo" in response.text
    assert "Observação de teste" in response.text
    assert "Adotar esta cartinha" in response.text  # Botão de adoção deve estar presente

# Testes para adoção de cartinha
def test_adopt_carta(mock_auth_user, mock_cartas_repo):
    """Teste para verificar se usuários podem adotar cartinhas."""
    # Configurar o mock para retornar uma cartinha adotada
    mock_cartas_repo.adopt_carta.return_value = MagicMock(
        id=1,
        id_carta=101,
        nome="Criança 1",
        sexo="M",
        presente="Brinquedo",
        status="adotada",
        adotante_email="usuario@example.com",
        del_bl=False
    )
    
    response = client.post("/cartas/adopt/101", allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/cartas/101"
    mock_cartas_repo.adopt_carta.assert_called_once_with(101, "usuario@example.com")

def test_cancel_adoption(mock_auth_user, mock_cartas_repo):
    """Teste para verificar se usuários podem cancelar adoções."""
    # Configurar o mock para retornar uma cartinha com adoção cancelada
    mock_cartas_repo.cancel_adoption.return_value = MagicMock(
        id=1,
        id_carta=101,
        nome="Criança 1",
        sexo="M",
        presente="Brinquedo",
        status="disponível",
        adotante_email=None,
        del_bl=False
    )
    
    response = client.post("/cartas/cancel/101", allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/cartas?status=minhas"
    mock_cartas_repo.cancel_adoption.assert_called_once_with(101, "usuario@example.com")

# Testes para área administrativa
def test_admin_cartas_authorized(mock_admin_user, mock_cartas_repo):
    """Teste para verificar se administradores podem acessar a área administrativa."""
    # Configurar o mock para retornar todas as cartinhas
    mock_cartas_repo.db.query().order_by().offset().limit().all.return_value = [
        MagicMock(
            id=1,
            id_carta=101,
            nome="Criança 1",
            sexo="M",
            presente="Brinquedo",
            status="disponível",
            adotante_email=None,
            del_bl=False
        ),
        MagicMock(
            id=2,
            id_carta=102,
            nome="Criança 2",
            sexo="F",
            presente="Boneca",
            status="adotada",
            adotante_email="outro@example.com",
            del_bl=False
        )
    ]
    # Configurar o mock para retornar a contagem total
    mock_cartas_repo.db.query().count.return_value = 2
    
    response = client.get("/cartas/admin")
    assert response.status_code == 200
    assert "Administração de Cartinhas" in response.text
    assert "Criança 1" in response.text
    assert "Criança 2" in response.text
    assert "Nova Cartinha" in response.text  # Botão para adicionar cartinha

def test_admin_cartas_unauthorized(mock_auth_user):
    """Teste para verificar se usuários comuns não podem acessar a área administrativa."""
    response = client.get("/cartas/admin", allow_redirects=False)
    assert response.status_code == 403  # Forbidden

# Testes para API de cartinhas
def test_api_list_cartas(mock_auth_user, mock_cartas_repo):
    """Teste para verificar se a API retorna a lista de cartinhas."""
    # Configurar o mock para retornar uma lista de cartinhas
    mock_cartas_repo.get_active_cartas.return_value = [
        MagicMock(
            id=1,
            id_carta=101,
            nome="Criança 1",
            sexo="M",
            presente="Brinquedo",
            status="disponível",
            adotante_email=None,
            del_bl=False,
            created_at="2023-01-01T10:00:00",
            updated_at="2023-01-01T10:00:00"
        )
    ]
    
    response = client.get("/cartas/api")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_carta"] == 101
    assert data[0]["nome"] == "Criança 1"
    assert data[0]["presente"] == "Brinquedo"
