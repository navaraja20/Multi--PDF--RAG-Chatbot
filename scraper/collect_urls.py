from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def save_urls(urls: Iterable[str], file_path: str | Path) -> Path:
    """Persist a collection of URLs to a text file, one per line.

    Existing files are overwritten to keep the list authoritative.
    Whitespace-only or empty entries are ignored.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = [u.strip() for u in urls if u and u.strip()]
    path.write_text("\n".join(cleaned), encoding="utf-8")
    return path


def load_urls(file_path: str | Path) -> List[str]:
    """Load URLs from a text file, stripping whitespace and ignoring blanks."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"URL list not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


__all__ = ["save_urls", "load_urls"]
