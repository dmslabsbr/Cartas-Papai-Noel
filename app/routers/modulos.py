from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.repositories.modulos_repository import ModulosRepository

router = APIRouter(
    prefix="/modulos",
    tags=["modulos"],
)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_modulos(
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    repo = ModulosRepository(db)
    ms = repo.list(skip=skip, limit=limit)
    return [{"id_modulo": m.id_modulo, "nome": m.nome} for m in ms]


@router.post("/", response_model=Dict[str, Any])
async def create_modulo(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    nome = (payload or {}).get("nome")
    if not nome:
        raise HTTPException(status_code=400, detail="'nome' é obrigatório")
    repo = ModulosRepository(db)
    m = repo.create(nome)
    return {"id_modulo": m.id_modulo, "nome": m.nome}


@router.patch("/{id_modulo}", response_model=Dict[str, Any])
async def update_modulo(
    id_modulo: int,
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    nome = (payload or {}).get("nome")
    if not nome:
        raise HTTPException(status_code=400, detail="'nome' é obrigatório")
    repo = ModulosRepository(db)
    m = repo.update(id_modulo, nome)
    if not m:
        raise HTTPException(status_code=404, detail="Módulo não encontrado")
    return {"id_modulo": m.id_modulo, "nome": m.nome}


@router.delete("/{id_modulo}", response_model=Dict[str, Any])
async def delete_modulo(
    id_modulo: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    repo = ModulosRepository(db)
    ok = repo.delete(id_modulo)
    if not ok:
        raise HTTPException(status_code=404, detail="Módulo não encontrado")
    return {"success": True}


