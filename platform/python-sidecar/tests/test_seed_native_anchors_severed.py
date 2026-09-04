"""Guard: the hand-authored-anchor seed path stays severed (adjudication #1739, D-CND-08).

`seed_native_phala_anchors()` is a deployed SQL function that inserts hand-authored
predictions with hand-assigned confidence values into `phala_anchors` -- the L4 root
table -- where they are indistinguishable from derived ones. Its Python wrapper
`seed_native_anchors()` is kept (dropping a deployed DB object is deferred to Phase Z)
but every call site was removed.

Per §N.8, a severance nothing can prove is severed is not a severance: without this
test, the next person to add a call site meets no resistance at all.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # platform/
SIDECAR = REPO / "python-sidecar"
MCP_SRC = REPO.parent / "platform-mcp" / "src"

# The one file allowed to contain the definition.
DEFINITION_FILE = SIDECAR / "brahmagyan" / "phala" / "anchors.py"


def _python_sources() -> list[Path]:
    return [p for p in SIDECAR.rglob("*.py") if "node_modules" not in p.parts]


def test_no_python_call_site_invokes_the_seed_wrapper() -> None:
    """No Python file may CALL seed_native_anchors(...) -- mentions in prose are fine."""
    offenders: list[str] = []
    for path in _python_sources():
        if path.name == Path(__file__).name:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:                          # not ours to police
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (
                func.id if isinstance(func, ast.Name)
                else func.attr if isinstance(func, ast.Attribute)
                else None
            )
            if name in {"seed_native_anchors", "seed_native_phala_anchors"}:
                offenders.append(f"{path.relative_to(REPO)}:{node.lineno}")
    assert offenders == [], (
        "seed_native_anchors() must have no call sites (adjudication #1739). Found: "
        + ", ".join(offenders)
    )


def test_no_http_route_exposes_the_seed_path() -> None:
    """The FastAPI route was removed and must not come back."""
    for path in _python_sources():
        text = path.read_text(encoding="utf-8")
        # A decorator line, not a comment mentioning the removed route.
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not re.search(r"""@router\.(post|get)\(\s*["'][^"']*seed_anchors""", stripped), (
                f"{path.relative_to(REPO)} re-exposes a seed_anchors route (adjudication #1739)"
            )


def test_no_typescript_caller_reaches_the_seed_endpoint() -> None:
    """The MCP caller was removed; nothing may call the sidecar endpoint either."""
    offenders: list[str] = []
    for path in MCP_SRC.rglob("*.ts"):
        if "node_modules" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("*", "//", "/*")):   # prose, incl. the removal notice
                continue
            if "seedNativeAnchors" in stripped or "phala/seed_anchors" in stripped:
                offenders.append(f"{path.name}:{lineno}")
    assert offenders == [], (
        "no TypeScript caller may reach the seed path (adjudication #1739). Found: "
        + ", ".join(offenders)
    )


def test_the_wrapper_is_kept_and_marked_forbidden_to_repair() -> None:
    """Option 2 (dropping the object) is deferred to Phase Z, so the wrapper stays --
    but it must carry the notice that stops a well-meaning repair."""
    text = DEFINITION_FILE.read_text(encoding="utf-8")
    assert "def seed_native_anchors(" in text
    assert "DEPRECATED AND DELIBERATELY UNREACHABLE" in text
    assert "REPAIRING THIS IS FORBIDDEN" in text
    assert "#1739" in text
