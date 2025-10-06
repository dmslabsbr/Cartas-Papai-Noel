"""SQLAlchemy models for authentication and authorization."""

from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base


class Role(Base):
    """
    Representa os papéis (roles) do sistema para RBAC.
    
    Nova tabela para controle de acesso baseado em papéis.
    """
    __tablename__ = "roles"
    __table_args__ = {"schema": "public"}
    
    id = Column(Integer, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    
    # Relacionamentos
    users = relationship("UserRole", back_populates="role")
    
    def __repr__(self):
        return f"<Role(code='{self.code}', description='{self.description}')>"


class UserRole(Base):
    """
    Associação muitos-para-muitos entre usuários e papéis.
    
    Nova tabela para controle de acesso baseado em papéis.
    """
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True)
    user_email = Column(Text, ForeignKey("public.usuarios.email"), nullable=False)
    role_id = Column(Integer, ForeignKey("public.roles.id"), nullable=False)
    
    # Constraint para garantir que um usuário não tenha o mesmo papel mais de uma vez
    __table_args__ = (
        UniqueConstraint("user_email", "role_id", name="uq_user_role"),
        {"schema": "public"}
    )
    
    # Relacionamentos
    user = relationship("Usuario", back_populates="roles")
    role = relationship("Role", back_populates="users")
    
    def __repr__(self):
        return f"<UserRole(user_email='{self.user_email}', role_id={self.role_id})>"
