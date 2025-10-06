"""
Bootstrap Phase 1 for Noel migration (FastAPI + PostgreSQL + MinIO).

This script creates a minimal, runnable structure:
- VERSION (visible versioning source of truth)
- requirements.txt (pinned)
- FastAPI base app rendering "versão: {x.y.z}" in HTML
- tests ensuring VERSION exists and base HTML contains "versão:"
- initial PostgreSQL schema (Fase 1)
- Dockerfile (for the app)
- .env.example (environment variables sample)
- bump_version.py and a pre-commit hook (best-effort)

Usage (Windows PowerShell):
  py -m venv .venv
  . .venv/Scripts/Activate.ps1
  py scripts/bootstrap_phase1.py
  pip install -r requirements.txt
  # Optional (if Docker installed): docker compose -f docker-compose.app.yml up -d postgres minio
  uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import os
import sys

ROOT = Path(__file__).resolve().parents[1]


def write_file(path: Path, content: str, *, exist_ok: bool = True) -> bool:
    """Write a file with UTF-8 encoding. If exist_ok and file exists, keep it.
    Returns True if file was created/updated, False if skipped.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and exist_ok:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def append_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(content)


def ensure_dirs(paths: List[Path]) -> List[Path]:
    created: List[Path] = []
    for p in paths:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(p)
    return created


REQ_TXT = (
    "fastapi==0.115.2\n"
    "uvicorn[standard]==0.30.6\n"
    "Jinja2==3.1.4\n"
    "pydantic==2.9.2\n"
    "pydantic-settings==2.5.2\n"
    "SQLAlchemy==2.0.35\n"
    "alembic==1.13.2\n"
    "psycopg[binary]==3.2.3\n"
    "httpx==0.27.2\n"
    "pytest==8.3.3\n"
    "pytest-asyncio==0.24.0\n"
)

CONFIG_PY = (
    "from pydantic_settings import BaseSettings\n"
    "from pydantic import Field\n\n"
    "class Settings(BaseSettings):\n"
    "    \"\"\"Application settings loaded from environment (.env).\"\"\"\n"
    "    environment: str = Field(default=\"development\", alias=\"ENVIRONMENT\")\n"
    "    database_url: str = Field(alias=\"DATABASE_URL\")\n"
    "    minio_endpoint: str = Field(alias=\"MINIO_ENDPOINT\")\n"
    "    minio_bucket: str = Field(default=\"cartas\", alias=\"MINIO_BUCKET\")\n"
    "    app_port: int = Field(default=8000, alias=\"APP_PORT\")\n\n"
    "    class Config:\n"
    "        env_file = \".env\"\n"
    "        env_file_encoding = \"utf-8\"\n"
    "        case_sensitive = False\n\n"
    "def get_settings() -> \"Settings\":\n"
    "    return Settings()  # type: ignore[call-arg]\n"
)

MAIN_PY = (
    "from pathlib import Path\n"
    "from fastapi import FastAPI, Request\n"
    "from fastapi.responses import HTMLResponse\n"
    "from fastapi.templating import Jinja2Templates\n"
    "from .config import get_settings\n\n"
    "def read_version() -> str:\n"
    "    \"\"\"Read semantic version from the VERSION file at repo root.\"\"\"\n"
    "    version_file = Path(__file__).resolve().parents[1] / \"VERSION\"\n"
    "    try:\n"
    "        return version_file.read_text(encoding=\"utf-8\").strip()\n"
    "    except Exception:\n"
    "        return \"0.0.0\"\n\n"
    "app = FastAPI(title=\"Noel API\")\n"
    "templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / \"templates\"))\n"
    "SETTINGS = get_settings()\n"
    "APP_VERSION = read_version()\n\n"
    "@app.get(\"/\", response_class=HTMLResponse)\n"
    "async def index(request: Request) -> HTMLResponse:\n"
    "    return templates.TemplateResponse(\"base.html\", {\"request\": request, \"version\": APP_VERSION})\n"
)

