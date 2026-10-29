"""Backend connection settings for the JiuwenSwarm runtime.

Mirrors the coachme integration boundary: model/endpoint details live here, application logic
never imports provider details directly.
"""

from __future__ import annotations

import os

from .. import config


class ConfigError(RuntimeError):
    """Raised when the runtime is not configured."""


def model_provider() -> str:
    return os.getenv("MODEL_PROVIDER", "OpenAI")


def api_base() -> str:
    return os.getenv("API_BASE", "")


def api_key() -> str:
    return os.getenv("API_KEY", "")


def text_model_name() -> str:
    return os.getenv("MODEL_NAME", "")


def temperature() -> float:
    return float(os.getenv("LLM_TEMPERATURE", "0.2"))


def timeout() -> float:
    return float(os.getenv("LLM_TIMEOUT", "180"))


def verify_ssl() -> bool:
    return os.getenv("LLM_SSL_VERIFY", "true").strip().lower() in {"1", "true", "yes", "on"}


def max_iterations() -> int:
    return int(os.getenv("ROOTCAUSE_AGENT_MAX_ITERATIONS", "8"))


def token_budget() -> int:
    return int(os.getenv("ROOTCAUSE_AGENT_TOKEN_BUDGET", "0"))


def validate() -> None:
    missing = [k for k in ("API_KEY", "API_BASE", "MODEL_NAME") if not os.getenv(k)]
    if missing:
        raise ConfigError("Missing required environment variables: " + ", ".join(missing))


def available() -> bool:
    try:
        import openjiuwen  # noqa: F401

        return True
    except Exception:
        return False


def status() -> dict[str, object]:
    configured = available() and not any(not os.getenv(k) for k in ("API_KEY", "API_BASE", "MODEL_NAME"))
    if not available():
        detail = "openjiuwen is not installed in this runtime"
    elif not configured:
        detail = "MODEL_PROVIDER / API_BASE / API_KEY / MODEL_NAME are not configured"
    else:
        detail = "JiuwenSwarm DeepAgent runtime ready"
    return {
        "configured": configured,
        "available": available(),
        "backend": "openjiuwen",
        "detail": detail,
        "model": text_model_name(),
        "version": config.MODEL_VERSION,
    }
