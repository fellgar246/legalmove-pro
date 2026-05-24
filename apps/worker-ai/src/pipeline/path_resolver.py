"""Resolve document storage paths for the worker."""

from __future__ import annotations

import os
from pathlib import Path

def resolve_document_path(storage_path: str) -> str:
    """
    Resolve a document storage_path to an existing file on disk.

    Tries the path as stored, then UPLOADS_DIR + basename for relative paths.
    """
    uploads_dir = os.getenv("UPLOADS_DIR", "")
    candidates: list[Path] = [Path(storage_path)]

    if not os.path.isabs(storage_path) and uploads_dir:
        candidates.append(Path(uploads_dir) / Path(storage_path).name)

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return str(candidate.resolve())

    raise FileNotFoundError(f"Document file not found: {storage_path}")