BASE_HTML = (
    "<!doctype html>\n"
    "<html lang=\"pt-BR\">\n"
    "  <head>\n"
    "    <meta charset=\"utf-8\" />\n"
    "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
    "    <title>Noel</title>\n"
    "    <style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:2rem;}footer{margin-top:2rem;color:#555;font-size:.9rem}</style>\n"
    "  </head>\n"
    "  <body>\n"
    "    <h1>Cartinhas do Noel</h1>\n"
    "    <p>Base da migração para FastAPI.</p>\n"
    "    <footer>versão: {{ version }}</footer>\n"
    "  </body>\n"
    "</html>\n"
)

TEST_VERSION = (
    "import pathlib\n\n"
    "def test_version_file_exists():\n"
    "    root = pathlib.Path(__file__).resolve().parents[1]\n"
    "    version_path = root / \"VERSION\"\n"
    "    assert version_path.exists(), \"VERSION file must exist\"\n"
    "    assert version_path.read_text(encoding=\"utf-8\").strip() != \"\", \"VERSION must not be empty\"\n\n"
    "def test_base_template_contains_versao():\n"
    "    root = pathlib.Path(__file__).resolve().parents[1]\n"
    "    base_html = (root / \"app\" / \"templates\" / \"base.html\").read_text(encoding=\"utf-8\")\n"
    "    assert \"versão:\" in base_html, \"Base HTML must contain the string 'versão:'\"\n"
)

SCHEMA_SQL = (
    "-- Initial schema for PostgreSQL (Fase 1)\n"
    "CREATE TABLE IF NOT EXISTS modulo (\n"
    "    id_modulo SERIAL PRIMARY KEY,\n"
    "    nome TEXT NOT NULL UNIQUE\n"
    ");\n\n"
    "CREATE TABLE IF NOT EXISTS usuarios (\n"
    "    email TEXT PRIMARY KEY,\n"
    "    display_name TEXT NOT NULL,\n"
    "    matricula TEXT,\n"
    "    id_modulo INTEGER REFERENCES modulo(id_modulo),\n"
    "    bl_ativo BOOLEAN NOT NULL DEFAULT TRUE,\n"
    "    created_at TIMESTAMPTZ NOT NULL DEFAULT now()\n"
    ");\n\n"
    "CREATE TABLE IF NOT EXISTS cartas_diversas (\n"
    "    id SERIAL PRIMARY KEY,\n"
    "    id_carta INTEGER NOT NULL UNIQUE,\n"
    "    nome TEXT NOT NULL,\n"
    "    sexo TEXT NOT NULL CHECK (sexo IN ('M','F')),\n"
    "    presente TEXT NOT NULL,\n"
    "    status TEXT NOT NULL,\n"
    "    observacao TEXT,\n"
    "    adotante_email TEXT REFERENCES usuarios(email),\n"
    "    del_bl BOOLEAN NOT NULL DEFAULT FALSE,\n"
    "    del_time TIMESTAMPTZ,\n"
    "    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),\n"
    "    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()\n"
    ");\n\n"
    "CREATE INDEX IF NOT EXISTS idx_cartas_status ON cartas_diversas(status);\n"
    "CREATE INDEX IF NOT EXISTS idx_cartas_adotante ON cartas_diversas(adotante_email);\n"
    "CREATE INDEX IF NOT EXISTS idx_cartas_delbl ON cartas_diversas(del_bl);\n\n"
    "CREATE TABLE IF NOT EXISTS icon_presente (\n"
    "    id SERIAL PRIMARY KEY,\n"
    "    keyword TEXT NOT NULL,\n"
    "    icon_code TEXT NOT NULL\n"
    ");\n\n"
    "CREATE OR REPLACE VIEW vw_usuarios AS\n"
    "SELECT email, display_name, id_modulo, bl_ativo FROM usuarios;\n\n"
    "CREATE OR REPLACE VIEW vw_usuarios_ativos AS\n"
    "SELECT * FROM vw_usuarios WHERE bl_ativo = TRUE;\n"
)

