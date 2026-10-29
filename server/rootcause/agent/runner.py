"""Runner lifecycle and output extraction, mirroring the coachme integration."""

from __future__ import annotations

from typing import Any

_started = False


async def start() -> None:
    global _started
    if _started:
        return
    from openjiuwen.core.runner import Runner

    try:
        await Runner.start()
    except Exception:
        pass
    _started = True


def output_text(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, dict):
        for key in ("output", "content", "answer", "result"):
            value = result.get(key)
            if isinstance(value, str):
                return value
        return str(result)
    return getattr(result, "content", None) or str(result)


def usage(result: Any) -> dict[str, Any]:
    data = result if isinstance(result, dict) else {}
    usage_data = data.get("usage") or data.get("usage_metadata") or getattr(result, "usage", None)
    if isinstance(usage_data, dict):
        return usage_data
    return {}


async def run_agent(agent: Any, query: str) -> Any:
    await start()
    from openjiuwen.core.runner import Runner

    return await Runner.run_agent(agent, {"query": query})
