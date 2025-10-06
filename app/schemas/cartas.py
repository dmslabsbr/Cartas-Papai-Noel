from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.schemas.base import BaseSchema

class StatusEnum(str, Enum):
    """Enum para status de cartinhas."""
    DISPONIVEL = "disponível"
    ADOTADA = "adotada"
    ENTREGUE = "entregue"
    CANCELADA = "cancelada"

class SexoEnum(str, Enum):
    """Enum para sexo das crianças."""
    MASCULINO = "M"
    FEMININO = "F"

class CartaBase(BaseSchema):
    """Esquema base para cartinhas."""
    nome: str
    sexo: SexoEnum
    presente: str
    status: StatusEnum = StatusEnum.DISPONIVEL
    observacao: Optional[str] = None

class CartaCreate(CartaBase):
    """Esquema para criação de cartinhas."""
    id_carta: Optional[int] = None

class CartaUpdate(BaseSchema):
    """Esquema para atualização de cartinhas."""
    nome: Optional[str] = None
    sexo: Optional[SexoEnum] = None
    presente: Optional[str] = None
    status: Optional[StatusEnum] = None
    observacao: Optional[str] = None
    adotante_email: Optional[EmailStr] = None
    # Permite limpar/atualizar a referência do anexo sem apagar o arquivo
    urlcarta: Optional[str] = None

class CartaSchema(CartaBase):
    """Esquema para representação de cartinhas."""
    id: int
    id_carta: int
    adotante_email: Optional[EmailStr] = None
    del_bl: bool = False
    del_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    urlcarta: Optional[str] = None

class CartaAdopt(BaseSchema):
    """Esquema para adoção de cartinhas."""
    id_carta: int