DOCKERFILE = (
    "FROM python:3.12-slim\n"
    "WORKDIR /app\n"
    "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\n"
    "COPY requirements.txt ./\n"
    "RUN pip install --no-cache-dir -r requirements.txt\n"
    "COPY app ./app\n"
    "EXPOSE 8000\n"
    "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
)

ENV_EXAMPLE = (
    "# Application\n"
    "APP_PORT=8000\n"
    "ENVIRONMENT=development\n\n"
    "# PostgreSQL\n"
    "POSTGRES_USER=noel\n"
    "POSTGRES_PASSWORD=noel123\n"
    "POSTGRES_DB=noel\n"
    "POSTGRES_PORT=5432\n"
    "DATABASE_HOST=postgres\n"
    "DATABASE_URL=postgresql+psycopg://noel:noel123@postgres:5432/noel\n\n"
    "# MinIO\n"
    "MINIO_ROOT_USER=miniouser\n"
    "MINIO_ROOT_PASSWORD=miniosecret123\n"
    "MINIO_PORT=9000\n"
    "MINIO_CONSOLE_PORT=9001\n"
    "MINIO_ENDPOINT=http://minio:9000\n"
    "MINIO_BUCKET=cartas\n\n"
    "# Alembic\n"
    "ALEMBIC_CONFIG=alembic.ini\n"
)

BUMP_VERSION = (
    '"""\nSimple version bump script (semantic version, patch increment by default).\nUsage:\n  py scripts/bump_version.py [major|minor|patch]\n"""\n'
    "from __future__ import annotations\n"
    "import sys\n"
    "from pathlib import Path\n\n"
    "def bump(part: str = \"patch\") -> str:\n"
    "    version_file = Path(__file__).resolve().parents[1] / \"VERSION\"\n"
    "    current = version_file.read_text(encoding=\"utf-8\").strip()\n"
    "    major, minor, patch = (int(x) for x in current.split(\".\"))\n"
    "    if part == \"major\":\n"
    "        major, minor, patch = major + 1, 0, 0\n"
    "    elif part == \"minor\":\n"
    "        minor, patch = minor + 1, 0\n"
    "    else:\n"
    "        patch += 1\n"
    "    new_v = f\"{major}.{minor}.{patch}\"\n"
    "    version_file.write_text(new_v, encoding=\"utf-8\")\n"
    "    print(new_v)\n"
    "    return new_v\n\n"
    "if __name__ == \"__main__\":\n"
    "    arg = sys.argv[1] if len(sys.argv) > 1 else \"patch\"\n"
    "    bump(arg)\n"
)

PRE_COMMIT_SH = (
    "#!/usr/bin/env bash\n"
    "set -e\n"
    "if command -v python >/dev/null 2>&1; then PY=python; elif command -v py >/dev/null 2>&1; then PY=py; else exit 0; fi\n"
    "$PY scripts/bump_version.py patch >/dev/null 2>&1 || true\n"
    "git add VERSION >/dev/null 2>&1 || true\n"
)

README_APPEND = (
    "\n---\n\n## FastAPI (Migração — Fase 1)\n\n"
    "### Ambiente virtual (Windows)\n"
    "```powershell\npy -m venv .venv\n. .venv\\Scripts\\Activate.ps1\npip install -r requirements.txt\n```\n\n"
    "### Variáveis de ambiente\nCrie um arquivo `.env` baseado nos valores de `.env.example`.\n\n"
    "### Subir infraestrutura (opcional)\n"
    "```powershell\ndocker compose -f docker-compose.app.yml up -d postgres minio\n```\n\n"
    "### Rodar a aplicação (dev)\n"
    "```powershell\nuvicorn app.main:app --reload --port 8000\n```\n\n"
    "### Testes\n````powershell\npytest -q\n````\n\n"
    "### Versionamento visível\n- Fonte de verdade: arquivo `VERSION` (renderizado no HTML como `versão: x.y.z`).\n- Testes garantem a presença de `VERSION` e da string `\"versão:\"` no HTML base.\n\n"
)


