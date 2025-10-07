from .cartas import router as cartas_router
from .relatorios import router as relatorios_router
from .usuarios import router as usuarios_router
from .modulos import router as modulos_router
from .permissoes import router as permissoes_router

__all__ = ["cartas_router", "relatorios_router", "usuarios_router", "modulos_router", "permissoes_router"]
