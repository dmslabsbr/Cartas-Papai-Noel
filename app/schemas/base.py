from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

class BaseSchema(BaseModel):
    """Esquema base para todos os modelos Pydantic."""
    model_config = ConfigDict(from_attributes=True)
