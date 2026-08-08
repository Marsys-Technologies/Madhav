"""
test_a1_producer_graha_subject_convergence.py — ADHIṢṬHĀNA Campaign A, Lane A1
================================================================================
`ga_condition_writer.py` (5 sites) and `ga_vargas_writer.py` (1 site) emitted
LONG-form graha names into `fact_subject` via a bare `graha.upper()` /
`floored_body.upper()` call, instead of the system-A short codes
(SUN/MOON/MAR/MER/JUP/VEN/SAT/RAH_MEAN/KET_MEAN/LAGNA) every other producer in
`ga_writers` uses. `ALL_GRAHAS` is Title-case ("Mars"), so `.upper()` produced
"MARS" — wrong — instead of "MAR". Rahu/Ketu are worse: "RAHU"/"KETU" instead
of the canonical "RAH_MEAN"/"KET_MEAN".

R19 (L1 stays sealed): this is a forward-only producer fix. No migration, no
backfill, no UPDATE against existing chart_facts rows — only the writer code
changes so future builds emit correctly.

DB-free: fake psycopg-shaped connections/cursors return canned rows so the
row-building helpers run without a real database, following the pattern
already established in test_ga_condition_savepoint_guard.py.
"""
from __future__ import annotations

import re
import sys
import pathlib
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_condition_writer import (  # noqa: E402
    _build_per_varga_avastha_rows,
    _build_d1_avastha_rows,
)

# System-A short codes (CLAUDE.md §B) — the only legal graha fact_subject forms.
SYSTEM_A_SHORT_CODES = {
    "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN", "LAGNA",
}

# Forbidden LONG-form values the defect used to emit (graha.upper() on Title-case names).
FORBIDDEN_LONG_FORMS = {
    "SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU",
} - {"SUN", "MOON"}  # SUN/MOON happen to be identical in both systems


class _FakeCursor:
    """Routes fetchall() results by a keyword match on the executed SQL text,
    mirroring the real queries in _load_graha_positions / _load_combustion_orbs
    / _build_per_varga_avastha_rows's chart_divisionals read."""

    def __init__(self, conn):
        self._conn = conn
        self._rows: list = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if "chart_facts" in sql:
            self._rows = self._conn.position_rows
        elif "bg_combustion_orbs" in sql:
            self._rows = self._conn.combustion_rows
        elif "chart_divisionals" in sql:
            self._rows = self._conn.divisional_rows
        else:
            self._rows = []
        return self

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, position_rows=None, combustion_rows=None, divisional_rows=None):
        self.position_rows = position_rows or []
        self.combustion_rows = combustion_rows or []
        self.divisional_rows = divisional_rows or []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        # _build_per_varga_avastha_rows calls conn.execute(...) directly
        # (not conn.cursor()) — mirror that shape too.
        cur = _FakeCursor(self)
        cur.execute(sql, params)
        return cur


def _assert_all_system_a(rows: list[dict], categories: set[str]) -> list[str]:
    """Return the fact_subject values emitted for the given fact_category set."""
    subjects = [
        r["fact_subject"] for r in rows if r["fact_category"] in categories
    ]
    assert subjects, f"no rows found for categories {categories} — fixture didn't reach the site"
    for s in subjects:
        assert s in SYSTEM_A_SHORT_CODES, (
            f"fact_subject={s!r} is not a system-A short code "
            f"(expected one of {sorted(SYSTEM_A_SHORT_CODES)})"
        )
        assert s not in FORBIDDEN_LONG_FORMS, (
            f"fact_subject={s!r} is a forbidden LONG-form graha name"
        )
    return subjects


# ── ga_condition_writer.py: lines ~1078 / ~1104 / ~1127 (Part A/B/C, per-varga) ──

def test_per_varga_avastha_rows_use_short_code_subjects():
    """Sites ~1078 (baladi), ~1104 (deeptaadi), ~1127 (Part C floors) — Mars must
    emit 'MAR', never 'MARS'."""
    conn = _FakeConn(
        divisional_rows=[
            ("Mars", "D9", "degree_in_sign", None, 15.0),
            ("Mars", "D9", "dignity", "own", None),
        ],
    )
    rows = _build_per_varga_avastha_rows(
        conn, "chart-1", str(uuid.uuid4()), "lahiri_chitrapaksha",
        "2026-08-08T00:00:00Z", "1.0",
    )

    baladi_subjects = _assert_all_system_a(rows, {"graha_avastha_baladi_per_varga"})
    assert "MAR" in baladi_subjects and "MARS" not in baladi_subjects

    deeptaadi_subjects = _assert_all_system_a(rows, {"graha_avastha_deeptaadi_per_varga"})
    assert "MAR" in deeptaadi_subjects and "MARS" not in deeptaadi_subjects

    # Part C floor rows run over ALL_GRAHAS (Sun..Ketu) regardless of varga_data —
    # this is where the Rahu/Ketu long-form defect is most visible.
    floor_categories = {
        r["fact_category"] for r in rows if r.get("fact_key") == "D_ALL"
    }
    floor_subjects = _assert_all_system_a(rows, floor_categories)
    assert "RAH_MEAN" in floor_subjects, floor_subjects
    assert "KET_MEAN" in floor_subjects, floor_subjects
    assert "RAHU" not in floor_subjects and "KETU" not in floor_subjects


