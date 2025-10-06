"""SQLAlchemy models for the application."""

from app.db import Base

# Import all models here to ensure they are registered with SQLAlchemy
from .modulo import Modulo
from .usuarios import Usuario
from .cartas import CartaDiversa
from .icon_presente import IconPresente
from .auth import Role, UserRole
