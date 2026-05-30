"""
Generate text-based contract PDFs for local testing — no external dependencies.

Builds a minimal but valid PDF (with a correct xref table) whose pages carry
selectable, embedded text. Useful to exercise the native PDF path in the worker
without needing a real contract PDF or a PDF authoring library.

The ``build_text_pdf_bytes`` / ``write_text_pdf`` helpers are imported by the
unit tests, so they must stay dependency-free.

Usage:
    cd apps/worker-ai
    python scripts/generate_test_pdf.py
"""

from __future__ import annotations

from pathlib import Path

# Reuse the same fixture contracts the image generator uses, so PDF and image
# QA cover comparable content.
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from generate_test_images import (  # type: ignore
        PAIR1_AMENDMENT,
        PAIR1_ORIGINAL,
    )
except Exception:  # pragma: no cover - fallback if image script is unavailable
    PAIR1_ORIGINAL = "CONTRATO DE PRUEBA\nClausula 1. Texto original."
    PAIR1_AMENDMENT = "ENMIENDA DE PRUEBA\nArticulo 1. Texto modificado."


def _escape_pdf_text(text: str) -> str:
    """Escape characters that are special inside a PDF literal string."""
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _content_stream(lines: list[str]) -> bytes:
    """Build a page content stream that paints each line with Helvetica."""
    body = ["BT", "/F1 11 Tf", "12 TL", "50 760 Td"]
    if lines:
        body.append(f"({_escape_pdf_text(lines[0])}) Tj")
        for line in lines[1:]:
            body.append("T*")
            body.append(f"({_escape_pdf_text(line)}) Tj")
    body.append("ET")
    return ("\n".join(body)).encode("latin-1", errors="replace")


def build_text_pdf_bytes(text: str) -> bytes:
    """
    Build a single-page, text-based PDF as raw bytes with a valid xref table.

    The output is intentionally minimal but standards-compliant enough for
    ``pypdf`` to extract the embedded text reliably.
    """
    lines = text.splitlines() or [" "]
    content = _content_stream(lines)

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n"
        + content
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"

    xref_offset = len(out)
    count = len(objects) + 1
    out += f"xref\n0 {count}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")

    out += (
        f"trailer\n<< /Size {count} /Root 1 0 R >>\n".encode("ascii")
        + b"startxref\n"
        + f"{xref_offset}\n".encode("ascii")
        + b"%%EOF\n"
    )
    return bytes(out)


def write_text_pdf(text: str, output_path: Path) -> Path:
    """Write a text-based PDF to ``output_path`` and return the path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(build_text_pdf_bytes(text))
    return output_path


def main() -> None:
    output_dir = _SCRIPT_DIR.parent / "data" / "test_contracts"
    pairs = [
        (PAIR1_ORIGINAL, output_dir / "pair1_original.pdf", "Service Agreement (original)"),
        (PAIR1_AMENDMENT, output_dir / "pair1_amendment.pdf", "Service Agreement (amendment)"),
    ]
    print("Generating text-based test contract PDFs...")
    for text, path, title in pairs:
        write_text_pdf(text, path)
        print(f"  Created: {path}  ({title})")

    print("\nDone. Text-based PDFs created in data/test_contracts/")
    print("\nUsage example (no DB/worker, needs OPENAI_API_KEY):")
    print(
        "  PYTHONPATH=src python -m pipeline.cli "
        "--original-file-path data/test_contracts/pair1_original.pdf "
        "--amendment-file-path data/test_contracts/pair1_amendment.pdf"
    )


if __name__ == "__main__":
    main()
