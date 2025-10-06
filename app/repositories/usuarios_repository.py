from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, text
from datetime import datetime

from app.models import Usuario, UserRole, Role
from app.repositories.base import BaseRepository
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioSchema

class UsuariosRepository(BaseRepository[Usuario, UsuarioSchema, UsuarioCreate, UsuarioUpdate]):
    """
    Repositório para operações com usuários.
    
    Implementa operações específicas para o modelo Usuario.
    """
    
    def __init__(self, db: Session):
        super().__init__(Usuario, db)
    
    def get_by_email(self, email: str) -> Optional[Usuario]:
        """
        Obtém um usuário pelo email.
        
        Args:
            email: Email do usuário
            
        Returns:
            Instância do usuário ou None se não encontrado
        """
        return self.db.query(self.model).filter(self.model.email == email).first()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Obtém usuários ativos.
        
        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuários ativos
        """
        return self.db.query(self.model).filter(
            self.model.bl_ativo == True
        ).offset(skip).limit(limit).all()
    
    def get_users_by_modulo(self, id_modulo: int, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Obtém usuários por módulo.
        
        Args:
            id_modulo: ID do módulo
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuários do módulo especificado
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.bl_ativo == True,
                self.model.id_modulo == id_modulo
            )
        ).offset(skip).limit(limit).all()
    
    def get_users_by_role(self, role_code: str, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Obtém usuários por role (papel).
        
        Args:
            role_code: Código da role
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuários com a role especificada
        """
        return self.db.query(self.model).join(
            UserRole, self.model.email == UserRole.user_email
        ).join(
            Role, UserRole.role_id == Role.id
        ).filter(
            and_(
                self.model.bl_ativo == True,
                Role.code == role_code
            )
        ).offset(skip).limit(limit).all()
    
    def add_role_to_user(self, email: str, role_code: str) -> bool:
        """
        Adiciona uma role a um usuário.
        
        Args:
            email: Email do usuário
            role_code: Código da role
            
        Returns:
            True se a role foi adicionada, False caso contrário
        """
        user = self.get_by_email(email)
        if not user:
            return False
        
        role = self.db.query(Role).filter(Role.code == role_code).first()
        if not role:
            return False
        
        # Verificar se o usuário já possui a role
        existing_role = self.db.query(UserRole).filter(
            and_(
                UserRole.user_email == email,
                UserRole.role_id == role.id
            )
        ).first()
        
        if existing_role:
            return True  # Já possui a role
        
        # Adicionar a role ao usuário
        user_role = UserRole(user_email=email, role_id=role.id)
        self.db.add(user_role)
        self.db.commit()
        return True
    
    def remove_role_from_user(self, email: str, role_code: str) -> bool:
        """
        Remove uma role de um usuário.
        
        Args:
            email: Email do usuário
            role_code: Código da role
            
        Returns:
            True se a role foi removida, False caso contrário
        """
        user = self.get_by_email(email)
        if not user:
            return False
        
        role = self.db.query(Role).filter(Role.code == role_code).first()
        if not role:
            return False
        
        # Remover a role do usuário
        user_role = self.db.query(UserRole).filter(
            and_(
                UserRole.user_email == email,
                UserRole.role_id == role.id
            )
        ).first()
        
        if not user_role:
            return False  # Não possui a role
        
        self.db.delete(user_role)
        self.db.commit()
        return True
    
    def deactivate_user(self, email: str) -> bool:
        """
        Desativa um usuário.
        
        Args:
            email: Email do usuário
            
        Returns:
            True se o usuário foi desativado, False caso contrário
        """
        user = self.get_by_email(email)
        if not user:
            return False
        
        user.bl_ativo = False
        self.db.add(user)
        self.db.commit()
        return True
    
    def activate_user(self, email: str) -> bool:
        """
        Ativa um usuário.
        
        Args:
            email: Email do usuário
            
        Returns:
            True se o usuário foi ativado, False caso contrário
        """
        user = self.get_by_email(email)
        if not user:
            return False
        
        user.bl_ativo = True
        self.db.add(user)
        self.db.commit()
        return True
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Pesquisa usuários por texto em vários campos.
        
        Args:
            query: Texto para pesquisar
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuários que correspondem à pesquisa
        """
        search = f"%{query}%"
        return self.db.query(self.model).filter(
            or_(
                self.model.email.ilike(search),
                self.model.display_name.ilike(search),
                self.model.matricula.ilike(search)
            )
        ).offset(skip).limit(limit).all()
