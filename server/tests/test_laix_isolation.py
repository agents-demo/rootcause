from __future__ import annotations

import ast
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "rootcause" / "laix"
FORBIDDEN_ROOTS = {
    "rootcause",
    "fastapi",
    "sqlite3",
    "numpy",
    "openjiuwen",
    "starlette",
    "uvicorn",
    "langchain",
    "openai",
    "anthropic",
}
NOUNS = ("rootcause", "factory", "case", "line")

# Every app-specific noun that is still allowed in executable code, with the reason it is frozen.
# The guard is a ratchet: a new name containing one of NOUNS fails until it is added here on purpose.
ALLOWED_DOMAIN_TERMS = {
    # v1 dataclass fields; ``Signal.as_generic()`` maps line_id -> subject, parameter -> kind.
    "line_id": "frozen Signal/FollowUp field",
    "case_id": "frozen FollowUp field and schema key",
    # "baseline" contains "line"; it is a quality metric frozen in the v1 contract.
    "baseline": "quality baseline value/field",
    "baseline_rate": "quality baseline rate field",
    # LAIX-Bench fixture vocabulary.
    "BenchCase": "bench fixture dataclass",
    "cases": "bench fixture function and report key",
    "case": "bench loop variable",
    "contract_cases": "bench fixture function",
    # Synthetic fixture values. The subject is intentionally a quality line.
    "line-6": "synthetic fixture subject",
    "line-6:hydrogen": "synthetic dedupe key",
    "warning-no-baseline": "synthetic case id",
    # Implementation keyword, not a domain noun.
    "default_factory": "dataclasses keyword",
    # Runtime strings frozen by the replay contract; changing them would change recorded decisions.
    "already actioned or already open for this line and parameter": "frozen policy reason",
    " follow-up case(s); the estimate is directional only. Match on line, defect and batch before treating it as an effect.": "frozen outcome note",
    " follow-up cases in a ": "frozen outcome note",
}


def python_files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def docstring_nodes(tree: ast.AST) -> set[int]:
    found: set[int] = set()
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, holders):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                found.add(id(body[0].value))
    return found


def executable_terms(tree: ast.AST) -> set[str]:
    """Identifiers and string literals, excluding docstrings and therefore comments."""
    docstrings = docstring_nodes(tree)
    terms: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            terms.add(node.id)
        elif isinstance(node, ast.Attribute):
            terms.add(node.attr)
        elif isinstance(node, ast.arg):
            terms.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            terms.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            terms.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            terms.add(node.value)
    return terms


def test_package_imports_no_host_or_agent_modules():
    offenders = []
    for path in python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots = [node.module.split(".")[0]]
            else:
                continue
            for root in roots:
                if root in FORBIDDEN_ROOTS:
                    offenders.append(f"{path.name}: {root}")
                assert root in sys.stdlib_module_names or root == "laix", f"{path.name}: non-stdlib import {root}"
    assert offenders == []


def test_non_stdlib_imports_are_only_stdlib():
    imported = set()
    for path in python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
    assert imported <= sys.stdlib_module_names, f"non-stdlib imports: {sorted(imported - sys.stdlib_module_names)}"


def test_domain_nouns_are_explicit_and_known():
    hits: set[str] = set()
    for path in python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for term in executable_terms(tree):
            if any(noun in term.lower() for noun in NOUNS):
                hits.add(term)
    unknown = sorted(hits - set(ALLOWED_DOMAIN_TERMS))
    assert unknown == [], "new domain noun(s) in portable code; name them in ALLOWED_DOMAIN_TERMS or remove them"
    # Keep the guard honest: the known app fields are still visible, not silently renamed.
    assert {"line_id", "case_id", "baseline"} <= hits


def test_adapter_stays_outside_the_portable_package():
    assert not (PACKAGE / "laix_adapter.py").exists()
    assert (PACKAGE.parent / "laix_adapter.py").is_file()
