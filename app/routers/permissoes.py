from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models.auth import Role

router = APIRouter(
    prefix="/permissoes",
    tags=["permissoes"],
)


@router.get("/roles", response_model=List[Dict[str, Any]])
async def list_roles(
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    roles = db.query(Role).order_by(Role.code.asc()).all()
    return [{"id": r.id, "code": r.code, "description": r.description} for r in roles]


