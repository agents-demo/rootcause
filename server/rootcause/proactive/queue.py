"""Bounded offline queue for edge sites.

The scheduler buffers samples and alert candidates during a network gap. The queue is bounded so a
long outage degrades to a digest instead of exhausting the box. Draining is idempotent by key.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OfflineQueue:
    max_items: int = 500
    items: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=500))
    dropped: int = 0

    def __post_init__(self) -> None:
        self.items = deque(maxlen=max(1, self.max_items))

    def push(self, item: dict[str, Any], *, key: str) -> bool:
        for existing in self.items:
            if existing.get("key") == key:
                return False
        if len(self.items) >= self.max_items:
            self.items.popleft()
            self.dropped += 1
        self.items.append({**item, "key": key})
        return True

    def drain(self) -> list[dict[str, Any]]:
        out = list(self.items)
        self.items.clear()
        return out

    def summary(self) -> dict[str, Any]:
        return {"queued": len(self.items), "dropped": self.dropped, "max_items": self.max_items}
