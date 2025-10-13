"""Utilities for working with PDF files.

This module provides helpers to extract images from PDF documents using
PyMuPDF (fitz), without relying on external system tools.
"""

from __future__ import annotations

from typing import Optional, Tuple


def extract_first_image_from_pdf_first_page(pdf_bytes: bytes) -> Optional[Tuple[str, bytes]]:
    """Extract the first embedded image from the first page of a PDF.

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        A tuple (ext, image_bytes) if an embedded image is found on page 1,
        where `ext` is the file extension reported by PyMuPDF (e.g., 'png', 'jpeg').
        Returns None if no embedded image is found.

    Raises:
        ImportError: If PyMuPDF (fitz) is not installed.
        Exception:   For any unexpected PDF parsing errors.
    """
    try:
        import fitz  # type: ignore  # PyMuPDF
    except Exception as exc:  # pragma: no cover - clear error path
        raise ImportError(
            "Dependência 'pymupdf' não instalada. Execute: pip install pymupdf"
        ) from exc

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.page_count < 1:
                return None
            page = doc.load_page(0)
            images = page.get_images(full=True)
            if not images:
                return None
            xref = images[0][0]
            img_dict = doc.extract_image(xref)
            image_bytes = img_dict.get("image")
            ext = img_dict.get("ext", "png")
            if not image_bytes:
                return None
            return ext, image_bytes
    except Exception:
        # Let the caller decide how to handle a generic failure
        raise


