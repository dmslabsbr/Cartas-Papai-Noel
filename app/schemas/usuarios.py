from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List

from app.schemas.base import BaseSchema

class RoleSchema(BaseSchema):
    """Esquema para roles (papéis)."""
    id: int
    code: str
    description: Optional[str] = None

class UserRoleSchema(BaseSchema):
    """Esquema para associação entre usuários e roles."""
    user_email: EmailStr
    role: RoleSchema

class UsuarioBase(BaseSchema):
    """Esquema base para usuários."""
    email: EmailStr
    display_name: str
    matricula: Optional[str] = None
    id_modulo: Optional[int] = None
    bl_ativo: bool = True

class UsuarioCreate(UsuarioBase):
    """Esquema para criação de usuários."""
    pass

class UsuarioUpdate(BaseSchema):
    """Esquema para atualização de usuários."""
    display_name: Optional[str] = None
    matricula: Optional[str] = None
    id_modulo: Optional[int] = None
    bl_ativo: Optional[bool] = None

class UsuarioSchema(UsuarioBase):
    """Esquema para representação de usuários."""
    created_at: datetime
    roles: List[RoleSchema] = []

class UsuarioWithModulo(UsuarioSchema):
    """Esquema para usuários com informações do módulo."""
    modulo_nome: Optional[str] = None

class UsuarioLogin(BaseSchema):
    """Esquema para login de usuários."""
    email: EmailStr
    password: str
