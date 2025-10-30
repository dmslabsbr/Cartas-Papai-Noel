from typing import Optional, Callable, Dict, Any
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings

logger = logging.getLogger("uvicorn")
SETTINGS = get_settings()

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware para verificar autenticação e gerenciar sessões.
    
    Este middleware verifica se o usuário está autenticado para rotas protegidas
    e redireciona para a página de login quando necessário.
    """
    
    def __init__(
        self,
        app,
        exclude_paths: list = None,
        public_paths: list = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/static", 
            "/health", 
            "/login", 
            "/logout",
            "/api/auth"
        ]
        # Rotas públicas (sem login): home, favicon, listagem/detalhe de cartinhas
        self.public_paths = public_paths or [
            "/",
            "/favicon.ico",
            "/cartas",
        ]
        # Prefixos GET públicos (APIs ou detalhes): permitir leitura sem login
        self.public_get_prefixes = [
            "/cartas/",         # detalhes HTML
            "/cartas/api",      # listagem e detalhes por API GET
        ]
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Não verificar autenticação para caminhos excluídos
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # Verificar se o usuário está autenticado
        user = request.session.get("user")
        
        # Para rotas públicas, apenas continuar (mesmo sem autenticação)
        if self._is_public_path(request):
            return await call_next(request)
        
        # Para rotas protegidas, verificar autenticação
        if not user:
            # Se for uma requisição API, retornar 401
            if request.url.path.startswith("/api/") or request.url.path.startswith("/cartas/api"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Não autenticado"}
                )
            # Se for uma requisição web, redirecionar para login
            # Importante: usar 303 See Other para forçar GET na página de login
            # e preservar a query string do destino original
            from fastapi import status as _status
            path = request.url.path
            qs = ("?" + str(request.query_params)) if str(request.query_params) else ""
            next_value = path + qs
            return RedirectResponse(url=f"/login?next={next_value}", status_code=_status.HTTP_303_SEE_OTHER)
        
        # Se estiver autenticado, continuar
        return await call_next(request)
    
    def _should_skip_auth(self, path: str) -> bool:
        """Verifica se o caminho deve ignorar a verificação de autenticação."""
        return any(path.startswith(exclude) for exclude in self.exclude_paths)
    
    def _is_public_path(self, request: Request) -> bool:
        """Verifica se o caminho é público (acessível sem login)."""
        path = request.url.path
        if path in self.public_paths:
            return True
        # Permitir GET em prefixos públicos (detalhes/listagem)
        if request.method.upper() == "GET" and any(path.startswith(pfx) for pfx in self.public_get_prefixes):
            return True
        return False
