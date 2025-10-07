from fastapi import APIRouter, Depends, HTTPException, Request, Query, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from app.version import read_version
from app.utils.template_helpers import first_name_from_user  # helper nome

from app.db import get_db
from app.dependencies import get_current_user, require_roles
from app.dependencies import get_optional_user
from app.repositories import CartasRepository
from app.repositories.icon_presente_repository import IconPresenteRepository
from app.schemas import CartaSchema, CartaCreate, CartaUpdate, CartaAdopt
from app.services.storage_service import StorageService
import io

logger = logging.getLogger("uvicorn")

# Configurar o router
router = APIRouter(
    prefix="/cartas",
    tags=["cartas"],
    responses={404: {"description": "Not found"}},
)

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
# Expor versão do app globalmente para os templates deste router
templates.env.globals["app_version"] = read_version()
templates.env.globals["first_name_from_user"] = first_name_from_user

# Rotas para interface web

@router.get("/", response_class=HTMLResponse)
async def list_cartas(
    request: Request,
    q: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=5, le=100),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Lista de cartinhas com paginação e filtros. Público: sem login.
    """
    repository = CartasRepository(db)
    icon_repo = IconPresenteRepository(db)
    skip = (page - 1) * per_page
    
    # Filtrar por status se especificado
    if status == "disponivel":
        cartas = repository.get_available_cartas(skip=skip, limit=per_page)
        total = repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            repository.model.adotante_email == None,
            repository.model.status == "disponível"
        ).count()
    elif status == "adotadas":
        cartas = repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            repository.model.adotante_email != None,
            repository.model.status == "adotada"
        ).offset(skip).limit(per_page).all()
        total = repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            repository.model.adotante_email != None,
            repository.model.status == "adotada"
        ).count()
    elif status == "entregues":
        from sqlalchemy import or_
        cartas = repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            or_(
                repository.model.entregue_bl == True,
                repository.model.status.ilike("%entregue%"),
            ),
        ).order_by(repository.model.id.desc()).offset(skip).limit(per_page).all()
        total = repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            or_(
                repository.model.entregue_bl == True,
                repository.model.status.ilike("%entregue%"),
            ),
        ).count()
    elif status == "minhas" and user:
        cartas = repository.get_adopted_cartas(user["email"], skip=skip, limit=per_page)
        total = repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            repository.model.adotante_email == user["email"]
        ).count()
    elif q:  # Pesquisa por texto
        cartas = repository.search_cartas(q, skip=skip, limit=per_page)
        total = len(cartas)  # Simplificado para este exemplo
    else:
        cartas = repository.get_active_cartas(skip=skip, limit=per_page)
        total = repository.db.query(repository.model).filter(
            repository.model.del_bl == False
        ).count()
    
    # Calcular informações de paginação
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    # Mapear ícones sugeridos por id_carta para lookup simples no template
    icons_by_id: dict[int, list[str]] = {}
    for c in cartas:
        icons_by_id[c.id_carta] = icon_repo.icons_for_present_text(getattr(c, 'presente', '') or '')

    return templates.TemplateResponse(
        "cartas/list.html",
        {
            "request": request,
            "cartas": cartas,  # manter compatibilidade existente
            "icons_by_id": icons_by_id,
            "user": user or {},
            "q": q,
            "status_filter": status,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        }
    )

@router.get("/admin", response_class=HTMLResponse)
async def admin_cartas(
    request: Request,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=5, le=100),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Administração de cartinhas (apenas para administradores).
    """
    repository = CartasRepository(db)
    skip = (page - 1) * per_page
    
    if q:
        cartas = repository.search_cartas(q, skip=skip, limit=per_page)
        total = len(cartas)  # Simplificado para este exemplo
    else:
        # Incluir também as cartinhas deletadas logicamente
        cartas = repository.db.query(repository.model).order_by(
            repository.model.id.desc()
        ).offset(skip).limit(per_page).all()
        total = repository.db.query(repository.model).count()
    
    # Calcular informações de paginação
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    return templates.TemplateResponse(
        "cartas/admin.html",
        {
            "request": request,
            "cartas": cartas,
            "user": user,
            "q": q,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        }
    )


