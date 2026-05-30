import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from core import document_parser
from core.document_parser import (
    DOCUMENT_TYPE_IMAGE,
    DOCUMENT_TYPE_PDF,
    detect_document_type,
    parse_contract_document_with_metadata,
)
from core.image_parser import ImageParseResult
from core.pdf_parser import LOCAL_PDF_TEXT_SOURCE
from generate_test_pdf import build_text_pdf_bytes  # type: ignore

SAMPLE_TEXT = "CONTRATO\nClausula 1. Texto de prueba con contenido suficiente para parsear."


def test_detects_pdf_by_magic_bytes(tmp_path):
    path = tmp_path / "contract.pdf"
    path.write_bytes(build_text_pdf_bytes(SAMPLE_TEXT))
    assert detect_document_type(path) == DOCUMENT_TYPE_PDF


def test_detects_pdf_even_with_wrong_extension(tmp_path):
    path = tmp_path / "contract.bin"
    path.write_bytes(build_text_pdf_bytes(SAMPLE_TEXT))
    assert detect_document_type(path) == DOCUMENT_TYPE_PDF


def test_detects_image_by_extension(tmp_path):
    path = tmp_path / "contract.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n not really a png")
    assert detect_document_type(path) == DOCUMENT_TYPE_IMAGE


def test_unsupported_extension_raises(tmp_path):
    path = tmp_path / "contract.docx"
    path.write_bytes(b"PK\x03\x04 zip-like")
    with pytest.raises(ValueError, match="Unsupported document format"):
        detect_document_type(path)


def test_missing_document_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="Document not found"):
        parse_contract_document_with_metadata(str(tmp_path / "missing.pdf"))


def test_routes_pdf_to_local_extractor(tmp_path):
    path = tmp_path / "contract.pdf"
    path.write_bytes(build_text_pdf_bytes(SAMPLE_TEXT))

    result = parse_contract_document_with_metadata(str(path))

    assert result.model == LOCAL_PDF_TEXT_SOURCE
    assert "CONTRATO" in result.text


def test_routes_image_to_vision_parser(tmp_path):
    path = tmp_path / "contract.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n fake")

    expected = ImageParseResult(text="ocr text", model="gpt-4o", usage={"total_tokens": 5})
    with patch.object(
        document_parser,
        "parse_contract_image_with_metadata",
        return_value=expected,
    ) as image_parser_mock:
        result = parse_contract_document_with_metadata(str(path), client=None)

    image_parser_mock.assert_called_once()
    assert result is expected
