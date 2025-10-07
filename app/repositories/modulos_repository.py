from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.modulo import Modulo


class ModulosRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = Modulo

    def list(self, skip: int = 0, limit: int = 100) -> List[Modulo]:
        return self.db.query(self.model).order_by(self.model.id_modulo.asc()).offset(skip).limit(limit).all()

    def get(self, id_modulo: int) -> Optional[Modulo]:
        return self.db.get(self.model, id_modulo)

    def create(self, nome: str) -> Modulo:
        m = self.model(nome=nome)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def update(self, id_modulo: int, nome: str) -> Optional[Modulo]:
        m = self.get(id_modulo)
        if not m:
            return None
        m.nome = nome
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def delete(self, id_modulo: int) -> bool:
        m = self.get(id_modulo)
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True


