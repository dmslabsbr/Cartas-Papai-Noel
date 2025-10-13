from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime

from app.models import CartaDiversa, Usuario
from app.repositories.base import BaseRepository
from app.schemas.cartas import CartaCreate, CartaUpdate, CartaSchema

class CartasRepository(BaseRepository[CartaDiversa, CartaSchema, CartaCreate, CartaUpdate]):
    """
    Repositório para operações com cartinhas.
    
    Implementa operações específicas para o modelo CartaDiversa.
    """
    
    def __init__(self, db: Session):
        super().__init__(CartaDiversa, db)
    
    def create_carta(self, payload: CartaCreate) -> CartaDiversa:
        """Cria uma cartinha, gerando id_carta automaticamente se não informado."""
        data = payload.model_dump()
        if not data.get("id_carta"):
            # Gera próximo id_carta: maior existente + 1 (ou 1 se vazio)
            max_id = self.db.query(func.max(self.model.id_carta)).scalar() or 0
            data["id_carta"] = int(max_id) + 1
        carta = self.model(
            id_carta=data["id_carta"],
            nome=data["nome"],
            sexo=data["sexo"],
            presente=data["presente"],
            status=data.get("status", "disponível"),
            observacao=data.get("observacao"),
            del_bl=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(carta)
        self.db.commit()
        self.db.refresh(carta)
        return carta
    
    def get_by_id_carta(self, id_carta: int) -> Optional[CartaDiversa]:
        """
        Obtém uma cartinha pelo id_carta.
        
        Args:
            id_carta: ID único da cartinha
            
        Returns:
            Instância da cartinha ou None se não encontrada
        """
        return self.db.query(self.model).filter(self.model.id_carta == id_carta).first()
    
    def get_active_cartas(self, skip: int = 0, limit: int = 100) -> List[CartaDiversa]:
        """
        Obtém cartinhas ativas (não deletadas).
        
        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de cartinhas ativas
        """
        return self.db.query(self.model).filter(
            self.model.del_bl == False
        ).order_by(desc(self.model.id)).offset(skip).limit(limit).all()
    
    def get_available_cartas(self, skip: int = 0, limit: int = 100) -> List[CartaDiversa]:
        """
        Obtém cartinhas disponíveis para adoção.
        
        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de cartinhas disponíveis
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.del_bl == False,
                self.model.adotante_email == None,
                self.model.status == "disponível",
                self.model.entregue_bl == False,
            )
        ).order_by(desc(self.model.id)).offset(skip).limit(limit).all()
    
    def get_adopted_cartas(self, email: str, skip: int = 0, limit: int = 100) -> List[CartaDiversa]:
        """
        Obtém cartinhas adotadas por um usuário específico.
        
        Args:
            email: Email do adotante
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de cartinhas adotadas pelo usuário
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.del_bl == False,
                self.model.adotante_email == email
            )
        ).order_by(desc(self.model.id)).offset(skip).limit(limit).all()
    
    def adopt_carta(self, id_carta: int, email: str) -> Optional[CartaDiversa]:
        """
        Marca uma cartinha como adotada por um usuário.
        
        Args:
            id_carta: ID da cartinha
            email: Email do adotante
            
        Returns:
            Cartinha atualizada ou None se não encontrada ou indisponível
        """
        carta = self.get_by_id_carta(id_carta)
        if not carta or carta.del_bl:
            return None
        # Regras de negócio: só adota se disponível, sem adotante e não entregue
        if carta.adotante_email is not None:
            return None
        if (carta.status or "").lower() != "disponível":
            return None
        if bool(getattr(carta, "entregue_bl", False)):
            return None
        
        carta.adotante_email = email
        carta.status = "adotada"
        carta.updated_at = datetime.now()
        # Garantir flags de entrega coerentes
        carta.entregue_bl = False
        carta.entregue_por_email = None
        carta.entregue_em = None
        
        self.db.add(carta)
        self.db.commit()
        self.db.refresh(carta)
        return carta
    
    def cancel_adoption(self, id_carta: int, email: str) -> Optional[CartaDiversa]:
        """
        Cancela a adoção de uma cartinha pelo próprio adotante.
        
        Args:
            id_carta: ID da cartinha
            email: Email do adotante (para verificação)
            
        Returns:
            Cartinha atualizada ou None se não encontrada ou não pertencer ao usuário
        """
        carta = self.get_by_id_carta(id_carta)
        if not carta or carta.del_bl:
            return None
        if carta.adotante_email != email:
            return None
        # Se já entregue, não permitir cancelamento por usuário comum (será via admin release)
        if bool(getattr(carta, "entregue_bl", False)):
            return None
        
        carta.adotante_email = None
        carta.status = "disponível"
        carta.updated_at = datetime.now()
        carta.entregue_bl = False
        carta.entregue_por_email = None
        carta.entregue_em = None
        
        self.db.add(carta)
        self.db.commit()
        self.db.refresh(carta)
        return carta
    
    def release_carta(self, id_carta: int, by_user_email: Optional[str], is_admin: bool) -> Optional[CartaDiversa]:
        """
        Libera uma cartinha (remove adoção). Admin sempre pode. Usuário comum somente se for o adotante.
        
        Args:
            id_carta: ID da cartinha
            by_user_email: Email do usuário que está solicitando a liberação (pode ser None para admins de sistema)
            is_admin: Se quem executa tem papel ADMIN
        """
        carta = self.get_by_id_carta(id_carta)
        if not carta or carta.del_bl:
            return None
        if not is_admin and carta.adotante_email != by_user_email:
            return None
        
        carta.adotante_email = None
        carta.status = "disponível"
        carta.updated_at = datetime.now()
        carta.entregue_bl = False
        carta.entregue_por_email = None
        carta.entregue_em = None
        
        self.db.add(carta)
        self.db.commit()
        self.db.refresh(carta)
        return carta
    
    def mark_delivered(self, id_carta: int, admin_email: str) -> Optional[CartaDiversa]:
        """
        Marca uma cartinha como entregue (apenas para administradores). Requer estar adotada.
        
        Args:
            id_carta: ID da cartinha
            admin_email: Email do administrador que está registrando a entrega
        """
        carta = self.get_by_id_carta(id_carta)
        if not carta or carta.del_bl:
            return None
        # Só permite se estiver adotada
        if (carta.status or "").lower() != "adotada" or carta.adotante_email is None:
            return None
        
        carta.entregue_bl = True
        carta.entregue_por_email = admin_email
        carta.entregue_em = datetime.now()
        # Opcional: evoluir status para "entregue"
        carta.status = "entregue"
        carta.updated_at = datetime.now()
        
        self.db.add(carta)
        self.db.commit()
        self.db.refresh(carta)
        return carta

    def unmark_delivered(self, id_carta: int) -> Optional[CartaDiversa]:
        """
        Reverte a marcação de entrega (apenas ADMIN via rota). Mantém a adoção e volta status para 'adotada'.
        """
        carta = self.get_by_id_carta(id_carta)
        if not carta or carta.del_bl:
            return None
        # Só faz sentido se estava marcada como entregue ou status contém entregue
        was_delivered = bool(getattr(carta, "entregue_bl", False)) or (str(carta.status or "").lower().find("entregue") != -1)
        if not was_delivered:
            return None
        # Requer que ainda exista adotante; caso não exista, volta para disponível
        if carta.adotante_email:
            carta.status = "adotada"
        else:
            carta.status = "disponível"
        carta.entregue_bl = False
        carta.entregue_por_email = None
        carta.entregue_em = None
        carta.updated_at = datetime.now()
        self.db.add(carta)
        self.db.commit()
        self.db.refresh(carta)
        return carta
    
    def search_cartas(self, query: str, skip: int = 0, limit: int = 100) -> List[CartaDiversa]:
        """
        Pesquisa cartinhas por texto em vários campos.
        
        Args:
            query: Texto para pesquisar
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de cartinhas que correspondem à pesquisa
        """
        search = f"%{query}%"
        return self.db.query(self.model).filter(
            and_(
                self.model.del_bl == False,
                or_(
                    self.model.nome.ilike(search),
                    self.model.presente.ilike(search),
                    self.model.observacao.ilike(search)
                )
            )
        ).order_by(desc(self.model.id)).offset(skip).limit(limit).all()

    def update(self, id: Any, obj_in: Union[CartaUpdate, Dict[str, Any]]) -> Optional[CartaDiversa]:
        """
        Atualiza uma cartinha com sincronização de flags de entrega baseada no status.
        - Se status contém "entregue": define entregue_bl=True e preenche entregue_em se ausente.
        - Caso contrário: zera entregue_bl e campos relacionados.
        """
        db_obj = self.get(id)
        if not db_obj:
            return None
        # Extrai dados a atualizar
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        # Aplica campos simples
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Sincroniza flags de entrega quando status é informado
        if "status" in obj_data:
            status_value = str(obj_data.get("status") or db_obj.status or "")
            status_lower = status_value.lower()
            is_delivered = "entregue" in status_lower
            if is_delivered:
                db_obj.entregue_bl = True
                if not getattr(db_obj, "entregue_em", None):
                    db_obj.entregue_em = datetime.now()
            else:
                db_obj.entregue_bl = False
                db_obj.entregue_por_email = None
                db_obj.entregue_em = None
        
        db_obj.updated_at = datetime.now()
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def soft_delete(self, id_carta: int) -> bool:
        """
        Marca uma cartinha como deletada logicamente (soft delete).
        
        Args:
            id_carta: ID da cartinha a ser deletada
            
        Returns:
            True se a cartinha foi deletada, False se não encontrada
        """
        carta = self.get_by_id_carta(id_carta)
        if not carta or carta.del_bl:
            return False
        
        carta.del_bl = True
        carta.del_time = datetime.now()
        carta.updated_at = datetime.now()
        
        self.db.add(carta)
        self.db.commit()
        return True
