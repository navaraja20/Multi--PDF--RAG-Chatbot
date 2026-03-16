from __future__ import annotations

import re
from typing import Iterable

_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_ALNUM_PUNCT_RE = re.compile(r"[^a-zA-Z0-9\s.,!?\'\"]+")


def _merge_fragments(lines: Iterable[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        if merged and cleaned == merged[-1]:
            continue
        merged.append(cleaned)
    return merged


def clean_text(raw_text: str) -> str:
    """Normalize whitespace and drop obvious noise from extracted text."""
    # Remove URLs and strip disallowed characters before paragraph assembly
    sanitized = _URL_RE.sub(" ", raw_text)
    sanitized = _ALNUM_PUNCT_RE.sub(" ", sanitized)

    # Replace runs of whitespace with single spaces inside lines
    lines = [_WHITESPACE_RE.sub(" ", part).strip() for part in sanitized.splitlines()]
    merged = _merge_fragments(lines)
    paragraphs: list[str] = []
    buffer: list[str] = []
    for line in merged:
        if len(line) < 2:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        buffer.append(line)
    if buffer:
        paragraphs.append(" ".join(buffer))
    return "\n\n".join(paragraphs)


__all__ = ["clean_text"]
