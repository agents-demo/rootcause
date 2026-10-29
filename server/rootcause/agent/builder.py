"""Build a JiuwenSwarm DeepAgent for RootCause.

Follows the coachme pattern: a thin builder over openjiuwen.harness.create_deep_agent. The model
provider is wired once here; application code passes a scenario, prompt and tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models import Scenario
from . import settings, tools

SYSTEM_PROMPT = """You are RootCause, an evidence-first quality engineer for a factory.
Use the case tools before answering. Cite evidence IDs (EV-xx) for every material claim.
Never invent data. Never claim a cause is approved: the engineer decides.
The ranked cause list is the current evidence-weighted result. If you believe the evidence
supports a different order, say so explicitly as a disagreement and cite the evidence; do not
present a different cause as the leading result without that label.
Never control a line, change a setpoint, reject a part or hold a batch.
If the evidence is insufficient, say so and name what is missing.
Keep answers short and operational."""


@dataclass
class BuildResult:
    agent: Any
    tools: list[Any]


def _model() -> Any:
    from openjiuwen.core.foundation.llm import Model, ModelClientConfig, ModelRequestConfig

    client = ModelClientConfig(
        client_provider=settings.model_provider(),
        api_key=settings.api_key(),
        api_base=settings.api_base(),
        timeout=settings.timeout(),
        verify_ssl=settings.verify_ssl(),
    )
    request = ModelRequestConfig(
        model=settings.text_model_name(),
        temperature=settings.temperature(),
        top_p=0.9,
    )
    return Model(model_client_config=client, model_config=request)


def build(scenario: Scenario, *, system_prompt: str | None = None, max_iterations: int | None = None) -> BuildResult:
    from openjiuwen.harness import create_deep_agent

    settings.validate()
    case_tools = tools.make_tools(scenario)
    agent = create_deep_agent(
        model=_model(),
        system_prompt=system_prompt or SYSTEM_PROMPT,
        tools=case_tools,
        rails=[],
        enable_task_loop=False,
        max_iterations=max_iterations or settings.max_iterations(),
        workspace=None,
        parallel_tool_calls=False,
    )
    return BuildResult(agent=agent, tools=case_tools)
