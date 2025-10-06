"""
Serviço de armazenamento para anexos de cartinhas usando MinIO.

Este serviço encapsula operações de upload e acesso a arquivos (PDFs e imagens)
relacionados às cartinhas.

Notas:
- Importa o cliente MinIO de forma preguiçosa para evitar erros de import no startup
  caso a dependência ainda não esteja instalada.
- Valida tipos MIME permitidos: application/pdf, image/jpeg, image/png, image/webp.
- Gera chaves de objeto organizadas por prefixo (e.g., cartas/{id_carta}/anexo.ext).
"""
from __future__ import annotations

from typing import Optional, List
from datetime import timedelta
import os
import mimetypes
import uuid
import logging

from fastapi import UploadFile, HTTPException, status

from app.config import get_settings


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}

logger = logging.getLogger("uvicorn")


class StorageService:
    """Serviço de armazenamento baseado em MinIO."""

    def __init__(self) -> None:
        settings = get_settings()
        self.endpoint: str = settings.minio_endpoint
        self.bucket: str = settings.minio_bucket
        # Preferir credenciais do settings (arquivo .env) e cair para env vars apenas se necessário
        access_key = settings.minio_access_key or settings.minio_root_user or os.getenv("MINIO_ACCESS_KEY") or os.getenv("MINIO_ROOT_USER")
        secret_key = settings.minio_secret_key or settings.minio_root_password or os.getenv("MINIO_SECRET_KEY") or os.getenv("MINIO_ROOT_PASSWORD")
        if not access_key or not secret_key:
            logger.error("[StorageService] Credenciais MinIO ausentes (endpoint=%s, bucket=%s)", self.endpoint, self.bucket)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credenciais MinIO não configuradas"
            )
        self.access_key: str = access_key
        self.secret_key: str = secret_key
        logger.info("[StorageService] Configurado com endpoint=%s, bucket=%s, secure=%s", self.endpoint, self.bucket, str(self.endpoint.startswith("https://")))

    def _client(self):
        """Cria o cliente MinIO sob demanda."""
        try:
            from minio import Minio
        except Exception as exc:  # ImportError ou similar
            logger.exception("[StorageService] Dependência 'minio' não instalada")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependência 'minio' não instalada"
            ) from exc
        # Detectar uso de http/https a partir do endpoint
        secure = self.endpoint.startswith("https://")
        endpoint = self.endpoint.replace("https://", "").replace("http://", "")
        logger.debug("[StorageService] Criando cliente MinIO endpoint=%s secure=%s", endpoint, secure)
        return Minio(endpoint, access_key=self.access_key, secret_key=self.secret_key, secure=secure)

    def _ensure_bucket(self) -> None:
        client = self._client()
        try:
            exists = client.bucket_exists(self.bucket)
            logger.debug("[StorageService] Verificando bucket '%s' (exists=%s)", self.bucket, exists)
            if not exists:
                logger.info("[StorageService] Criando bucket '%s'", self.bucket)
                client.make_bucket(self.bucket)
        except Exception as exc:
            logger.exception("[StorageService] Falha ao garantir bucket '%s'", self.bucket)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao preparar bucket MinIO"
            ) from exc

    @staticmethod
    def _validate_mime(upload: UploadFile) -> None:
        filename = upload.filename or ""
        content_type = upload.content_type or mimetypes.guess_type(filename)[0]
        logger.debug("[StorageService] Validando MIME filename=%s content_type=%s", filename, content_type)
        if not content_type or content_type not in ALLOWED_MIME_TYPES:
            logger.warning("[StorageService] MIME não permitido filename=%s content_type=%s", filename, content_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de arquivo não permitido. Envie PDF ou imagem (JPEG/PNG/WEBP).",
            )

    @staticmethod
    def _object_name_for_carta(id_carta: int, filename: Optional[str]) -> str:
        # Preserva extensão, gera nome único
        ext = ""
        if filename and "." in filename:
            ext = filename[filename.rfind(".") :]
        unique = uuid.uuid4().hex
        return f"cartas/{id_carta}/anexo-{unique}{ext}"

    def upload_carta_anexo(self, id_carta: int, upload: UploadFile) -> str:
        """
        Faz upload de um anexo de cartinha e retorna o nome do objeto.
        """
        self._validate_mime(upload)
        self._ensure_bucket()
        client = self._client()

        object_name = self._object_name_for_carta(id_carta, upload.filename)
        size = 0
        # Tentar obter tamanho se disponível (nem sempre UploadFile sabe o tamanho)
        try:
            if hasattr(upload.file, "seek") and hasattr(upload.file, "tell"):
                pos = upload.file.tell()
                upload.file.seek(0, os.SEEK_END)
                size = upload.file.tell()
                upload.file.seek(pos)
        except Exception:
            size = 0
        logger.info(
            "[StorageService] Iniciando upload id_carta=%s filename=%s content_type=%s size=%s object_name=%s",
            id_carta,
            upload.filename,
            upload.content_type,
            size,
            object_name,
        )

        try:
            # Enviar stream; se size=0, MinIO ainda aceita o stream em put_object com part_size
            client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=upload.file,
                length=size if size > 0 else -1,
                part_size=10 * 1024 * 1024,  # 10MB
                content_type=upload.content_type,
            )
            logger.info("[StorageService] Upload concluído bucket=%s object=%s", self.bucket, object_name)
        except Exception as exc:
            logger.exception("[StorageService] Falha no upload para bucket=%s object=%s", self.bucket, object_name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao enviar anexo para MinIO"
            ) from exc
        return object_name

    def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(minutes=15)) -> str:
        """Gera URL assinado temporário para download do objeto."""
        client = self._client()
        try:
            url = client.presigned_get_object(self.bucket, object_name, expires=expires)
            logger.debug("[StorageService] URL assinada gerada object=%s expires=%ss", object_name, int(expires.total_seconds()))
            return url
        except Exception as exc:
            logger.exception("[StorageService] Falha ao gerar URL assinada object=%s", object_name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao gerar URL de download"
            ) from exc

    def delete_object(self, object_name: str) -> None:
        """Remove um objeto do bucket."""
        client = self._client()
        try:
            client.remove_object(self.bucket, object_name)
            logger.info("[StorageService] Objeto removido bucket=%s object=%s", self.bucket, object_name)
        except Exception as exc:
            logger.exception("[StorageService] Falha ao remover object=%s", object_name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao remover objeto MinIO"
            ) from exc

    def list_carta_anexos(self, id_carta: int) -> List[str]:
        """Lista nomes de objetos de anexos para a carta (prefixo cartas/{id_carta}/)."""
        client = self._client()
        prefix = f"cartas/{id_carta}/"
        try:
            objects = client.list_objects(self.bucket, prefix=prefix, recursive=True)
            names: List[str] = []
            for obj in objects:
                names.append(getattr(obj, "object_name", ""))
            result = [n for n in names if n]
            logger.debug("[StorageService] Listados %s anexos prefix=%s", len(result), prefix)
            return result
        except Exception as exc:
            logger.exception("[StorageService] Falha ao listar anexos prefix=%s", prefix)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao listar anexos"
            ) from exc

    def get_latest_carta_anexo_url(self, id_carta: int, expires: timedelta = timedelta(minutes=15)) -> Optional[str]:
        """Retorna URL assinada do anexo mais recente da carta, se existir."""
        client = self._client()
        prefix = f"cartas/{id_carta}/"
        latest_obj = None
        latest_time = None
        try:
            for obj in client.list_objects(self.bucket, prefix=prefix, recursive=True):
                obj_time = getattr(obj, "last_modified", None)
                if latest_time is None or (obj_time and obj_time > latest_time):
                    latest_time = obj_time
                    latest_obj = getattr(obj, "object_name", None)
            if not latest_obj:
                logger.info("[StorageService] Nenhum anexo encontrado para id_carta=%s", id_carta)
                return None
            url = client.presigned_get_object(self.bucket, latest_obj, expires=expires)
            logger.debug("[StorageService] URL mais recente gerada object=%s", latest_obj)
            return url
        except Exception as exc:
            logger.exception("[StorageService] Falha ao obter URL do anexo mais recente id_carta=%s", id_carta)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao obter URL do anexo mais recente"
            ) from exc
