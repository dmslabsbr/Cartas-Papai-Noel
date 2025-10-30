"""SQLAlchemy model for the 'grupos' table."""

from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Grupo(Base):
    """
    Representa os grupos de cartinhas (ex.: Correios, Terceirizados).
    """
    __tablename__ = "grupos"
    __table_args__ = {"schema": "public"}

    id_grupo = Column(Integer, primary_key=True)
    ds_grupo = Column(Text, nullable=False)
    cor = Column(Text, nullable=True)  # hexa, ex.: #00FF00

    # Relacionamentos
    cartas = relationship("CartaDiversa", back_populates="grupo", cascade="save-update")

    def __repr__(self):
        return f"<Grupo(id_grupo={self.id_grupo}, ds_grupo='{self.ds_grupo}')>"