# ── ga_condition_writer.py: lines ~1310 / ~1334 (D1 sayanadi / lajjitadi) ────────

def test_d1_avastha_rows_use_short_code_subjects():
    """Sites ~1310 (sayanadi) / ~1334 (lajjitadi) — ALL_GRAHAS iteration must
    emit system-A short codes, not Title-case.upper()."""
    conn = _FakeConn(
        position_rows=[
            ("MAR", "sign", "Aries", None),
            ("MAR", "degree_in_sign", None, 10.0),
            # Rahu/Ketu are the sharpest edge of the defect: bare .upper() on
            # Title-case "Rahu"/"Ketu" produces "RAHU"/"KETU", not the
            # canonical "RAH_MEAN"/"KET_MEAN" — a different code, not just a
            # different case.
            ("RAH_MEAN", "sign", "Gemini", None),
            ("RAH_MEAN", "degree_in_sign", None, 5.0),
        ],
    )
    rows = _build_d1_avastha_rows(
        conn, "chart-1", str(uuid.uuid4()), "lahiri_chitrapaksha",
        "2026-08-08T00:00:00Z", "1.0",
    )

    sayanadi_subjects = _assert_all_system_a(rows, {"graha_avastha_sayanadi"})
    assert "MAR" in sayanadi_subjects and "MARS" not in sayanadi_subjects

    lajjitadi_subjects = _assert_all_system_a(rows, {"graha_avastha_lajjitadi"})
    assert "MAR" in lajjitadi_subjects and "MARS" not in lajjitadi_subjects

    all_subjects = {r["fact_subject"] for r in rows}
    assert "RAH_MEAN" in all_subjects, all_subjects
    assert "RAHU" not in all_subjects


# ── ga_vargas_writer.py: ~line 3002 (floored-body scope-cap sentinel) ───────────
#
# FLOORED_BODIES = ["Uranus", "Neptune", "Pluto", "Lilith", "MC"] — none of
# these collide with a system-A graha today, so a value-level test at this
# site cannot observe a behavioral difference between `.upper()` and
# `PLANET_TO_SUBJECT.get(x, x.upper())` with current data (both produce
# "URANUS" etc.). The defect class is still real: a bare `.upper()` bypasses
# the canonical map entirely, so if a real graha name were ever added to
# FLOORED_BODIES it would silently mis-emit exactly like the ga_condition
# sites did. This asserts the fix routes through PLANET_TO_SUBJECT at the
# fact_subject construction site, and — value-level — that the mapping
# fallback used there is the correct one for a hypothetical canonical graha.

def test_ga_vargas_floored_body_fact_subject_routes_through_planet_to_subject():
    src_path = (
        pathlib.Path(__file__).resolve().parents[1]
        / "ga_writers" / "ga_vargas_writer.py"
    )
    src = src_path.read_text()

    # Isolate the scope-cap sentinel block (the FLOORED_BODIES loop), not the
    # unrelated `sentinel_key = f"{floored_body.upper()}_..."` dedup key a few
    # lines above it (not a fact_subject emission — out of this lane's scope).
    match = re.search(
        r'"fact_subject":\s*(.+?),\n',
        src[src.index("for floored_body in FLOORED_BODIES"):],
    )
    assert match, "could not locate the fact_subject assignment in the FLOORED_BODIES loop"
    expr = match.group(1).strip()

    assert expr != "floored_body.upper()", (
        "ga_vargas_writer.py's floored-body fact_subject still calls "
        "floored_body.upper() directly instead of routing through "
        "PLANET_TO_SUBJECT — same defect class as ga_condition_writer.py"
    )
    assert "PLANET_TO_SUBJECT" in expr, expr


def test_ga_vargas_imports_planet_to_subject():
    import ga_writers.ga_vargas_writer as gv

    assert hasattr(gv, "PLANET_TO_SUBJECT"), (
        "ga_vargas_writer must import the canonical PLANET_TO_SUBJECT mapping "
        "(from ga_writers.ga_positions_writer) rather than reimplementing "
        "graha-subject naming with a bare .upper()"
    )
    # Value-level check on the promoted mapping itself: a hypothetical real
    # graha routed through the same expression FLOORED_BODIES uses must
    # resolve to the system-A short code, not a bare .upper().
    assert gv.PLANET_TO_SUBJECT.get("Mars", "Mars".upper()) == "MAR"
    assert gv.PLANET_TO_SUBJECT.get("Rahu", "Rahu".upper()) == "RAH_MEAN"
    # Current FLOORED_BODIES entries are untouched (no key in the map — the
    # fallback still applies, so today's emitted values are unchanged).
    for body in gv.FLOORED_BODIES:
        assert gv.PLANET_TO_SUBJECT.get(body, body.upper()) == body.upper()
