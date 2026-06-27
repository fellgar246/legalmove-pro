import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from storage.document_materializer import (
    DocumentMaterializationError,
    DocumentMaterializer,
    DocumentStorageRef,
    MaterializedDocument,
    infer_document_extension,
)


def _local_ref(storage_path: str) -> DocumentStorageRef:
    return DocumentStorageRef(
        document_id="doc-local",
        storage_provider="local",
        storage_path=storage_path,
        storage_key="orig.png",
        original_filename="orig.png",
        content_type="image/png",
    )


def _s3_ref(
    *,
    storage_key: str = "dev/documents/original/2026/06/abc-contract.pdf",
    original_filename: str = "contract.pdf",
    content_type: str = "application/pdf",
) -> DocumentStorageRef:
    return DocumentStorageRef(
        document_id="doc-s3",
        storage_provider="s3",
        storage_path=storage_key,
        storage_key=storage_key,
        original_filename=original_filename,
        content_type=content_type,
    )


def _azure_blob_ref(
    *,
    storage_key: str = "documents/original/2026/06/abc-contract.pdf",
    original_filename: str = "contract.pdf",
    content_type: str = "application/pdf",
) -> DocumentStorageRef:
    return DocumentStorageRef(
        document_id="doc-azure",
        storage_provider="azure_blob",
        storage_path=storage_key,
        storage_key=storage_key,
        original_filename=original_filename,
        content_type=content_type,
    )


def test_materialize_local_returns_existing_path_without_cleanup(tmp_path, monkeypatch):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    file_path = uploads_dir / "orig.png"
    file_path.write_bytes(b"png")
    monkeypatch.setenv("UPLOADS_DIR", str(uploads_dir))

    materializer = DocumentMaterializer()
    materialized = materializer.materialize(_local_ref(str(file_path)))

    assert materialized.local_path == str(file_path.resolve())
    assert materialized.should_cleanup is False


def test_materialize_local_treats_empty_provider_as_local(tmp_path, monkeypatch):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    file_path = uploads_dir / "orig.png"
    file_path.write_bytes(b"png")
    monkeypatch.setenv("UPLOADS_DIR", str(uploads_dir))

    ref = DocumentStorageRef(
        document_id="doc-local",
        storage_provider="",
        storage_path=str(file_path),
        storage_key="orig.png",
        original_filename="orig.png",
        content_type="image/png",
    )
    materializer = DocumentMaterializer()
    materialized = materializer.materialize(ref)

    assert materialized.local_path == str(file_path.resolve())
    assert materialized.should_cleanup is False


def test_materialize_s3_downloads_to_temp_file_with_pdf_extension(tmp_path):
    temp_dir = tmp_path / "documents"
    temp_dir.mkdir()
    payload = b"%PDF-1.4 mock"

    def fake_download(bucket: str, key: str, filename: str) -> None:
        assert bucket == "legalmove-pro-dev-documents"
        assert key == "dev/documents/original/2026/06/abc-contract.pdf"
        Path(filename).write_bytes(payload)

    s3_client = MagicMock()
    s3_client.download_file.side_effect = fake_download

    materializer = DocumentMaterializer(
        aws_region="us-east-1",
        s3_bucket="legalmove-pro-dev-documents",
        temp_dir=str(temp_dir),
        s3_client=s3_client,
    )
    materialized = materializer.materialize(_s3_ref())

    assert materialized.should_cleanup is True
    assert materialized.local_path.endswith(".pdf")
    assert Path(materialized.local_path).read_bytes() == payload
    s3_client.download_file.assert_called_once()


def test_materialize_s3_infers_extension_from_content_type(tmp_path):
    temp_dir = tmp_path / "documents"
    temp_dir.mkdir()

    def fake_download(_bucket: str, _key: str, filename: str) -> None:
        Path(filename).write_bytes(b"png")

    s3_client = MagicMock()
    s3_client.download_file.side_effect = fake_download

    ref = DocumentStorageRef(
        document_id="doc-s3",
        storage_provider="s3",
        storage_path="dev/documents/original/2026/06/abc",
        storage_key="dev/documents/original/2026/06/abc",
        original_filename="scan",
        content_type="image/png",
    )
    materializer = DocumentMaterializer(
        s3_bucket="bucket",
        temp_dir=str(temp_dir),
        s3_client=s3_client,
    )
    materialized = materializer.materialize(ref)

    assert materialized.local_path.endswith(".png")


