from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from pydantic import BaseModel

# Tipo genérico para modelos SQLAlchemy
ModelType = TypeVar("ModelType")
# Tipo genérico para esquemas Pydantic
SchemaType = TypeVar("SchemaType", bound=BaseModel)
# Tipo genérico para esquemas de criação Pydantic
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
# Tipo genérico para esquemas de atualização Pydantic
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, SchemaType, CreateSchemaType, UpdateSchemaType]):
    """
    Repositório base com operações CRUD genéricas.
    
    Esta classe implementa operações básicas de CRUD (Create, Read, Update, Delete)
    que podem ser reutilizadas por repositórios específicos.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Inicializa o repositório base.
        
        Args:
            model: Classe do modelo SQLAlchemy
            db: Sessão do banco de dados
        """
        self.model = model
        self.db = db
    
    def get(self, id: Any) -> Optional[ModelType]:
        """
        Obtém um registro pelo ID.
        
        Args:
            id: ID do registro
            
        Returns:
            Instância do modelo ou None se não encontrado
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Obtém um registro pelo valor de um campo específico.
        
        Args:
            field_name: Nome do campo
            value: Valor do campo
            
        Returns:
            Instância do modelo ou None se não encontrado
        """
        return self.db.query(self.model).filter(getattr(self.model, field_name) == value).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Obtém uma lista de registros com paginação.
        
        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de instâncias do modelo
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Cria um novo registro.
        
        Args:
            obj_in: Dados para criar o registro (esquema Pydantic ou dicionário)
            
        Returns:
            Instância do modelo criado
        """
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> Optional[ModelType]:
        """
        Atualiza um registro existente.
        
        Args:
            id: ID do registro a atualizar
            obj_in: Dados para atualizar (esquema Pydantic ou dicionário)
            
        Returns:
            Instância do modelo atualizado ou None se não encontrado
        """
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: Any) -> bool:
        """
        Remove um registro.
        
        Args:
            id: ID do registro a remover
            
        Returns:
            True se o registro foi removido, False caso contrário
        """
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """
        Conta o número total de registros.
        
        Returns:
            Número total de registros
        """
        return self.db.query(self.model).count()