def main() -> None:
    created_items: Dict[str, List[str]] = {"dirs": [], "files": []}

    # Ensure directories
    dirs = [
        ROOT / "app",
        ROOT / "app" / "templates",
        ROOT / "tests",
        ROOT / "db" / "init",
        ROOT / "scripts",
    ]
    for d in ensure_dirs(dirs):
        created_items["dirs"].append(str(d.relative_to(ROOT)))

    # VERSION
    if write_file(ROOT / "VERSION", "0.1.0\n", exist_ok=True):
        created_items["files"].append("VERSION")

    # requirements
    if write_file(ROOT / "requirements.txt", REQ_TXT, exist_ok=True):
        created_items["files"].append("requirements.txt")

    # app package
    write_file(ROOT / "app" / "__init__.py", "", exist_ok=True)
    if write_file(ROOT / "app" / "config.py", CONFIG_PY, exist_ok=True):
        created_items["files"].append("app/config.py")
    if write_file(ROOT / "app" / "main.py", MAIN_PY, exist_ok=True):
        created_items["files"].append("app/main.py")
    if write_file(ROOT / "app" / "templates" / "base.html", BASE_HTML, exist_ok=True):
        created_items["files"].append("app/templates/base.html")

    # tests
    if write_file(ROOT / "tests" / "test_version.py", TEST_VERSION, exist_ok=True):
        created_items["files"].append("tests/test_version.py")

    # DB schema
    if write_file(ROOT / "db" / "init" / "001_schema.sql", SCHEMA_SQL, exist_ok=True):
        created_items["files"].append("db/init/001_schema.sql")

    # Dockerfile
    if write_file(ROOT / "Dockerfile", DOCKERFILE, exist_ok=True):
        created_items["files"].append("Dockerfile")

    # env example
    if write_file(ROOT / ".env.example", ENV_EXAMPLE, exist_ok=True):
        created_items["files"].append(".env.example")

    # bump script
    if write_file(ROOT / "scripts" / "bump_version.py", BUMP_VERSION, exist_ok=True):
        created_items["files"].append("scripts/bump_version.py")

    # git hook (best-effort)
    git_dir = ROOT / ".git"
    hooks_dir = git_dir / "hooks"
    if git_dir.exists() and hooks_dir.exists():
        pre_commit = hooks_dir / "pre-commit"
        if write_file(pre_commit, PRE_COMMIT_SH, exist_ok=True):
            try:
                os.chmod(pre_commit, 0o775)
            except Exception:
                pass
            created_items["files"].append(".git/hooks/pre-commit")

    # README augmentation (append if present, else skip)
    readme = ROOT / "README.md"
    try:
        if readme.exists():
            append_file(readme, README_APPEND)
        else:
            # Create a minimal README if not present
            base_readme = (
                "# Noel (Migração Python — Fase 1)\n\n"
                "Este repositório contém a infraestrutura inicial para migrar o app Noel para FastAPI.\n\n"
            )
            write_file(readme, base_readme + README_APPEND, exist_ok=True)
            created_items["files"].append("README.md")
    except Exception:
        pass

    # Summary
    print("Bootstrap Phase 1 completed.")
    if created_items["dirs"]:
        print("Created directories:")
        for d in created_items["dirs"]:
            print(f" - {d}")
    if created_items["files"]:
        print("Created files:")
        for f in created_items["files"]:
            print(f" - {f}")
    print("Next steps:")
    print(" 1) Create .env from .env.example and adjust values.")
    print(" 2) py -m venv .venv && . .venv/Scripts/Activate.ps1 && pip install -r requirements.txt")
    print(" 3) Optional: docker compose -f docker-compose.app.yml up -d postgres minio")
    print(" 4) uvicorn app.main:app --reload --port 8000")
    print(" 5) pytest -q")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
        sys.exit(1)