@router.get("/admin/miniaturas", response_class=HTMLResponse)
async def admin_miniaturas_page(
    request: Request,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Página para gerar miniaturas das imagens das cartinhas (ADMIN)."""
    repo = CartasRepository(db)
    storage = StorageService()
    # Cartas com URL
    cartas = repo.db.query(repo.model).filter(
        repo.model.del_bl == False,
        repo.model.urlcarta != None
    ).order_by(repo.model.id.desc()).all()

    # Tentar extrair object_name e checar se miniatura já existe (suffix _thumb.jpg)
    def extract_object(url_or_name: str) -> str:
        """Extrai o object_name aceitando tanto URL completa quanto object_name puro.
        Exemplos aceitos:
        - 'cartas/10/anexo-xxx.png' (já é object_name)
        - 'http://host/bucket/cartas/10/anexo-xxx.png?...'
        - '.../cartas/10/anexo-xxx.png' (qualquer URL contendo prefixo 'cartas/')
        """
        if not url_or_name:
            return ''
        # Se já parecer um object_name
        if url_or_name.startswith('cartas/'):
            return url_or_name
        base = url_or_name.split('?', 1)[0]
        parts = base.split('/')
        # Caso URL contenha explicitamente o bucket
        if storage.bucket in parts:
            idx = parts.index(storage.bucket)
            return '/'.join(parts[idx+1:])
        # Fallback: procurar prefixo conhecido
        if 'cartas/' in base:
            return base.split('cartas/', 1)[1].strip('/')
        return ''

    items = []
    client = storage._client()
    for c in cartas:
        obj = extract_object(getattr(c, 'urlcarta', '') or '')
        if not obj:
            continue
        thumb_name = obj.rsplit('.', 1)[0] + "_thumb.jpg"
        has_thumb = False
        # checar existência
        try:
            client.stat_object(storage.bucket, thumb_name)
            has_thumb = True
        except Exception:
            has_thumb = False
        items.append({
            "id_carta": c.id_carta,
            "object_name": obj,
            "thumb_name": thumb_name,
            "has_thumb": has_thumb,
        })

    return templates.TemplateResponse(
        "cartas/miniaturas.html",
        {"request": request, "user": user, "items": items}
    )


@router.post("/admin/miniaturas/generate", response_model=Dict[str, Any])
async def admin_generate_thumbnail(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"]))
):
    """Gera miniatura 200x300 para o objeto informado e grava no mesmo prefixo."""
    storage = StorageService()
    client = storage._client()

    object_name = (payload or {}).get("object_name")
    if not object_name:
        raise HTTPException(status_code=400, detail="object_name é obrigatório")

    # Pré-verificação simples por extensão
    if object_name.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF não suportado para miniatura no momento")

    # Baixar objeto original em memória
    response = None
    try:
        response = client.get_object(storage.bucket, object_name)
        data = response.read()
    finally:
        if response is not None:
            try:
                response.close()
                response.release_conn()
            except Exception:
                pass

    # Abrir como imagem (se PDF, tentar primeira página no futuro; por ora, erro)
    try:
        try:
            from PIL import Image  # lazy import
        except ImportError:
            raise HTTPException(status_code=500, detail="Dependência 'Pillow' não instalada. Execute: pip install Pillow")
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert('RGB')
            im.thumbnail((200, 300))
            out = io.BytesIO()
            im.save(out, format='JPEG', quality=85)
            out.seek(0)
    except Exception:
        raise HTTPException(status_code=400, detail="Arquivo não é uma imagem suportada para miniatura")

    thumb_name = object_name.rsplit('.', 1)[0] + "_thumb.jpg"
    client.put_object(
        storage.bucket,
        thumb_name,
        data=out,
        length=out.getbuffer().nbytes,
        content_type='image/jpeg'
    )
    url = storage.get_presigned_url(thumb_name)
    return {"thumb_object": thumb_name, "url": url}

@router.get("/{id_carta}", response_class=HTMLResponse)
async def view_carta(
    request: Request,
    id_carta: int,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Visualiza detalhes de uma cartinha. Público: sem login.
    """
    repository = CartasRepository(db)
    carta = repository.get_by_id_carta(id_carta)
    
    if not carta or carta.del_bl:
        return RedirectResponse(url="/cartas?error=not_found", status_code=status.HTTP_302_FOUND)
    
    # Verificar se o usuário é o adotante ou um administrador (se existir usuário)
    roles = (user or {}).get("roles", [])
    is_admin = any(role["code"] == "ADMIN" for role in roles)
    is_owner = bool(user) and carta.adotante_email == user.get("email")
    can_edit = is_admin or is_owner
    
    return templates.TemplateResponse(
        "cartas/view.html",
        {
            "request": request,
            "carta": carta,
            "user": user or {},
            "can_edit": can_edit,
            "is_admin": is_admin,
            "is_owner": is_owner
        }
    )

@router.post("/adopt/{id_carta}")
async def adopt_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adota uma cartinha.
    """
    repository = CartasRepository(db)
    carta = repository.adopt_carta(id_carta, user["email"])
    
    if not carta:
        return RedirectResponse(url="/cartas?error=adopt_failed", status_code=status.HTTP_302_FOUND)
    
    return RedirectResponse(url=f"/cartas/{id_carta}", status_code=status.HTTP_302_FOUND)

@router.post("/cancel/{id_carta}")
async def cancel_adoption(
    id_carta: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancela a adoção de uma cartinha.
    """
    repository = CartasRepository(db)
    carta = repository.cancel_adoption(id_carta, user["email"])
    
    if not carta:
        return RedirectResponse(url="/cartas?error=cancel_failed", status_code=status.HTTP_302_FOUND)
    
    return RedirectResponse(url="/cartas?status=minhas", status_code=status.HTTP_302_FOUND)

# Rotas de liberação e entrega

@router.post("/release/{id_carta}")
async def release_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Libera uma cartinha: ADMIN sempre pode; usuário comum somente se for o adotante.
    """
    repository = CartasRepository(db)
    is_admin = any(role["code"] == "ADMIN" for role in user.get("roles", []))
    carta = repository.release_carta(id_carta, by_user_email=user.get("email"), is_admin=is_admin)
    if not carta:
        return RedirectResponse(url="/cartas?error=release_failed", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url=f"/cartas/{id_carta}", status_code=status.HTTP_302_FOUND)

@router.post("/deliver/{id_carta}")
async def deliver_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Marca a cartinha como entregue (somente ADMIN).
    """
    repository = CartasRepository(db)
    carta = repository.mark_delivered(id_carta, admin_email=user.get("email"))
    if not carta:
        return RedirectResponse(url="/cartas?error=deliver_failed", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url=f"/cartas/{id_carta}", status_code=status.HTTP_302_FOUND)

@router.post("/undeliver/{id_carta}")
async def undeliver_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Desmarca a entrega de uma cartinha (somente ADMIN). Mantém a adoção e volta status para 'adotada'.
    """
    repository = CartasRepository(db)
    carta = repository.unmark_delivered(id_carta)
    if not carta:
        return RedirectResponse(url="/cartas?error=undeliver_failed", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url=f"/cartas/{id_carta}", status_code=status.HTTP_302_FOUND)

# Upload/Download de anexos (ADMIN)

@router.post("/api/admin/create", response_model=CartaSchema)
async def api_create_carta(
    carta: CartaCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    API para criar uma nova cartinha (apenas para administradores).
    """
    repository = CartasRepository(db)
    return repository.create_carta(carta)

@router.put("/api/admin/{id_carta}", response_model=CartaSchema)
async def api_update_carta(
    id_carta: int,
    carta: CartaUpdate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    API para atualizar uma cartinha (apenas para administradores).
    """
    repository = CartasRepository(db)
    db_carta = repository.get_by_id_carta(id_carta)
    
    if not db_carta:
        raise HTTPException(status_code=404, detail="Cartinha não encontrada")
    
    updated_carta = repository.update(db_carta.id, carta)
    if not updated_carta:
        raise HTTPException(status_code=400, detail="Não foi possível atualizar a cartinha")
    
    return updated_carta

@router.delete("/api/admin/{id_carta}", response_model=dict)
async def api_delete_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    API para remover uma cartinha (apenas para administradores).
    """
    repository = CartasRepository(db)
    success = repository.soft_delete(id_carta)
    
    if not success:
        raise HTTPException(status_code=404, detail="Cartinha não encontrada")
    
    return {"success": True, "message": "Cartinha removida com sucesso"}

@router.post("/api/admin/{id_carta}/anexo", response_model=dict)
async def api_upload_anexo(
    id_carta: int,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Upload de anexo (PDF/imagem) para a cartinha (somente ADMIN).
    """
    logger.info("[Upload] Recebendo anexo id_carta=%s filename=%s content_type=%s", id_carta, getattr(file, "filename", None), getattr(file, "content_type", None))
    # Validar existência da carta
    repo = CartasRepository(db)
    carta = repo.get_by_id_carta(id_carta)
    if not carta or carta.del_bl:
        logger.warning("[Upload] Cartinha não encontrada ou deletada id_carta=%s", id_carta)
        raise HTTPException(status_code=404, detail="Cartinha não encontrada")

    storage = StorageService()
    try:
        object_name = storage.upload_carta_anexo(id_carta, file)
        # Persistir o identificador estável do objeto (object_name) em vez de URL presignada expirada
        carta.urlcarta = object_name
        carta.updated_at = carta.updated_at or None  # garantir mudança
        db.add(carta)
        db.commit()
        db.refresh(carta)
        logger.info("[Upload] Sucesso id_carta=%s object=%s", id_carta, object_name)
        # Retornar também uma URL presignada para uso imediato no cliente
        url = storage.get_presigned_url(object_name)
        return {"object_name": object_name, "url": url}
    except HTTPException:
        # Já logado dentro do serviço; propagar
        raise
    except Exception as exc:
        logger.exception("[Upload] Erro inesperado no upload id_carta=%s", id_carta)
        raise HTTPException(status_code=500, detail="Falha inesperada ao enviar anexo") from exc

@router.get("/api/{id_carta}/anexo", response_model=dict)
async def api_get_anexo(
    id_carta: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
):
    """
    Retorna uma URL assinada temporária para o último anexo da carta (ADMIN por enquanto).
    """
    storage = StorageService()
    from sqlalchemy.orm import Session
    from app.db import get_db
    from fastapi import Depends as _Depends
    # Obter carta para ler campo urlcarta (pode conter object_name ou URL antiga)
    async def _get_urlcarta(db: Session = _Depends(get_db)):
        repo = CartasRepository(db)
        c = repo.get_by_id_carta(id_carta)
        return getattr(c, 'urlcarta', None) if c else None
    urlcarta = await _get_urlcarta()  # type: ignore

    def _extract_object(url_or_name: str) -> str:
        if not url_or_name:
            return ''
        # Se já parecer um object_name (começa com 'cartas/')
        if url_or_name.startswith('cartas/'):
            return url_or_name
        base = url_or_name.split('?', 1)[0]
        parts = base.split('/')
        if storage.bucket in parts:
            idx = parts.index(storage.bucket)
            return '/'.join(parts[idx+1:])
        # fallback: tentar localizar prefixo 'cartas/' em qualquer posição
        if 'cartas/' in base:
            return base.split('cartas/', 1)[1].strip('/')
        return ''

    object_name = _extract_object(urlcarta or '')
    if not object_name:
        # fallback para utilitário do storage, se existir
        try:
            url = storage.get_latest_carta_anexo_url(id_carta)
            if url:
                return {"url": url}
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Anexo não encontrado")

    url = storage.get_presigned_url(object_name)
    return {"url": url}


@router.get("/anexo/{id_carta}")
async def public_redirect_to_anexo(
    id_carta: int,
    db: Session = Depends(get_db),
):
    """
    Redireciona para uma URL assinada temporária do anexo da cartinha.
    Aberto (mesma política anterior de exibir anexo publicamente).
    """
    storage = StorageService()
    # Buscar a carta e extrair o object_name do campo urlcarta (suporta legacy URL)
    repo = CartasRepository(db)
    c = repo.get_by_id_carta(id_carta)
    if not c or not getattr(c, 'urlcarta', None):
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    urlcarta = c.urlcarta or ''
    def _extract_object(url_or_name: str) -> str:
        if not url_or_name:
            return ''
        if url_or_name.startswith('cartas/'):
            return url_or_name
        base = url_or_name.split('?', 1)[0]
        parts = base.split('/')
        if storage.bucket in parts:
            idx = parts.index(storage.bucket)
            return '/'.join(parts[idx+1:])
        if 'cartas/' in base:
            return base.split('cartas/', 1)[1].strip('/')
        return ''
    object_name = _extract_object(urlcarta)
    if not object_name:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    url = storage.get_presigned_url(object_name)
    return RedirectResponse(url=url, status_code=302)

# API REST

@router.get("/api", response_model=List[CartaSchema])
async def api_list_cartas(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API para listar cartinhas.
    """
    repository = CartasRepository(db)
    
    if status == "disponivel":
        return repository.get_available_cartas(skip=skip, limit=limit)
    elif status == "adotadas":
        return repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            repository.model.adotante_email != None,
            repository.model.status == "adotada"
        ).offset(skip).limit(limit).all()
    elif status == "entregues":
        from sqlalchemy import or_
        return repository.db.query(repository.model).filter(
            repository.model.del_bl == False,
            or_(
                repository.model.entregue_bl == True,
                repository.model.status.ilike("%entregue%"),
            ),
        ).order_by(repository.model.id.desc()).offset(skip).limit(limit).all()
    elif status == "minhas":
        return repository.get_adopted_cartas(user["email"], skip=skip, limit=limit)
    else:
        return repository.get_active_cartas(skip=skip, limit=limit)

@router.get("/api/{id_carta}", response_model=CartaSchema)
async def api_get_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API para obter detalhes de uma cartinha.
    """
    repository = CartasRepository(db)
    carta = repository.get_by_id_carta(id_carta)
    
    if not carta or carta.del_bl:
        raise HTTPException(status_code=404, detail="Cartinha não encontrada")
    
    return carta

@router.post("/api/adopt", response_model=CartaSchema)
async def api_adopt_carta(
    carta_adopt: CartaAdopt,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API para adotar uma cartinha.
    """
    repository = CartasRepository(db)
    carta = repository.adopt_carta(carta_adopt.id_carta, user["email"])
    
    if not carta:
        raise HTTPException(status_code=400, detail="Não foi possível adotar a cartinha")
    
    return carta

@router.post("/api/cancel/{id_carta}", response_model=CartaSchema)
async def api_cancel_adoption(
    id_carta: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API para cancelar a adoção de uma cartinha.
    """
    repository = CartasRepository(db)
    carta = repository.cancel_adoption(id_carta, user["email"])
    
    if not carta:
        raise HTTPException(status_code=400, detail="Não foi possível cancelar a adoção")
    
    return carta

@router.post("/api/release/{id_carta}", response_model=CartaSchema)
async def api_release_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API para liberar uma cartinha. ADMIN sempre pode; usuário comum apenas se for o adotante.
    """
    repository = CartasRepository(db)
    is_admin = any(role["code"] == "ADMIN" for role in user.get("roles", []))
    carta = repository.release_carta(id_carta, by_user_email=user.get("email"), is_admin=is_admin)
    if not carta:
        raise HTTPException(status_code=400, detail="Não foi possível liberar a cartinha")
    return carta

@router.post("/api/deliver/{id_carta}", response_model=CartaSchema)
async def api_deliver_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    API para marcar a cartinha como entregue (somente ADMIN).
    """
    repository = CartasRepository(db)
    carta = repository.mark_delivered(id_carta, admin_email=user.get("email"))
    if not carta:
        raise HTTPException(status_code=400, detail="Não foi possível marcar a entrega")
    return carta

@router.post("/api/undeliver/{id_carta}", response_model=CartaSchema)
async def api_undeliver_carta(
    id_carta: int,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    API para desmarcar a entrega da cartinha (somente ADMIN).
    """
    repository = CartasRepository(db)
    carta = repository.unmark_delivered(id_carta)
    if not carta:
        raise HTTPException(status_code=400, detail="Não foi possível desmarcar a entrega")
    return carta
