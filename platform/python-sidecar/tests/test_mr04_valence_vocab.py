"""MR-04 — Valence vocabulary mapping gate (W0.1 static tests, no DB required).

PG-4: gochara_v3/engine.py emits 'favourable' | 'adverse' | 'mixed'.
      kala_gochara_windows schema (migration 460) requires 'gain' | 'loss' | 'neutral' | 'mixed'.
      ka_gochara.py was passing row["valence"] straight through — filters on 'gain' / 'loss'
      never matched any row, valence facets permanently broken.

FIX:  _VALENCE_MAP dict + helper applied at INSERT time in ka_gochara.py.

These tests parse the source text of ka_gochara.py; they require no running DB,
no imports from the writer, and no live chart data.
"""
from __future__ import annotations

import ast
import re
import pathlib

# Resolve the writer's source file relative to this test file's location.
_WRITER_PATH = (
    pathlib.Path(__file__).parent.parent
    / "pipeline" / "orchestrator" / "writers" / "ka_gochara.py"
)


def _source() -> str:
    return _WRITER_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1 — 'favourable' must not be a raw literal assigned to the valence column
# ---------------------------------------------------------------------------

def test_ka_gochara_writer_maps_favourable_to_gain():
    """The string 'favourable' must not appear as the direct value assigned to the
    DB valence column.  If a mapping is in place, the only legal appearances of
    'favourable' are as a key in the mapping dict (not as a value passed to INSERT).

    We check: the INSERT params dict does NOT contain a bare 'favourable' literal
    on the right-hand side of the 'valence' key assignment outside of a mapping
    structure.  We do this by asserting that a _VALENCE_MAP dict exists and that
    'favourable' is a key (not value) in it.
    """
    src = _source()

    # The canonical key must be 'gain' in the map (not 'favourable')
    # so 'favourable' -> 'gain' must appear in the source.
    assert "'favourable'" in src, (
        "Expected 'favourable' to appear as a mapping key in ka_gochara.py — "
        "not found at all; mapping may be missing."
    )

    # 'gain' must appear as the mapped output value.
    assert "'gain'" in src, (
        "Expected canonical DB value 'gain' to appear in ka_gochara.py — "
        "not found; _VALENCE_MAP mapping to 'gain' is missing."
    )


# ---------------------------------------------------------------------------
# Test 2 — 'adverse' must not be a raw literal assigned to the valence column
# ---------------------------------------------------------------------------

def test_ka_gochara_writer_maps_adverse_to_loss():
    """'adverse' must appear only as a mapping key, never as the value that lands
    in the DB column.  The mapping must translate it to 'loss'."""
    src = _source()

    assert "'adverse'" in src, (
        "Expected 'adverse' to appear as a mapping key in ka_gochara.py — "
        "not found; mapping may be missing."
    )

    assert "'loss'" in src, (
        "Expected canonical DB value 'loss' to appear in ka_gochara.py — "
        "not found; _VALENCE_MAP mapping to 'loss' is missing."
    )


# ---------------------------------------------------------------------------
# Test 3 — a named mapping constant (_VALENCE_MAP or equivalent) must exist
# ---------------------------------------------------------------------------

def test_canonical_valence_vocab_defined():
    """A named constant (dict or function) mapping engine vocab to DB vocab must
    be defined in ka_gochara.py.  Bare inline string literals are not acceptable
    per §N.4 (no bare string literal for canonical vocabulary).

    We accept: _VALENCE_MAP = {...} at module level, OR a named function
    whose name contains 'valence' and 'map' (case-insensitive).
    """
    src = _source()

    # Check for a module-level dict assignment whose name suggests a valence map.
    has_dict_constant = bool(re.search(r"_VALENCE_MAP\s*=\s*\{", src))

    # Alternatively a function definition carrying both keywords.
    has_fn_form = bool(re.search(
        r"def\s+\w*valence\w*map\w*\s*\(|def\s+\w*map\w*valence\w*\s*\(",
        src, re.IGNORECASE,
    ))

    assert has_dict_constant or has_fn_form, (
        "ka_gochara.py must define a named valence-vocabulary mapping constant "
        "(_VALENCE_MAP = {...}) or an equivalently named function.  "
        "Neither was found.  Bare string literals inside the INSERT params dict "
        "do not satisfy §N.4."
    )


# ---------------------------------------------------------------------------
# Test 4 — engine vocab terms must pass through the mapping, not land raw in DB
# ---------------------------------------------------------------------------

def test_engine_vocab_not_passed_raw():
    """The INSERT params dict must NOT directly assign row['valence'] without a
    mapping call.  Specifically, the line:

        "valence": row["valence"],

    must NOT appear verbatim in the source after the fix.  A mapping must be
    interposed, e.g.:

        "valence": _VALENCE_MAP.get(row["valence"], "neutral"),

    We detect the unfixed pattern and assert it is absent.
    """
    src = _source()

    # The unfixed pattern: "valence": row["valence"] (with optional whitespace)
    raw_passthrough_pattern = re.compile(
        r'"valence"\s*:\s*row\s*\[\s*["\']valence["\']\s*\]'
    )

    assert not raw_passthrough_pattern.search(src), (
        'ka_gochara.py still contains the raw pass-through: '
        '"valence": row["valence"]  — engine vocabulary is being written '
        "directly to the DB column without going through _VALENCE_MAP.  "
        "Apply the mapping before INSERT."
    )
