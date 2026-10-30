"""Run the agent evaluation and red-team case set against the configured model.

Usage, from the `server` directory:

    python evals/run_agent_eval.py

Requires model credentials (API_KEY / API_BASE / MODEL_NAME) in the environment or `.env`.
Writes a JSON report under `server/evals/reports/`. This is a real model run, not a fixture.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rootcause.agent.evaluation import run_live  # noqa: E402

REPORT_DIR = Path(__file__).resolve().parent / "reports"


async def main() -> int:
    report = await run_live()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_DIR / f"agent-eval-{stamp}.json"
    payload = {"generated_at": datetime.now(UTC).isoformat(), **report}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = report["summary"]
    print(f"model={summary['model']} backend={summary['backend']}")
    print(f"cases={summary['cases']} pass={summary['pass']} fail={summary['fail']}")
    print(
        f"citation_coverage={summary['citation_coverage']} "
        f"refusal_rate={summary['refusal_rate']} "
        f"guardrail_violations={summary['guardrail_violations']}"
    )
    print(f"latency={summary['latency_ms']}")
    for result in report["results"]:
        status = "PASS" if result["pass"] else "FAIL"
        print(f"  {status} {result['id']:<22} {result['latency_ms']} ms")
        for reason in result["reasons"]:
            print(f"       - {reason}")
    print(f"report: {path}")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
