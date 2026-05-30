import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from core import pdf_parser
from core.pdf_parser import (
    LOCAL_PDF_TEXT_SOURCE,
    parse_contract_pdf,
    parse_contract_pdf_with_metadata,
)
from generate_test_pdf import build_text_pdf_bytes  # type: ignore

SAMPLE_TEXT = (
    "CONTRATO DE SERVICIOS DE CONSULTORIA\n"
    "Clausula 3 - Honorarios: USD 8.000 mensuales.\n"
    "Clausula 6 - Ley aplicable: Republica Argentina."
)


def _write_pdf(tmp_path: Path, text: str, name: str = "contract.pdf") -> Path:
    path = tmp_path / name
    path.write_bytes(build_text_pdf_bytes(text))
    return path


def test_extracts_embedded_text_from_text_pdf(tmp_path):
    pdf_path = _write_pdf(tmp_path, SAMPLE_TEXT)

    result = parse_contract_pdf_with_metadata(str(pdf_path))

    assert "CONTRATO DE SERVICIOS" in result.text
    assert "Honorarios" in result.text
    assert result.model == LOCAL_PDF_TEXT_SOURCE
    assert result.usage == {}


def test_convenience_wrapper_returns_text_only(tmp_path):
    pdf_path = _write_pdf(tmp_path, SAMPLE_TEXT)
    text = parse_contract_pdf(str(pdf_path))
    assert "Ley aplicable" in text


def test_missing_pdf_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="PDF not found"):
        parse_contract_pdf_with_metadata(str(tmp_path / "nope.pdf"))


def test_wrong_extension_raises_value_error(tmp_path):
    path = tmp_path / "contract.txt"
    path.write_bytes(build_text_pdf_bytes(SAMPLE_TEXT))
    with pytest.raises(ValueError, match="Not a valid PDF"):
        parse_contract_pdf_with_metadata(str(path))


def test_empty_pdf_file_raises(tmp_path):
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"")
    with pytest.raises(ValueError, match="PDF file is empty"):
        parse_contract_pdf_with_metadata(str(path))


def test_corrupt_pdf_raises_not_valid(tmp_path):
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"%PDF-1.4\nthis is not really a pdf body")
    with pytest.raises(ValueError, match="Not a valid PDF"):
        parse_contract_pdf_with_metadata(str(path))


def test_scanned_pdf_without_text_is_rejected_clearly(tmp_path):
    # A valid PDF whose page carries no extractable text -> treated as scanned.
    pdf_path = _write_pdf(tmp_path, " ", name="scanned.pdf")
    with pytest.raises(ValueError, match="scanned or image-only"):
        parse_contract_pdf_with_metadata(str(pdf_path))


def test_oversized_pdf_is_rejected(tmp_path, monkeypatch):
    pdf_path = _write_pdf(tmp_path, SAMPLE_TEXT)
    monkeypatch.setenv("PDF_MAX_BYTES", "10")
    pdf_parser.load_pdf_limits.cache_clear()
    try:
        with pytest.raises(ValueError, match="PDF file is too large"):
            parse_contract_pdf_with_metadata(str(pdf_path))
    finally:
        pdf_parser.load_pdf_limits.cache_clear()


def test_ocr_fallback_seam_is_not_implemented(tmp_path):
    with pytest.raises(NotImplementedError):
        pdf_parser._ocr_pdf_fallback(tmp_path / "x.pdf")
