"""Text extraction for uploaded documents.

Handles plain-text formats (.txt, .md, .csv) plus rich binary formats
(.pdf, .docx) and legacy Word (.doc). Every extractor is wrapped so a
single file failure surfaces a clear message instead of crashing the app.
"""

from __future__ import annotations

import io
import re
import sys
from typing import Optional

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".pdf", ".docx", ".doc"}


def extract_text(filename: str, data: bytes) -> str:
    """Return extracted plain text from *data* given *filename*.

    Raises ``ValueError`` (with a friendly message) if the file can't be
    read or the format isn't supported.
    """
    ext = _ext(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext or '(none)'}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )
    if ext in (".txt", ".md", ".csv"):
        return _read_plain_text(data)
    if ext == ".pdf":
        return _read_pdf(data)
    if ext == ".docx":
        return _read_docx(data)
    if ext == ".doc":
        return _read_doc(data)
    raise ValueError(f"Unsupported file type '{ext}'.")  # pragma: no cover


def _ext(filename: str) -> str:
    dot = str(filename).rfind(".")
    return str(filename)[dot:].lower() if dot >= 0 else ""


def _read_plain_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def _read_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ValueError(
            "PDF support requires 'pypdf'. Install it with: pip install pypdf"
        )
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages).strip() or "(PDF contained no extractable text.)"
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not read PDF file: {exc}")


def _read_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError:
        raise ValueError(
            "DOCX support requires 'python-docx'. Install it with: pip install python-docx"
        )
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not open DOCX file: {exc}")

    parts: list[str] = []
    for para in document.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in getattr(document, "tables", []):
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    text = "\n".join(parts).strip()
    if not text:
        # Fall back to raw content if the DOM yielded nothing.
        text = _read_plain_text(data)
    return text or "(DOCX contained no extractable text.)"


def _read_doc(data: bytes) -> str:
    """Read a legacy binary Word (.doc) document.

    Prefers Microsoft Word via COM on Windows when available, otherwise
    falls back to a best-effort text extraction from the OLE binary.
    """
    if sys.platform.startswith("win"):
        try:
            return _read_doc_with_word(data)
        except Exception:  # noqa: BLE001  (Word missing/COM unavailable)
            pass
    return _read_doc_ole(data)


def _read_doc_with_word(data: bytes) -> str:
    import tempfile
    import os

    import win32com.client  # pywin32

    word = win32com.client.Dispatch("Word.Application")
    try:
        word.Visible = False
        word.DisplayAlerts = 0
        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            doc = word.Documents.Open(tmp_path, ReadOnly=True)
            try:
                return doc.Content.Text or ""
            finally:
                doc.Close(False)
        finally:
            os.unlink(tmp_path)
    finally:
        word.Quit()
    return ""


def _read_doc_ole(data: bytes) -> str:
    """Best-effort extraction of readable text from a legacy .doc file.

    Legacy .doc stores text as UTF-16LE inside 'WordDocument' streams.
    We scan the binary for long runs of printable characters.
    """
    try:
        text = _extract_utf16_runs(data)
    except Exception:  # noqa: BLE001
        text = ""
    if not text.strip():
        # Raw .doc files sometimes embed a plain-text shadow stream.
        text = _extract_ascii_runs(data)
    return text.strip() or "(Could not extract text from this .doc file — try converting it to PDF or DOCX.)"


def _extract_utf16_runs(data: bytes) -> str:
    """Gather long runs of printable UTF-16LE characters."""
    # Decode as UTF-16LE with 'replace', then filter to printable runs.
    decoded = data.decode("utf-16-le", errors="replace")
    runs: list[str] = []
    current: list[str] = []
    for ch in decoded:
        if ch.isprintable() or ch in "\n\r\t":
            current.append(ch)
        else:
            if len("".join(current).strip()) >= 4:
                runs.append("".join(current).strip())
            current = []
    if len("".join(current).strip()) >= 4:
        runs.append("".join(current).strip())
    # Collapse internal whitespace and drop uninformative fragments.
    clean = [re.sub(r"[ \t]+", " ", r) for r in runs if any(c.isalpha() for c in r)]
    return "\n".join(clean)


def _extract_ascii_runs(data: bytes) -> str:
    ascii_blocks = re.findall(rb"[\x20-\x7e]{4,}", data)
    lines = []
    for block in ascii_blocks:
        text = block.decode("ascii", errors="ignore")
        if any(ch.isalpha() for ch in text):
            lines.append(text)
    return "\n".join(lines)


def extract_filename_only(name: str) -> str:
    """Return the bare filename (already just a name here, kept for clarity)."""
    return name
