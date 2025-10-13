from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.repositories import CartasRepository
from app.services.storage_service import StorageService
from app.version import read_version
from app.utils.template_helpers import first_name_from_user

router = APIRouter(
    prefix="/relatorios",
    tags=["relatorios"],
)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
# Expor versão global
templates.env.globals["app_version"] = read_version()
templates.env.globals["first_name_from_user"] = first_name_from_user


def _extract_object_name_from_url(url: str, bucket: str) -> Optional[str]:
    """
    Extrai o object_name de uma URL presignada do MinIO/S3.
    Ex.: https://host/bucket/cartas/10/anexo-abc.pdf?X-Amz-...
         -> cartas/10/anexo-abc.pdf
    """
    if not url:
        return None
    try:
        # Se já for um object_name salvo diretamente
        if url.startswith("cartas/"):
            return url
        # Remover querystring
        base = url.split("?", 1)[0]
        marker = f"/{bucket}/"
        idx = base.find(marker)
        if idx != -1:
            return base[idx + len(marker):]
        # Fallback: encontrar prefixo cartas/ em qualquer URL
        if "cartas/" in base:
            return base.split("cartas/", 1)[1].strip("/")
        return None
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
        {"request": request, "user": user}
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

    # Listar todos os objetos no bucket sob cartas/, mas agrupar para mostrar principal e miniatura relacionada
    orfaos: List[Dict[str, Any]] = []
    client = storage._client()
    for obj in client.list_objects(storage.bucket, prefix="cartas/", recursive=True):
        name = getattr(obj, "object_name", "")
        # órfão se não está referenciado por nenhuma cartinha ativa
        if not name or (name in referenced):
            continue
        # Evitar listar a miniatura como linha própria; preferir listar apenas o principal
        if name.endswith("_thumb.jpg"):
            continue
        thumb_name = name.rsplit('.', 1)[0] + "_thumb.jpg"
        has_thumb = False
        try:
            client.stat_object(storage.bucket, thumb_name)
            has_thumb = True
        except Exception:
            has_thumb = False
        orfaos.append({
            "object_name": name,
            "thumb_object": thumb_name if has_thumb else None,
            "size": getattr(obj, "size", 0),
            "last_modified": getattr(obj, "last_modified", None),
        })

    return templates.TemplateResponse(
        "relatorios/anexos_orfaos.html",
        {"request": request, "user": user, "anexos_orfaos": orfaos}
    )


@router.get("/anexos-referenciados", response_class=HTMLResponse)
async def relatorio_anexos_referenciados(
    request: Request,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Lista anexos que possuem correspondência a cartinhas no banco de dados (não deletadas logicamente).
    """
    repo = CartasRepository(db)
    storage = StorageService()

    # Coletar todos os object_names referenciados por cartinhas ativas
    referenced: set[str] = set()
    active_cartas = repo.db.query(repo.model).filter(repo.model.del_bl == False).all()
    for c in active_cartas:
        obj = _extract_object_name_from_url(getattr(c, "urlcarta", None) or "", storage.bucket)
        if obj:
            referenced.add(obj)

    # Mapear thumbs informadas no banco (urlcarta_pq)
    thumb_by_main: dict[str, str] = {}
    for c in active_cartas:
        main_obj = _extract_object_name_from_url(getattr(c, "urlcarta", None) or "", storage.bucket)
        thumb_obj = _extract_object_name_from_url(getattr(c, "urlcarta_pq", None) or "", storage.bucket)
        if main_obj and thumb_obj:
            thumb_by_main[main_obj] = thumb_obj

    # Para obter detalhes (tamanho/data), varrer o bucket e incluir os que estão referenciados
    referenciados: List[Dict[str, Any]] = []
    client = storage._client()
    for obj in client.list_objects(storage.bucket, prefix="cartas/", recursive=True):
        name = getattr(obj, "object_name", "")
        if name and (name in referenced):
            # Determinar thumb preferencial: banco, senão por convenção
            thumb_name = thumb_by_main.get(name) or (name.rsplit('.', 1)[0] + "_thumb.jpg")
            has_thumb = False
            try:
                client.stat_object(storage.bucket, thumb_name)
                has_thumb = True
            except Exception:
                has_thumb = False
            referenciados.append({
                "object_name": name,
                "thumb_object": thumb_name if has_thumb else None,
                "size": getattr(obj, "size", 0),
                "last_modified": getattr(obj, "last_modified", None),
            })

    return templates.TemplateResponse(
        "relatorios/anexos_referenciados.html",
        {"request": request, "user": user, "anexos_referenciados": referenciados}
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
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    object_name = (payload or {}).get("object_name")
    if not object_name:
        raise HTTPException(status_code=400, detail="object_name é obrigatório")
    storage = StorageService()
    
    # Extrair id_carta do object_name para limpar campos da carta deletada
    def _extract_id_carta_from_object(name: str) -> Optional[int]:
        try:
            parts = (name or "").split('/')
            # esperado: cartas/{id_carta}/arquivo
            if len(parts) >= 3 and parts[0] == 'cartas':
                return int(parts[1])
        except Exception:
            return None
        return None
    
    id_carta = _extract_id_carta_from_object(object_name)
    
    # Apagar objeto principal
    storage.delete_object(object_name)
    
    # Se for principal, tentar apagar miniatura correspondente
    try:
        thumb_name = object_name.rsplit('.', 1)[0] + "_thumb.jpg"
        storage.delete_object(thumb_name)
    except Exception:
        # ignorar se não existir
        pass
    
    # Se conseguimos extrair id_carta, limpar campos urlcarta e urlcarta_pq das cartas deletadas
    if id_carta is not None:
        repo = CartasRepository(db)
        # Buscar cartas deletadas (del_bl=True) com esse id_carta
        cartas_deletadas = repo.db.query(repo.model).filter(
            repo.model.id_carta == id_carta,
            repo.model.del_bl == True
        ).all()
        
        for carta in cartas_deletadas:
            # Limpar campos de anexo
            carta.urlcarta = None
            carta.urlcarta_pq = None
            carta.updated_at = datetime.now()
            db.add(carta)
        
        if cartas_deletadas:
            db.commit()
    
    return {"success": True}
