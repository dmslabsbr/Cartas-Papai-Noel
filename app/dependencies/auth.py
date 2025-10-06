from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db import get_db
from app.services import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtém o usuário atual da sessão ou do token JWT.
    
    Esta dependência pode ser usada em rotas protegidas para garantir
    que o usuário esteja autenticado e obter seus dados.
    
    Args:
        request: Objeto Request do FastAPI
        token: Token JWT opcional (para API)
        db: Sessão do banco de dados
        
    Returns:
        Dados do usuário autenticado
        
    Raises:
        HTTPException: Se o usuário não estiver autenticado
    """
    # Verificar se há um usuário na sessão (autenticação web)
    user = request.session.get("user")
    
    # Se não houver usuário na sessão, verificar token JWT (API)
    if not user and token:
        # TODO: Implementar validação de token JWT
        pass
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_roles(required_roles: List[str]):
    """
    Dependência para verificar se o usuário possui as roles necessárias.
    
    Args:
        required_roles: Lista de códigos de roles necessários
        
    Returns:
        Uma dependência que pode ser usada em rotas protegidas
    """
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = [role["code"] for role in user.get("roles", [])]
        
        # Verificar se o usuário possui pelo menos uma das roles necessárias
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente"
            )
        
        return user
    
    return role_checker


def get_optional_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Retorna o usuário autenticado se existir, caso contrário None. Não lança 401.
    """
    user = request.session.get("user")
    # TODO: validar token se necessário
    return user