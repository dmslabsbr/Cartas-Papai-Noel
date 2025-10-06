import httpx
import logging
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Usuario, UserRole, Role

logger = logging.getLogger("uvicorn")
SETTINGS = get_settings()

class AuthService:
    """
    Serviço para autenticação e autorização de usuários.
    
    Este serviço integra com a API LDAP externa para autenticação
    e gerencia as permissões dos usuários no sistema.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ldap_api_url = SETTINGS.ldap_api_url
    
    async def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Autentica um usuário usando a API LDAP externa.
        
        Args:
            username: Email ou nome de usuário
            password: Senha do usuário
            
        Returns:
            Tuple contendo status de autenticação (bool) e dados do usuário (dict)
        """
        try:
            # Chamar a API LDAP para autenticação
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ldap_api_url}/auth/check",
                    json={"username": username, "password": password},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    
                    # Adicionar o username como email para identificação do usuário
                    # já que a resposta LDAP não fornece o email
                    user_data["email"] = username
                    
                    # Verificar se o usuário existe no banco de dados
                    db_user = self._get_or_create_user(username, user_data)
                    
                    # Adicionar informações de permissões
                    user_data["roles"] = self._get_user_roles(db_user)
                    
                    return True, user_data
                else:
                    logger.warning(f"Falha na autenticação para {username}: {response.status_code}")
                    return False, None
                    
        except httpx.RequestError as e:
            logger.error(f"Erro ao conectar com API LDAP: {str(e)}")
            raise HTTPException(status_code=503, detail="Serviço de autenticação indisponível")
    
    def _get_or_create_user(self, username: str, user_data: Dict[str, Any]) -> Usuario:
        """
        Obtém ou cria um usuário no banco de dados com base nos dados da API LDAP.
        
        Args:
            username: Nome de usuário usado para autenticação
            user_data: Dados do usuário retornados pela API LDAP
            
        Returns:
            Objeto Usuario do banco de dados
        """
        # Usar o username como email para identificação do usuário
        email = username
        
        # Extrair informações adicionais da resposta LDAP
        info = user_data.get("info", {})
        
        # Verificar se o usuário já existe
        user = self.db.query(Usuario).filter(Usuario.email == email).first()
        
        if not user:
            # Extrair nome de exibição
            display_name = None
            
            # Tentar extrair o nome de exibição da resposta LDAP
            if isinstance(info, dict):
                display_name = (
                    info.get("displayName") or 
                    info.get("name") or 
                    info.get("cn")
                )
            
            # Se não conseguirmos extrair o nome, usar o username
            if not display_name:
                # Remover a parte do domínio se for um email
                if "@" in username:
                    display_name = username.split("@")[0]
                else:
                    display_name = username
            
            # Extrair matrícula se disponível
            matricula = None
            if isinstance(info, dict):
                matricula = info.get("employeeID") or info.get("matricula")
            
            # Criar novo usuário
            user = Usuario(
                email=email,
                display_name=display_name,
                matricula=matricula,
                bl_ativo=True
            )
            self.db.add(user)
            
            # Adicionar role padrão (USER)
            default_role = self.db.query(Role).filter(Role.code == "USER").first()
            if default_role:
                user_role = UserRole(user_email=email, role_id=default_role.id)
                self.db.add(user_role)
            
            self.db.commit()
            logger.info(f"Novo usuário criado: {email}")
        
        return user
    
    def _get_user_roles(self, user: Usuario) -> list:
        """
        Obtém as roles (papéis) do usuário.
        
        Args:
            user: Objeto Usuario
            
        Returns:
            Lista de roles do usuário
        """
        roles = []
        for user_role in user.roles:
            roles.append({
                "id": user_role.role.id,
                "code": user_role.role.code,
                "description": user_role.role.description
            })
        return roles
    
    def has_role(self, user_data: Dict[str, Any], role_code: str) -> bool:
        """
        Verifica se o usuário possui uma determinada role.
        
        Args:
            user_data: Dados do usuário da sessão
            role_code: Código da role a verificar
            
        Returns:
            True se o usuário possui a role, False caso contrário
        """
        roles = user_data.get("roles", [])
        return any(role["code"] == role_code for role in roles)
