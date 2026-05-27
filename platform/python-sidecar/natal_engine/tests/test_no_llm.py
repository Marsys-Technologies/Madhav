"""
test_no_llm.py — Enforces B.10 (no fabricated computation) at the import-grep level.

natal_engine/ must not import any LLM client SDK. The deterministic compute
path is sacrosanct. If a future change drags in anthropic / openai / vertexai
/ google.generativeai / cohere / etc., this test fails loudly.

Scope of the grep: the entire natal_engine/ package, including subpackages
(fixtures/, tests/), MINUS this test file itself (which references the
forbidden names in string form for the matcher).
"""

from __future__ import annotations

import re
from pathlib import Path

# Forbidden module names — top-level packages of common LLM client SDKs.
# Extend this list as new providers appear. Keep names lowercase.
FORBIDDEN_IMPORT_TOKENS: list[str] = [
    "anthropic",
    "openai",
    "google.generativeai",
    "vertexai",
    "cohere",
    "mistralai",
    "together",
    "deepseek",
    "ollama",
    "llama_index",
    "langchain",
]

# Regex matches:
#   import <token>
#   from <token>(.something)?
# with word boundaries so e.g. "openai" doesn't match "openairoute" (unlikely)
# and "anthropic" doesn't match "anthropic_lite" (also unlikely).
_IMPORT_RE_TEMPLATE = (
    r"^\s*(?:import\s+{tok}(?:\s|$|\.)"
    r"|from\s+{tok}(?:\.[a-zA-Z0-9_.]*)?\s+import\s+)"
)


def _scan_file(path: Path) -> list[tuple[str, int, str]]:
    """Return list of (token, line_no, line) hits in the file."""
    hits: list[tuple[str, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return hits

    for tok in FORBIDDEN_IMPORT_TOKENS:
        pattern = re.compile(
            _IMPORT_RE_TEMPLATE.format(tok=re.escape(tok)),
            re.MULTILINE,
        )
        for match in pattern.finditer(text):
            # Find line number
            line_no = text.count("\n", 0, match.start()) + 1
            line = text.splitlines()[line_no - 1]
            hits.append((tok, line_no, line))
    return hits


def test_no_llm_imports_anywhere_in_natal_engine() -> None:
    package_root = Path(__file__).resolve().parent.parent  # natal_engine/
    assert package_root.name == "natal_engine", (
        f"expected to be inside natal_engine/, got {package_root}"
    )

    self_path = Path(__file__).resolve()

    py_files = [p for p in package_root.rglob("*.py") if p.resolve() != self_path]
    assert py_files, "no .py files discovered under natal_engine/"

    all_hits: list[tuple[Path, str, int, str]] = []
    for f in py_files:
        for tok, lineno, line in _scan_file(f):
            all_hits.append((f.relative_to(package_root), tok, lineno, line))

    if all_hits:
        rendered = "\n".join(
            f"  {p} L{ln}: [{tok}] {line.strip()}"
            for p, tok, ln, line in all_hits
        )
        raise AssertionError(
            "B.10 violation — LLM client imports found in natal_engine/:\n"
            + rendered
        )
