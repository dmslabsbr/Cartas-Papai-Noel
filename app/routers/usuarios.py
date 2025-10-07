from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models.auth import Role
from app.repositories.usuarios_repository import UsuariosRepository

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_usuarios(
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
    ativo: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    repo = UsuariosRepository(db)
    if q:
        users = repo.search_users(q, skip=skip, limit=limit)
    elif ativo is True:
        users = repo.get_active_users(skip=skip, limit=limit)
    else:
        users = db.query(repo.model).offset(skip).limit(limit).all()

    result: List[Dict[str, Any]] = []
    for u in users:
        result.append({
            "email": u.email,
            "display_name": u.display_name,
            "matricula": u.matricula,
            "id_modulo": u.id_modulo,
            "bl_ativo": u.bl_ativo,
            "roles": [ur.role.code for ur in (u.roles or []) if ur.role],
            "created_at": u.created_at,
        })
    return result


@router.get("/roles", response_model=List[Dict[str, Any]])
async def list_roles(
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    roles = db.query(Role).order_by(Role.code.asc()).all()
    return [{"id": r.id, "code": r.code, "description": r.description} for r in roles]


@router.get("/{email}", response_model=Dict[str, Any])
async def get_usuario(
    email: str,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    repo = UsuariosRepository(db)
    u = repo.get_by_email(email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {
        "email": u.email,
        "display_name": u.display_name,
        "matricula": u.matricula,
        "id_modulo": u.id_modulo,
        "bl_ativo": u.bl_ativo,
        "roles": [ur.role.code for ur in (u.roles or []) if ur.role],
        "created_at": u.created_at,
    }


@router.post("/", response_model=Dict[str, Any])
async def create_usuario(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """
    Cria um novo usuário (ADMIN).
    Campos requeridos: email, display_name
    Opcionais: bl_ativo (default True), matricula, id_modulo, roles (lista de codes)
    """
    repo = UsuariosRepository(db)
    email = (payload or {}).get("email")
    display_name = (payload or {}).get("display_name")
    if not email or not display_name:
        raise HTTPException(status_code=400, detail="'email' e 'display_name' são obrigatórios")

    existing = repo.get_by_email(email)
    if existing:
        raise HTTPException(status_code=409, detail="Usuário já existe")

    bl_ativo = bool((payload or {}).get("bl_ativo", True))
    matricula = (payload or {}).get("matricula")
    id_modulo = (payload or {}).get("id_modulo")

    # Criar
    new_user = repo.model(
        email=email,
        display_name=display_name,
        bl_ativo=bl_ativo,
        matricula=matricula,
        id_modulo=id_modulo,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Atribuir roles, se informadas
    roles = (payload or {}).get("roles") or []
    for role_code in roles:
        try:
            repo.add_role_to_user(email, str(role_code))
        except Exception:
            # ignora falha individual de role; poderia logar
            pass

    # Atualizar instância com roles
    new_user = repo.get_by_email(email)
    return {
        "email": new_user.email,
        "display_name": new_user.display_name,
        "matricula": new_user.matricula,
        "id_modulo": new_user.id_modulo,
        "bl_ativo": new_user.bl_ativo,
        "roles": [ur.role.code for ur in (new_user.roles or []) if ur.role],
        "created_at": new_user.created_at,
    }


@router.patch("/{email}", response_model=Dict[str, Any])
async def patch_usuario(
    email: str,
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    repo = UsuariosRepository(db)
    u = repo.get_by_email(email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if "bl_ativo" in payload:
        value = bool(payload["bl_ativo"])
        # Impedir desativar o único ADMIN ativo
        if (u.bl_ativo is True) and (value is False) and repo.is_last_active_admin(email):
            raise HTTPException(status_code=400, detail="Não é permitido desativar o único administrador do sistema")
        u.bl_ativo = value
        db.add(u)
        db.commit()
        db.refresh(u)

    return {
        "email": u.email,
        "display_name": u.display_name,
        "matricula": u.matricula,
        "id_modulo": u.id_modulo,
        "bl_ativo": u.bl_ativo,
        "roles": [ur.role.code for ur in (u.roles or []) if ur.role],
        "created_at": u.created_at,
    }


@router.post("/{email}/roles/{role_code}", response_model=Dict[str, Any])
async def add_role(
    email: str,
    role_code: str,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    repo = UsuariosRepository(db)
    ok = repo.add_role_to_user(email, role_code)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível atribuir a role")
    u = repo.get_by_email(email)
    return {"email": email, "roles": [ur.role.code for ur in (u.roles or []) if ur.role]}


@router.delete("/{email}/roles/{role_code}", response_model=Dict[str, Any])
async def remove_role(
    email: str,
    role_code: str,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db),
):
    repo = UsuariosRepository(db)
    # Impedir remover role ADMIN do único admin ativo
    if role_code.upper() == "ADMIN" and repo.is_last_active_admin(email):
        raise HTTPException(status_code=400, detail="Não é permitido remover a role ADMIN do único administrador do sistema")
    ok = repo.remove_role_from_user(email, role_code)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível remover a role")
    u = repo.get_by_email(email)
    return {"email": email, "roles": [ur.role.code for ur in (u.roles or []) if ur.role]}