def test_materialize_s3_requires_bucket():
    materializer = DocumentMaterializer(s3_bucket="")
    with pytest.raises(DocumentMaterializationError, match="S3_BUCKET is required"):
        materializer.materialize(_s3_ref())


def test_materialize_s3_requires_storage_key():
    materializer = DocumentMaterializer(s3_bucket="bucket")
    ref = DocumentStorageRef(
        document_id="doc-s3",
        storage_provider="s3",
        storage_path="",
        storage_key="",
        original_filename="contract.pdf",
        content_type="application/pdf",
    )
    with pytest.raises(DocumentMaterializationError, match="missing storage_key"):
        materializer.materialize(ref)


def test_materialize_unknown_provider_fails_clearly():
    ref = DocumentStorageRef(
        document_id="doc-x",
        storage_provider="gcs",
        storage_path="path",
        storage_key="path",
        original_filename="file.pdf",
        content_type="application/pdf",
    )
    materializer = DocumentMaterializer()
    with pytest.raises(
        DocumentMaterializationError,
        match="Unsupported document storage provider",
    ):
        materializer.materialize(ref)


def test_materialize_s3_maps_not_found_error(tmp_path):
    from botocore.exceptions import ClientError

    temp_dir = tmp_path / "documents"
    temp_dir.mkdir()

    s3_client = MagicMock()
    s3_client.download_file.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
        "GetObject",
    )

    materializer = DocumentMaterializer(
        s3_bucket="bucket",
        temp_dir=str(temp_dir),
        s3_client=s3_client,
    )

    with pytest.raises(DocumentMaterializationError, match="S3 document not found"):
        materializer.materialize(_s3_ref())


def test_cleanup_removes_temporary_file(tmp_path):
    temp_file = tmp_path / "temp.pdf"
    temp_file.write_bytes(b"pdf")
    materializer = DocumentMaterializer()
    materialized = MaterializedDocument(
        local_path=str(temp_file),
        should_cleanup=True,
    )

    materializer.cleanup(materialized)

    assert not temp_file.exists()


def test_cleanup_does_not_remove_local_files(tmp_path):
    local_file = tmp_path / "local.pdf"
    local_file.write_bytes(b"pdf")
    materializer = DocumentMaterializer()
    materialized = MaterializedDocument(
        local_path=str(local_file),
        should_cleanup=False,
    )

    materializer.cleanup(materialized)

    assert local_file.exists()


def test_infer_document_extension_prefers_storage_key():
    ref = _s3_ref(
        storage_key="dev/documents/original/2026/06/abc-contract.pdf",
        original_filename="scan",
        content_type="image/png",
    )
    assert infer_document_extension(ref) == ".pdf"


def test_materialize_azure_blob_downloads_to_temp_file_with_pdf_extension(tmp_path):
    temp_dir = tmp_path / "documents"
    temp_dir.mkdir()
    payload = b"%PDF-1.4 mock"
    key = "documents/original/2026/06/abc-contract.pdf"

    blob_client = MagicMock()
    download = MagicMock()
    download.readall.return_value = payload
    blob_client.download_blob.return_value = download

    blob_service_client = MagicMock()
    blob_service_client.get_blob_client.return_value = blob_client

    materializer = DocumentMaterializer(
        azure_storage_account_name="lmprodev0001",
        azure_storage_container_name="documents",
        temp_dir=str(temp_dir),
        blob_service_client=blob_service_client,
    )
    materialized = materializer.materialize(_azure_blob_ref(storage_key=key))

    assert materialized.should_cleanup is True
    assert materialized.local_path.endswith(".pdf")
    assert Path(materialized.local_path).read_bytes() == payload
    blob_service_client.get_blob_client.assert_called_once_with(
        container="documents",
        blob=key,
    )


def test_materialize_azure_blob_requires_storage_account():
    materializer = DocumentMaterializer(
        azure_storage_account_name="",
        azure_storage_container_name="documents",
    )
    with pytest.raises(
        DocumentMaterializationError,
        match="AZURE_STORAGE_ACCOUNT_NAME is required",
    ):
        materializer.materialize(_azure_blob_ref())


def test_materialize_azure_blob_requires_container():
    materializer = DocumentMaterializer(
        azure_storage_account_name="account",
        azure_storage_container_name="",
    )
    with pytest.raises(
        DocumentMaterializationError,
        match="AZURE_STORAGE_CONTAINER_NAME is required",
    ):
        materializer.materialize(_azure_blob_ref())
