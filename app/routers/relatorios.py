from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.repositories import CartasRepository
from app.services.storage_service import StorageService

router = APIRouter(
    prefix="/relatorios",
    tags=["relatorios"],
)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _extract_object_name_from_url(url: str, bucket: str) -> Optional[str]:
    """
    Extrai o object_name de uma URL presignada do MinIO/S3.
    Ex.: https://host/bucket/cartas/10/anexo-abc.pdf?X-Amz-...
         -> cartas/10/anexo-abc.pdf
    """
    if not url:
        return None
    try:
        # Remover querystring
        base = url.split("?", 1)[0]
        marker = f"/{bucket}/"
        idx = base.find(marker)
        if idx == -1:
            return None
        return base[idx + len(marker):]
    except Exception:
        return None


@router.get("/", response_class=HTMLResponse)
async def relatorios_home(
    request: Request,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"]))
):
    # Página agregadora de relatórios
    return templates.TemplateResponse(
        "relatorios/index.html",
        {"request": request}
    )


@router.get("/anexos-orfaos", response_class=HTMLResponse)
async def relatorio_anexos_orfaos(
    request: Request,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    repo = CartasRepository(db)
    storage = StorageService()

    # Conjunto de object_names atualmente referenciados por alguma cartinha ativa (del_bl = False)
    referenced: set[str] = set()
    active_cartas = repo.db.query(repo.model).filter(repo.model.del_bl == False).all()
    for c in active_cartas:
        obj = _extract_object_name_from_url(getattr(c, "urlcarta", None) or "", storage.bucket)
        if obj:
            referenced.add(obj)

    # Listar todos os objetos no bucket sob cartas/
    orfaos: List[Dict[str, Any]] = []
    client = storage._client()
    for obj in client.list_objects(storage.bucket, prefix="cartas/", recursive=True):
        name = getattr(obj, "object_name", "")
        # órfão se não está referenciado por nenhuma cartinha ativa
        if name and (name not in referenced):
            orfaos.append({
                "object_name": name,
                "size": getattr(obj, "size", 0),
                "last_modified": getattr(obj, "last_modified", None),
            })

    return templates.TemplateResponse(
        "relatorios/anexos_orfaos.html",
        {"request": request, "anexos_orfaos": orfaos}
    )


@router.get("/api/object-url")
async def api_get_object_url(
    object_name: str = Query(..., description="Nome do objeto no bucket (ex.: cartas/10/anexo-abc.pdf)"),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"]))
) -> Dict[str, Any]:
    if not object_name or "/" not in object_name:
        raise HTTPException(status_code=400, detail="object_name inválido")
    storage = StorageService()
    url = storage.get_presigned_url(object_name)
    return {"url": url}


@router.post("/api/delete-object")
async def api_delete_object(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"]))
) -> Dict[str, Any]:
    object_name = (payload or {}).get("object_name")
    if not object_name:
        raise HTTPException(status_code=400, detail="object_name é obrigatório")
    storage = StorageService()
    storage.delete_object(object_name)
    return {"success": True}
