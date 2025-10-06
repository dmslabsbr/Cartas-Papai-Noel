"""SQLAlchemy model for the 'icon_presente' table."""

from sqlalchemy import Column, Integer, Text

from app.db import Base


class IconPresente(Base):
    """
    Representa o mapeamento entre palavras-chave e ícones para presentes.
    
    Equivalente à tabela 'icon_presente' do sistema original.
    """
    __tablename__ = "icon_presente"
    __table_args__ = {"schema": "public"}
    
    id = Column(Integer, primary_key=True)
    keyword = Column(Text, nullable=False)
    icon_code = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<IconPresente(keyword='{self.keyword}', icon_code='{self.icon_code}')>"
