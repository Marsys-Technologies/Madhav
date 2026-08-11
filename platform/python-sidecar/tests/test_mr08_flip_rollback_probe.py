"""
test_mr08_flip_rollback_probe.py — MR-08 static W0.1 interface gate.

PARIṢKĀRA MR-08: Versioned gochara flip/rollback/probe tooling.

GAP CLOSED (PG-30): Both real authority flips were performed via ad-hoc
one-off scripts not committed to git. MR-30 committed the canonical
operational scripts; MR-08 adds these static gate tests that verify the
scripts satisfy their interface contracts WITHOUT requiring a live DB or
network connection.

These are W0.1 (static) tests: they READ the script source text and
perform string / AST-level pattern matching. No subprocess execution,
no DB, no HTTP calls.

Live gate proof (actual rollback+re-flip execution transcript) is
recorded separately by the conductor after deployment as a PR comment.
"""
from __future__ import annotations

import pathlib
import re

# ---------------------------------------------------------------------------
# Resolve script paths relative to this test file
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]  # .../Madhav/pk-mr08
_GOCHARA_SCRIPTS = _REPO_ROOT / "platform" / "scripts" / "gochara"

_FLIP_PY     = _GOCHARA_SCRIPTS / "flip_authority.py"
_ROLLBACK_PY = _GOCHARA_SCRIPTS / "rollback_authority.py"
_PROBE_PY    = _GOCHARA_SCRIPTS / "probe_gochara.py"


# ===========================================================================
# Test 1: flip_authority.py exists
# ===========================================================================

def test_flip_authority_exists():
    """PG-30 gate: flip_authority.py must be committed at the expected path."""
    assert _FLIP_PY.exists(), (
        f"flip_authority.py not found at {_FLIP_PY}. "
        "MR-30 must commit this file before MR-08 gate can pass."
    )
    assert _FLIP_PY.is_file()


# ===========================================================================
# Test 2: flip_authority.py is chart-agnostic (no hardcoded chart UUID)
# ===========================================================================

_UUID_RE = re.compile(
    r"""['"]\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*['"]""",
    re.IGNORECASE,
)

# These UUIDs appear legitimately in docstrings/help text as EXAMPLES, not
# as hardcoded operational values.  We allow them in comments/docstrings but
# flag any UUID that appears outside a string that starts with 'e.g.'  or
# '(e.g.' — a simpler heuristic: count raw UUIDs in non-comment,
# non-example lines.
def _non_example_uuid_lines(source: str) -> list[str]:
    """Return source lines that contain a UUID but are not example/docstring lines."""
    bad = []
    for line in source.splitlines():
        stripped = line.strip()
        # Skip comments and docstring-style examples
        if stripped.startswith("#"):
            continue
        if "e.g." in stripped or "e.g " in stripped:
            continue
        if _UUID_RE.search(stripped):
            bad.append(line)
    return bad


def test_flip_authority_is_chart_agnostic():
    """
    flip_authority.py must NOT hardcode a specific chart UUID as an
    operational value — chart_id must come from --chart-id CLI arg.

    Example UUIDs in docstrings/help text ('e.g. 482012f1-...') are fine.
    A hardcoded UUID outside an example context is a PG-30 violation.
    """
    source = _FLIP_PY.read_text(encoding="utf-8")

    # Must declare --chart-id as a CLI argument (chart-agnostic design)
    assert "--chart-id" in source, (
        "flip_authority.py must declare --chart-id as a CLI argument. "
        "chart_id must be passed at runtime, not hardcoded."
    )

    # Must not contain operational hardcoded UUIDs outside example contexts
    bad_lines = _non_example_uuid_lines(source)
    assert not bad_lines, (
        "flip_authority.py contains hardcoded UUID(s) outside example/comment "
        f"context — PG-30 violation. Offending lines:\n"
        + "\n".join(f"  {ln}" for ln in bad_lines)
    )


# ===========================================================================
# Test 3: rollback_authority.py exists
# ===========================================================================

def test_rollback_authority_exists():
    """PG-30 gate: rollback_authority.py must be committed at the expected path."""
    assert _ROLLBACK_PY.exists(), (
        f"rollback_authority.py not found at {_ROLLBACK_PY}. "
        "MR-30 must commit this file before MR-08 gate can pass."
    )
    assert _ROLLBACK_PY.is_file()


