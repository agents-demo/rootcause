"""Notification routing, deduplication and signed webhook delivery."""

from __future__ import annotations

import hashlib
import hmac
import json
import urllib.request
from collections.abc import Iterable
from datetime import datetime, time
from typing import Any

from ..models import Notification, WatchCase


def build_notification(
    *,
    notification_id: str,
    watch: WatchCase,
    kind: str,
    severity: str,
    title: str,
    detail: str,
    now: datetime,
    role: str = "quality_manager",
) -> Notification:
    return Notification(
        id=notification_id,
        at=now.replace(microsecond=0).isoformat(),
        kind=kind,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title,
        detail=detail,
        watch_id=watch.id,
        role=role,
        delivered=True,
        read=False,
        dedup_key=f"{watch.group_key}:{kind}",
    )


def _field(n: Any, key: str, default: Any = None) -> Any:
    return n.get(key, default) if isinstance(n, dict) else getattr(n, key, default)


def dedupe(existing: Iterable[Notification | dict[str, Any]], candidate: Notification) -> bool:
    """True when the candidate should be suppressed."""
    return any(_field(n, "dedup_key") == candidate.dedup_key and not _field(n, "read", False) for n in existing)


def in_quiet_hours(now: datetime, quiet: str = "22:00-06:00") -> bool:
    try:
        start_s, end_s = quiet.split("-")
        start = time.fromisoformat(start_s)
        end = time.fromisoformat(end_s)
    except ValueError:
        return False
    current = now.time()
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def rate_limited(existing: Iterable[Notification | dict[str, Any]], *, max_per_shift: int, since: datetime) -> bool:
    recent = [n for n in existing if _parse(_field(n, "at", "1970-01-01T00:00:00+00:00")) >= since]
    return len(recent) >= max_per_shift


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sign_payload(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def deliver_webhook(url: str, payload: dict[str, Any], *, secret: str = "", timeout: float = 3.0) -> dict[str, Any]:
    """Deliver a signed JSON payload. The public demo's URL is intentionally invalid.

    A real site sets a Teams/Slack/automation webhook and a shared secret. Delivery failure never
    blocks the in-app notification or the case itself.
    """
    if not url or ".invalid" in url:
        return {"delivered": False, "mode": "in-app-only", "detail": "No usable webhook configured; in-app delivery only."}
    body = json.dumps({**payload, "sent_at": datetime.now().astimezone().replace(microsecond=0).isoformat()}, sort_keys=True).encode()
    headers = {"Content-Type": "application/json", "X-RootCause-Timestamp": str(int(datetime.now().timestamp()))}
    if secret:
        headers["X-RootCause-Signature"] = sign_payload(body, secret)
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"delivered": 200 <= response.status < 300, "status": response.status}
    except Exception as exc:
        return {"delivered": False, "mode": "in-app-only", "detail": f"{type(exc).__name__}: {exc}"}
