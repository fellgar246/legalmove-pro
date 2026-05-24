import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pipeline.path_resolver import resolve_document_path


def test_resolve_document_path_uses_existing_absolute_path(tmp_path, monkeypatch):
    file_path = tmp_path / "contract.png"
    file_path.write_bytes(b"png")
    monkeypatch.setenv("UPLOADS_DIR", "")

    resolved = resolve_document_path(str(file_path))

    assert resolved == str(file_path.resolve())


def test_resolve_document_path_falls_back_to_uploads_dir(tmp_path, monkeypatch):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    stored = uploads_dir / "abc.png"
    stored.write_bytes(b"png")

    monkeypatch.setenv("UPLOADS_DIR", str(uploads_dir))

    resolved = resolve_document_path("./uploads/abc.png")

    assert resolved == str(stored.resolve())


def test_resolve_document_path_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))

    try:
        resolve_document_path("./uploads/missing.png")
        raised = False
    except FileNotFoundError as exc:
        raised = True
        assert "Document file not found" in str(exc)

    assert raised
