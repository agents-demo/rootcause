"""JiuwenSwarm / openJiuwen runtime adapter, following the coachme integration pattern.

The deterministic evidence engine remains the source of truth for ranking and approvals. The LLM
runtime is given real case tools and produces a cited narrative or answer; it cannot approve, control
the line or invent evidence. If the runtime is not configured the API returns 503 instead of a fake
answer.
"""

from __future__ import annotations

import re
from typing import Any

from ..models import Scenario
from . import builder, runner, settings


class OpenJiuwenRuntime:
    backend = "openjiuwen"

    def __init__(self, scenarios: list[Scenario]) -> None:
        self.scenarios = {s.case.id: s for s in scenarios}

    def status(self):
        from .settings import status as settings_status

        result = settings_status()
        from .jiuwen_status import AgentStatus

        return AgentStatus(
            configured=bool(result["configured"]),
            available=bool(result["available"]),
            backend=str(result["backend"]),
            detail=str(result["detail"]),
            model=str(result.get("model", "")),
        )

    def _scenario(self, case_id: str | None) -> Scenario:
        if case_id and case_id in self.scenarios:
            return self.scenarios[case_id]
        return next(iter(self.scenarios.values()))

    @staticmethod
    def _citations(text: str) -> list[str]:
        return sorted(set(re.findall(r"\b(?:EV|H-EV|B-EV|E-EV)-\d+\b", text)))

    async def ask(self, question: str, *, case_id: str | None = None) -> dict[str, Any]:
        settings.validate()
        scenario = self._scenario(case_id)
        built = builder.build(scenario)
        prompt = (
            f"Case {scenario.case.id}: {scenario.case.defect_type}. Part {scenario.case.part}. "
            f"Question: {question}\n"
            "Use the tools. Cite evidence IDs. If the evidence does not answer it, say what is missing. "
            "Do not approve a cause and do not recommend line control."
        )
        result = await runner.run_agent(built.agent, prompt)
        answer = runner.output_text(result)
        return {
            "answer": answer,
            "citations": self._citations(answer),
            "backend": self.backend,
            "model": settings.text_model_name(),
            "case_id": scenario.case.id,
            "usage": runner.usage(result),
        }

    async def case_narrative(self, case_id: str) -> dict[str, Any]:
        question = (
            "Write a concise engineer narrative for this case: what happened, the leading causes with "
            "confidence, the evidence that supports or weakens them, and the next checks. Cite evidence IDs."
        )
        return await self.ask(question, case_id=case_id)
