"""SQLAlchemy model for the 'cartas_diversas' table."""

from sqlalchemy import (
    Column, Integer, Text, Boolean, DateTime, 
    ForeignKey, CheckConstraint, Index, text
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class CartaDiversa(Base):
    """
    Representa as cartinhas do sistema.
    
    Equivalente à tabela 'cartas_diversas' do sistema original.
    """
    __tablename__ = "cartas_diversas"
    __table_args__ = (
        CheckConstraint("sexo IN ('M', 'F')", name="ck_cartas_sexo"),
        Index("idx_cartas_status", "status"),
        Index("idx_cartas_adotante", "adotante_email"),
        Index("idx_cartas_delbl", "del_bl"),
        Index("idx_cartas_entregue", "entregue_bl"),
        {"schema": "public"}
    )
    
    id = Column(Integer, primary_key=True)
    id_carta = Column(Integer, nullable=False, unique=True)
    nome = Column(Text, nullable=False)
    sexo = Column(Text, nullable=False)
    presente = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    observacao = Column(Text, nullable=True)
    adotante_email = Column(Text, ForeignKey("public.usuarios.email"), nullable=True)
    # URL pública do anexo (PDF/Imagem)
    urlcarta = Column(Text, nullable=True)
    del_bl = Column(Boolean, nullable=False, default=False)
    del_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Campos de entrega
    entregue_bl = Column(Boolean, nullable=False, server_default=text("FALSE"))
    entregue_por_email = Column(Text, ForeignKey("public.usuarios.email"), nullable=True)
    entregue_em = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    adotante = relationship(
        "Usuario",
        back_populates="cartas_adotadas",
        foreign_keys="CartaDiversa.adotante_email",
    )
    
    def __repr__(self):
        return f"<CartaDiversa(id_carta={self.id_carta}, nome='{self.nome}', status='{self.status}')>"
    
    @property
    def is_deleted(self):
        return self.del_bl
    
    @property
    def is_adopted(self):
        return self.adotante_email is not None
    
    @property
    def is_delivered(self):
        # Considera tanto o flag dedicado quanto o status textual, para compatibilidade
        return bool(self.entregue_bl) or (self.status or "").upper() == "ENTREGUE"
