from __future__ import annotations

from pathlib import Path
from typing import Optional


def docx_to_pdf(docx_path: str | Path, pdf_path: Optional[str | Path] = None) -> Path:
    """Convert a DOCX file to PDF using docx2pdf."""
    from docx2pdf import convert  # import lazily so the module is optional until needed

    docx_file = Path(docx_path)
    if pdf_path is None:
        pdf_file = docx_file.with_suffix(".pdf")
    else:
        pdf_file = Path(pdf_path)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    convert(str(docx_file), str(pdf_file))
    return pdf_file


__all__ = ["docx_to_pdf"]
