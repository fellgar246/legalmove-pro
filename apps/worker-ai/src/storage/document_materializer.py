"""Materialize document storage references into local file paths."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.errors import DocumentLoadError
from pipeline.path_resolver import resolve_document_path

_CONTENT_TYPE_EXTENSIONS: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

_SUPPORTED_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif"})


@dataclass(frozen=True)
class DocumentStorageRef:
    document_id: str
    storage_provider: str
    storage_path: str
    storage_key: str | None
    original_filename: str | None
    content_type: str | None


@dataclass(frozen=True)
class MaterializedDocument:
    local_path: str
    should_cleanup: bool


class DocumentMaterializationError(DocumentLoadError):
    """Failed to materialize a document for processing."""


def _normalize_provider(provider: str | None) -> str:
    if provider is None or not str(provider).strip():
        return "local"
    return str(provider).strip().lower()


def _extension_from_name(name: str | None) -> str:
    if not name:
        return ""
    suffix = Path(name).suffix.lower()
    if suffix in _SUPPORTED_EXTENSIONS:
        return suffix
    return ""


def _extension_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ""
    normalized = content_type.strip().lower().split(";", 1)[0].strip()
    return _CONTENT_TYPE_EXTENSIONS.get(normalized, "")


def infer_document_extension(ref: DocumentStorageRef) -> str:
    """Choose a file suffix for temporary S3 downloads."""
    for candidate in (
        _extension_from_name(ref.storage_key),
        _extension_from_name(ref.original_filename),
        _extension_from_content_type(ref.content_type),
    ):
        if candidate:
            return candidate
    return ""


class DocumentMaterializer:
    """Resolve document storage references to local filesystem paths."""

    def __init__(
        self,
        *,
        aws_region: str = "",
        s3_bucket: str = "",
        temp_dir: str = "",
        s3_client: Any | None = None,
    ) -> None:
        self._aws_region = aws_region.strip()
        self._s3_bucket = s3_bucket.strip()
        self._temp_dir = temp_dir.strip()
        self._s3_client = s3_client

    def materialize(self, doc: DocumentStorageRef) -> MaterializedDocument:
        provider = _normalize_provider(doc.storage_provider)
        if provider == "local":
            local_path = resolve_document_path(doc.storage_path)
            return MaterializedDocument(local_path=local_path, should_cleanup=False)
        if provider == "s3":
            return self._materialize_s3(doc)
        raise DocumentMaterializationError(
            f"Unsupported document storage provider: {doc.storage_provider!r}"
        )

    def cleanup(self, materialized: MaterializedDocument) -> None:
        if not materialized.should_cleanup:
            return
        path = Path(materialized.local_path)
        if path.is_file():
            path.unlink()

    def _materialize_s3(self, doc: DocumentStorageRef) -> MaterializedDocument:
        if not self._s3_bucket:
            raise DocumentMaterializationError(
                "S3_BUCKET is required to materialize S3 documents."
            )

        key = (doc.storage_key or "").strip() or doc.storage_path.strip()
        if not key:
            raise DocumentMaterializationError("S3 document is missing storage_key.")

        suffix = infer_document_extension(doc)
        temp_dir = self._prepare_temp_dir()
        fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=temp_dir)
        os.close(fd)

        client = self._get_s3_client()
        try:
            client.download_file(self._s3_bucket, key, temp_path)
        except Exception as exc:
            self._cleanup_partial(temp_path)
            raise self._map_s3_download_error(key, exc) from exc

        if not Path(temp_path).is_file():
            raise DocumentMaterializationError(
                f"Downloaded S3 document was not created: {temp_path}"
            )

        return MaterializedDocument(local_path=temp_path, should_cleanup=True)

    def _get_s3_client(self) -> Any:
        if self._s3_client is not None:
            return self._s3_client

        try:
            import boto3
            from botocore.exceptions import NoCredentialsError
        except ImportError as exc:
            raise DocumentMaterializationError(
                "boto3 is required to materialize S3 documents."
            ) from exc

        kwargs: dict[str, str] = {}
        if self._aws_region:
            kwargs["region_name"] = self._aws_region

        try:
            client = boto3.client("s3", **kwargs)
        except NoCredentialsError as exc:
            raise DocumentMaterializationError(
                "AWS credentials are not available for S3 document download."
            ) from exc

        self._s3_client = client
        return client

    def _map_s3_download_error(self, key: str, exc: Exception) -> DocumentMaterializationError:
        try:
            from botocore.exceptions import ClientError, NoCredentialsError
        except ImportError:
            return DocumentMaterializationError(f"Failed to download S3 document: {key}")

        if isinstance(exc, NoCredentialsError):
            return DocumentMaterializationError(
                "AWS credentials are not available for S3 document download."
            )

        if isinstance(exc, ClientError):
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return DocumentMaterializationError(f"S3 document not found: {key}")
            return DocumentMaterializationError(f"Failed to download S3 document: {key}")

        return DocumentMaterializationError(f"Failed to download S3 document: {key}")

    def _prepare_temp_dir(self) -> str:
        if self._temp_dir:
            path = Path(self._temp_dir)
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
        return tempfile.gettempdir()

    def _cleanup_partial(self, temp_path: str) -> None:
        path = Path(temp_path)
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass
