from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import logging
import httpx
import anyio
import psycopg
import traceback
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List
import re

from .config import get_settings
from .db import get_db
from .middleware import AuthMiddleware
from .services import AuthService
from .dependencies import get_current_user, require_roles
from .routers import cartas_router, relatorios_router


def read_version() -> str:
    """Read semantic version from the VERSION file at repo root."""
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0"


SETTINGS = get_settings()
APP_VERSION = read_version()

# Inicializar a aplicação FastAPI
app = FastAPI(
    title="Noel API",
    description="API para o sistema Noel",
    version=APP_VERSION
)

# Configurar diretórios de templates e arquivos estáticos
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
# Disponibilizar versão globalmente nos templates (widget reutilizável)
templates.env.globals["app_version"] = APP_VERSION
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if SETTINGS.environment == "development" else ["https://noel.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de autenticação
app.add_middleware(
    AuthMiddleware,
    exclude_paths=["/static", "/health", "/login", "/logout", "/api/auth"],
    public_paths=["/", "/favicon.ico", "/cartas"]
)

# Configurar middleware de sessão (deve ser adicionado por último para ser executado primeiro)
app.add_middleware(
    SessionMiddleware,
    secret_key=SETTINGS.session_secret_key,
    max_age=SETTINGS.session_max_age
)

# Incluir routers
app.include_router(cartas_router)
app.include_router(relatorios_router)

@app.on_event("startup")
async def _log_version_on_startup() -> None:
    logger = logging.getLogger("uvicorn")
    logger.info("Noel API starting - version=%s environment=%s", APP_VERSION, SETTINGS.environment)


async def _check_minio_ready(*, debug: bool = False) -> Union[Dict[str, Any], bool]:
    """Check if MinIO is ready by calling its health endpoint."""
    if debug:
        result = {"ok": False, "url": "", "error": None}
        try:
            url = SETTINGS.minio_endpoint.rstrip("/") + "/minio/health/ready"
            result["url"] = url
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(url)
                result["status_code"] = resp.status_code
                result["ok"] = resp.status_code == 200
                if not result["ok"]:
                    result["error"] = f"Unexpected status: {resp.status_code}"
                return result
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            return result
    else:
        try:
            url = SETTINGS.minio_endpoint.rstrip("/") + "/minio/health/ready"
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False


def _check_db_sync(*, debug: bool = False) -> Union[Dict[str, Any], bool]:
    """Check if PostgreSQL is ready by executing a simple query."""
    # Converter formato SQLAlchemy para formato direto do psycopg
    # De: postgresql+psycopg://user:pass@host:port/dbname
    # Para: postgresql://user:pass@host:port/dbname
    db_url = SETTINGS.database_url.replace("postgresql+psycopg://", "postgresql://")
    
    if debug:
        result = {"ok": False, "url": SETTINGS.database_url, "error": None}
        try:
            # Mask password in URL for display
            display_url = SETTINGS.database_url
            if "@" in display_url and ":" in display_url.split("@")[0]:
                user_part = display_url.split("@")[0]
                if ":" in user_part:
                    username = user_part.split(":")[0]
                    result["url"] = f"{username}:***@{display_url.split('@', 1)[1]}"
            
            # Usar a URL convertida para conexão direta
            with psycopg.connect(db_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS health_check")
                    row = cur.fetchone()
                    result["ok"] = row is not None and row[0] == 1
                    result["query_result"] = row[0] if row else None
                    result["connection_string_used"] = db_url.replace(
                        db_url.split("://")[1].split("@")[0].split(":", 1)[1], "***"
                    ) if "://" in db_url and "@" in db_url else db_url
            return result
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            result["connection_string_tried"] = db_url.replace(
                db_url.split("://")[1].split("@")[0].split(":", 1)[1], "***"
            ) if "://" in db_url and "@" in db_url else db_url
            return result
    else:
        try:
            # Usar a URL convertida para conexão direta
            with psycopg.connect(db_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            return False


async def _check_ldap_ready(*, debug: bool = False) -> Dict[str, Any]:
    """Check if LDAP auth API is reachable and try to extract its version.

    Strategy:
    - GET base URL from settings (SETTINGS.ldap_api_url)
    - Try to parse JSON and look for common version fields
    - Fallback to searching a semantic version in the text body
    """
    result: Dict[str, Any] = {"ok": False, "url": SETTINGS.ldap_api_url, "version": None}
    try:
        base_url = SETTINGS.ldap_api_url.rstrip("/")
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(base_url)
            result["status_code"] = resp.status_code
            if resp.status_code == 200:
                # Try JSON first
                version: Optional[str] = None
                try:
                    data = resp.json()
                    # Common keys that might hold version info
                    for key in ("version", "app_version", "build", "tag"):
                        if isinstance(data, dict) and key in data and isinstance(data[key], str):
                            version = data[key]
                            break
                except Exception:
                    # Not JSON; fallback to text search
                    text = resp.text or ""
                    m = re.search(r"\b(\d+\.\d+\.\d+(?:[-+][\w\.]+)?)\b", text)
                    if m:
                        version = m.group(1)

                result["version"] = version
                result["ok"] = True
            else:
                result["error"] = f"Unexpected status: {resp.status_code}"
    except Exception as e:
        result["error"] = str(e)
        if debug:
            result["traceback"] = traceback.format_exc()
    return result


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint with status summary."""
    from datetime import datetime
    
    minio_ok = await _check_minio_ready()
    ldap_result = await _check_ldap_ready()
    db_ok = await anyio.to_thread.run_sync(_check_db_sync)
    status = "ok" if (minio_ok and db_ok and ldap_result.get("ok")) else (
        "degraded" if (minio_ok or db_ok or ldap_result.get("ok")) else "down"
    )
    
    # Horário atual no formato ISO 8601
    current_time = datetime.now().isoformat()
    
    return {
        "status": status, 
        "version": APP_VERSION, 
        "minio_ok": minio_ok, 
        "db_ok": db_ok,
        "ldap_ok": bool(ldap_result.get("ok")),
        "ldap_version": ldap_result.get("version"),
        "time": current_time
    }


@app.get("/health/debug")
async def health_debug() -> dict:
    """
    Detailed health check with debugging information.
    
    Shows detailed diagnostics in server logs but returns only basic status to client.
    """
    from datetime import datetime
    import json
    
    # Coleta informações detalhadas para logging no servidor
    minio_result = await _check_minio_ready(debug=True)
    ldap_result = await _check_ldap_ready(debug=True)
    
    # anyio.to_thread.run_sync() não aceita keyword arguments, então precisamos usar uma função wrapper
    async def _check_db_with_debug():
        return await anyio.to_thread.run_sync(lambda: _check_db_sync(debug=True))
    
    db_result = await _check_db_with_debug()
    
    status = (
        "ok"
        if (minio_result["ok"] and db_result["ok"] and ldap_result.get("ok"))
        else (
            "degraded"
            if (minio_result["ok"] or db_result["ok"] or ldap_result.get("ok"))
            else "down"
        )
    )
    
    # Informações detalhadas para log do servidor
    debug_info = {
        "status": status,
        "version": APP_VERSION,
        "minio": minio_result,
        "database": db_result,
        "ldap": ldap_result,
        "env": {
            "minio_endpoint": SETTINGS.minio_endpoint,
            "minio_bucket": SETTINGS.minio_bucket,
            "database_url_masked": db_result["url"],  # Masked password
            "environment": SETTINGS.environment,
        }
    }
    
    # Log detalhado no terminal do servidor
    logger = logging.getLogger("uvicorn")
    logger.info("=== HEALTH DEBUG INFO ===")
    # Usar level INFO para garantir que seja exibido
    debug_json = json.dumps(debug_info, indent=2, default=str)
    for line in debug_json.split("\n"):
        logger.info(line)
    logger.info("=========================")
    
    # Para o cliente, retorna apenas o status básico (igual ao /health)
    current_time = datetime.now().isoformat()
    return {
        "status": status, 
        "version": APP_VERSION, 
        "minio_ok": minio_result["ok"], 
        "db_ok": db_result["ok"],
        "ldap_ok": bool(ldap_result.get("ok")),
        "ldap_version": ldap_result.get("version"),
        "time": current_time
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Página inicial do sistema."""
    user = request.session.get("user")
    return templates.TemplateResponse(
        "base.html", 
        {"request": request, "version": APP_VERSION, "user": user}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, 
    next: Optional[str] = None,
    error: Optional[str] = None
) -> HTMLResponse:
    """Página de login."""
    # Se já estiver autenticado, redirecionar para a página inicial
    if request.session.get("user"):
        return RedirectResponse(url=next or "/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "version": APP_VERSION, "next": next, "error": error}
    )


@app.post("/login")
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> RedirectResponse:
    """Processa o formulário de login."""
    auth_service = AuthService(db)
    next_url = request.query_params.get("next", "/")
    
    try:
        success, user_data = await auth_service.authenticate(
            username=form_data.username,
            password=form_data.password
        )
        
        if success and user_data:
            # Armazenar dados do usuário na sessão
            request.session["user"] = user_data
            return RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
        else:
            # Falha na autenticação
            return RedirectResponse(
                url=f"/login?next={next_url}&error=invalid_credentials",
                status_code=status.HTTP_302_FOUND
            )
    except HTTPException as e:
        # Erro no serviço de autenticação
        return RedirectResponse(
            url=f"/login?next={next_url}&error={e.detail}",
            status_code=status.HTTP_302_FOUND
        )


@app.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Encerra a sessão do usuário."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
) -> HTMLResponse:
    """Página de dashboard (protegida)."""
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "version": APP_VERSION, "user": user}
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"]))
) -> HTMLResponse:
    """Página de administração (protegida, apenas para administradores)."""
    return templates.TemplateResponse(
        "admin.html", 
        {"request": request, "version": APP_VERSION, "user": user}
    )


# API de autenticação
@app.post("/api/auth/login")
async def api_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """API para autenticação."""
    auth_service = AuthService(db)
    
    success, user_data = await auth_service.authenticate(
        username=form_data.username,
        password=form_data.password
    )
    
    if not success or not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implementar geração de token JWT
    
    return {
        "access_token": "temporary_token",  # Placeholder para token JWT
        "token_type": "bearer",
        "user": user_data
    }


@app.get("/api/auth/me")
async def api_me(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """API para obter dados do usuário atual."""
    return user
