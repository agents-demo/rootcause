"""Privacy filter for free-text operator notes before they enter a watch case."""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\+?\d[\d\s()./-]{7,}\d")
_HR = re.compile(r"\b(hr|human resources|salary|disciplinary|medical|sick note)\b", re.IGNORECASE)


def sanitize_note(text: str, *, max_length: int = 600) -> str:
    cleaned = _EMAIL.sub("[email redacted]", text or "")
    cleaned = _PHONE.sub("[phone redacted]", cleaned)
    if _HR.search(cleaned):
        cleaned = _HR.sub("[personal]", cleaned)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 1].rstrip() + "…"
    return cleaned
