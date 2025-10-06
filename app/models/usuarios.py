"""SQLAlchemy model for the 'usuarios' table."""

from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class Usuario(Base):
    """
    Representa os usuários do sistema.
    
    Equivalente à tabela 'usuarios' do sistema original, com adaptações
    para usar email como chave primária e suporte a RBAC.
    """
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "public"}
    
    email = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)
    matricula = Column(Text, nullable=True)
    id_modulo = Column(Integer, ForeignKey("public.modulo.id_modulo"), nullable=True)
    bl_ativo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relacionamentos
    modulo = relationship("Modulo", back_populates="usuarios")
    cartas_adotadas = relationship(
        "CartaDiversa",
        back_populates="adotante",
        foreign_keys="CartaDiversa.adotante_email",
    )
    # Relação de conveniência para entregas registradas por este usuário (admin)
    cartas_entregues = relationship(
        "CartaDiversa",
        foreign_keys="CartaDiversa.entregue_por_email",
        viewonly=True,
    )
    roles = relationship("UserRole", back_populates="user")
    
    def __repr__(self):
        return f"<Usuario(email='{self.email}', display_name='{self.display_name}')>"
    
    @property
    def is_active(self):
        return self.bl_ativo
    
    @property
    def role_codes(self):
        """Lista de códigos de papéis (roles) do usuário."""
        return [ur.role.code for ur in self.roles if ur.role]
    
    def has_role(self, role_code):
        """Verifica se o usuário tem um determinado papel."""
        return role_code in self.role_codes
