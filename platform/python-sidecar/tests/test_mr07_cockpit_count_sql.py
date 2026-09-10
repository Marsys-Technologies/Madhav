"""
tests/test_mr07_cockpit_count_sql.py — MR-07 gate: cockpit truth for production corpus.

GAP (PARISHKARA MR-07):
  ka_gochara's count_sql was fixed in MR-06 to scope to generation='3.0' on
  kala_gochara_windows_v2.

  ka_gochara_sweep's count_sql is STILL generation-blind:
    SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1

  This is semantically wrong: the cockpit reads this count as "rows owned by
  ka_gochara_sweep" but a generation-blind count would double-count any future v2/v3
  rows that land in kala_gochara_windows. The sweep (v1 writer) only ever wrote
  generation='v1' rows; the count_sql must reflect that.

REMEDIATION (what MR-07 implements):
  Scope ka_gochara_sweep's count_sql to generation='v1':
    SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'

  This is accurate: the sweep only wrote v1 rows. A generation-blind count is
  semantically misleading and risks double-counting once v3 rows exist.

WHAT THESE TESTS VERIFY (all offline/static, no DB required):
  1. ka_gochara_sweep count_sql is scoped to generation='v1'.
  2. ka_gochara count_sql is already scoped to generation='3.0' (MR-06 regression guard).
  3. ka_gochara_sweep count_sql is NOT generation-blind (bare WHERE chart_id=$1 form absent).
"""
from __future__ import annotations

import os
import re

# ── paths ────────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.dirname(_HERE)
_PLATFORM = os.path.dirname(_SIDECAR)

_SEED = os.path.join(_PLATFORM, "scripts", "seed", "asset_registry_seed.ts")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _extract_asset_block(src: str, asset_id: str) -> str:
    """Return the text of the seed object whose asset_id matches.

    Scans for the pattern `asset_id: '<asset_id>'` and returns everything from
    the preceding `{` to the matching `}` (first closing brace on its own line
    after the asset_id line). This is intentionally simple — the seed file is
    consistently formatted so this heuristic is sufficient.
    """
    pattern = rf"asset_id:\s*['\"]({re.escape(asset_id)})['\"]"
    m = re.search(pattern, src)
    if m is None:
        return ""
    # Walk back to find the opening brace of this object.
    start = src.rfind("{", 0, m.start())
    if start == -1:
        return ""
    # Walk forward to find the matching closing brace (depth-aware).
    depth = 0
    pos = start
    while pos < len(src):
        ch = src[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start : pos + 1]
        pos += 1
    return src[start:]


# ── Test 1: ka_gochara_sweep count_sql scoped to generation='v1' ─────────────

def test_ka_gochara_sweep_count_sql_scoped_to_v1():
    """ka_gochara_sweep count_sql must be scoped to generation='v1'.

    The sweep (v1 writer) only ever wrote generation='v1' rows to
    kala_gochara_windows. A generation-blind count would be semantically
    misleading: it would count ANY rows in kala_gochara_windows for the chart,
    not just the ones the sweep authored.

    MR-07 fixes this by scoping the count_sql:
      SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'
    """
    src = _read(_SEED)
    block = _extract_asset_block(src, "ka_gochara_sweep")
    assert block, "ka_gochara_sweep entry not found in asset_registry_seed.ts"

    assert re.search(
        r"count_sql\s*:.*generation\s*=\s*['\"]v1['\"]",
        block,
        re.DOTALL,
    ), (
        "ka_gochara_sweep count_sql must be scoped to generation='v1'. "
        "The sweep only wrote v1 rows; a generation-blind count is semantically wrong. "
        f"(found block: {block[:500]!r})"
    )


# ── Test 2: ka_gochara count_sql still scoped to generation='3.0' (MR-06 guard) ──

def test_ka_gochara_count_sql_scoped_to_3_0():
    """ka_gochara count_sql must reference generation='3.0' (MR-06 regression guard).

    MR-06 fixed ka_gochara's count_sql to scope to kala_gochara_windows_v2 with
    generation='3.0'. This test asserts that MR-07 does NOT regress that fix.
    This test should PASS even before the MR-07 green implementation, confirming
    the MR-06 fix is still in place.
    """
    src = _read(_SEED)
    block = _extract_asset_block(src, "ka_gochara")
    assert block, "ka_gochara entry not found in asset_registry_seed.ts"

    assert re.search(
        r"count_sql\s*:.*generation.*3\.0",
        block,
        re.DOTALL,
    ), (
        "ka_gochara count_sql must reference generation='3.0' (MR-06 fix must not regress). "
        f"(found block: {block[:500]!r})"
    )


# ── Test 3: ka_gochara_sweep count_sql is NOT generation-blind ───────────────

def test_ka_gochara_sweep_count_sql_not_blind():
    """ka_gochara_sweep count_sql must NOT be the bare generation-blind form.

    The generation-blind form is:
      SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1

    with no AND clause. This form is semantically wrong because it would count
    any row in kala_gochara_windows for the chart, not just the v1 rows that
    the sweep authored. After MR-07, the count_sql must include a generation
    filter so the bare form is gone.
    """
    src = _read(_SEED)
    block = _extract_asset_block(src, "ka_gochara_sweep")
    assert block, "ka_gochara_sweep entry not found in asset_registry_seed.ts"

    # Find the count_sql value within the block
    count_sql_match = re.search(
        r"count_sql\s*:\s*['\"]([^'\"]+)['\"]",
        block,
    )
    assert count_sql_match, (
        "ka_gochara_sweep block must have a count_sql field. "
        f"(found block: {block[:500]!r})"
    )
    count_sql_value = count_sql_match.group(1)

    # The blind form ends with WHERE chart_id=$1 (no AND generation=...)
    blind_pattern = re.compile(
        r"FROM\s+kala_gochara_windows\s+WHERE\s+chart_id=\$1\s*$",
        re.IGNORECASE,
    )
    assert not blind_pattern.search(count_sql_value), (
        "ka_gochara_sweep count_sql must NOT be the bare generation-blind form "
        "'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1'. "
        "After MR-07 it must include AND generation='v1'. "
        f"(found count_sql: {count_sql_value!r})"
    )
