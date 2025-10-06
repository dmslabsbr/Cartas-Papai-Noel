"""SQLAlchemy model for the 'modulo' table."""

from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Modulo(Base):
    """
    Representa os módulos/permissões do sistema.
    
    Equivalente à tabela 'modulo' do sistema original.
    """
    __tablename__ = "modulo"
    __table_args__ = {"schema": "public"}
    
    id_modulo = Column(Integer, primary_key=True)
    nome = Column(Text, nullable=False, unique=True)
    
    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="modulo")
    
    def __repr__(self):
        return f"<Modulo(id_modulo={self.id_modulo}, nome='{self.nome}')>"