def test_rollback_authority_is_chart_agnostic():
    """
    rollback_authority.py must:
    - Accept --chart-id as a CLI argument (not hardcoded)
    - Issue a parameterized DELETE on kala_gochara_authority scoped to chart_id
    """
    source = _ROLLBACK_PY.read_text(encoding="utf-8")

    assert "--chart-id" in source, (
        "rollback_authority.py must declare --chart-id as a CLI argument."
    )

    # The DELETE statement must reference kala_gochara_authority and
    # use a parameterized WHERE clause (not a hardcoded UUID literal in SQL).
    assert "DELETE" in source.upper() and "kala_gochara_authority" in source, (
        "rollback_authority.py must issue a DELETE on kala_gochara_authority."
    )

    # Verify the WHERE clause uses a parameter placeholder (%s), not a
    # literal UUID.  We look for the DELETE ... WHERE pattern.
    #
    # PARIṢKĀRA MR-08 regex-residual fix (2026-08-11): the original pattern
    # used a lazy-DOTALL `.*?` between "kala_gochara_authority" and "WHERE
    # chart_id = %s". With DOTALL, `.` matches newlines too, so the lazy
    # wildcard was free to cross straight through the end of the DELETE's
    # own SQL string, past the closing `cur.execute(...)` call, and pick up
    # an unrelated "WHERE chart_id = %s" belonging to a DIFFERENT statement
    # later in the file (e.g. the verify-deletion SELECT) — the match was
    # never actually anchored to the DELETE statement it claims to test.
    # Mutation-verified: stripping the WHERE clause from the DELETE itself
    # (an unscoped delete-all) still let the old pattern find a later,
    # unrelated "WHERE chart_id = %s" and wrongly PASS.
    #
    # Fix: drop DOTALL and restrict the gap to characters that cannot leave
    # the enclosing Python string literal (exclude `"` / `'`). This forces
    # the WHERE clause to be found within the SAME quoted SQL string as the
    # DELETE, not merely somewhere later in the file. (Same "\b / \w-aware
    # anchoring, not raw substring/wildcard" discipline as the precedent
    # word-boundary fix in test_ka_gochara_v3_mutation_guard.py — here the
    # anchor is the string-literal boundary rather than \b, since the defect
    # is statement-crossing, not token-substring collision.)
    delete_block_match = re.search(
        r"DELETE\s+FROM\s+kala_gochara_authority\b[^\"']*?WHERE\s+chart_id\s*=\s*%s",
        source,
        re.IGNORECASE,
    )
    assert delete_block_match is not None, (
        "rollback_authority.py must DELETE FROM kala_gochara_authority "
        "WHERE chart_id = %s (parameterized, not hardcoded), with the WHERE "
        "clause inside the SAME SQL string as the DELETE. "
        "Pattern 'DELETE FROM kala_gochara_authority ... WHERE chart_id = %s' "
        "not found within a single statement."
    )


# ===========================================================================
# Test 4: probe_gochara.py calls HTTP, not direct SQL
# ===========================================================================

def test_probe_gochara_calls_http_not_sql():
    """
    probe_gochara.py must probe the DEPLOYED MCP product via HTTP (not SQL).

    Per MR-08 design note: a SQL-only probe can pass even when the deployed
    MCP product is broken (wrong deployment, missing table access, runtime
    misconfiguration). The probe MUST use an HTTP client library.

    Positive assertions:
      - Uses urllib.request OR requests OR httpx for the probe call
      - Accepts --chart-id as a CLI argument

    Negative assertion:
      - Does NOT import psycopg (no direct DB connection in probe path)
    """
    source = _PROBE_PY.read_text(encoding="utf-8")

    # Must take chart_id via CLI
    assert "--chart-id" in source, (
        "probe_gochara.py must declare --chart-id as a CLI argument."
    )

    # Must use an HTTP client (stdlib urllib.request, or requests, or httpx)
    uses_http = any(token in source for token in (
        "urllib.request",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
    ))
    assert uses_http, (
        "probe_gochara.py must use an HTTP client library (urllib.request, "
        "requests, or httpx) to call the deployed MCP endpoint. "
        "No HTTP import found."
    )

    # Must NOT directly import psycopg for its probe path
    # (it is acceptable for psycopg to appear in comments, but not as an import)
    psycopg_import_lines = [
        ln for ln in source.splitlines()
        if re.match(r"\s*(import psycopg|from psycopg)", ln)
    ]
    assert not psycopg_import_lines, (
        "probe_gochara.py must NOT import psycopg. "
        "The probe must call the deployed MCP HTTP endpoint, not SQL directly. "
        f"Found psycopg import(s):\n"
        + "\n".join(f"  {ln}" for ln in psycopg_import_lines)
    )
