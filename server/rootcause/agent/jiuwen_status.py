"""Small status type shared by the API and tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentStatus:
    configured: bool
    available: bool
    backend: str
    detail: str
    model: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "available": self.available,
            "backend": self.backend,
            "detail": self.detail,
            "model": self.model,
        }
