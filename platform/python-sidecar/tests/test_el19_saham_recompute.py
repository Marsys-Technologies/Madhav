"""
test_el19_saham_recompute.py — EL-19 (Elevation Campaign v2.1, Lane β.D2).

Recompute-proof regression guard for the Tājaka sahams.

EL-19 in the register reads "Sahams — REACHABLE-BUT-EMPTY, never computed."
That premise is FALSE: the sahams ARE computed, by ga_sensitive_writer's
`_build_saham_rows` (70+ sahams, day/night formula variants, all 5 ayanamshas),
grounded to Tājaka Nīlakaṇṭhī (Tajik Neelakanthi) Ch.2, two_pass_verified, and
stored under fact_category **`saham_position`** (the census/`ganita_special_
lagnas_get` tool probe the bare name `saham`, which is a serving-layer alias
gap owned by α, not a compute gap). This test proves the compute is present
AND correct by independently recomputing two sahams (Puṇya and the wealth-
relevant Dhana that §0.2 flags) from the L1 graha longitudes and asserting an
exact match to the stored `saham_position` longitude on BOTH canonical charts.

Classical Tājaka saham formula: saham = (A - B + Lagna) mod 360, with the
(A, B) pair swapping between day-birth and night-birth (the row's own
`day_birth` flag selects the variant):
    Puṇya  day = Moon - Sun  + Asc      night = Sun - Moon + Asc
    Dhana  day = Jup  - Sun  + Asc      night = Jup - Moon + Asc
Both cite Tājaka Nīlakaṇṭhī Ch.2 (Tajik Neelakanthi).

DB-optional: skipped when DATABASE_URL is unset (CI without a live DB) or the
canonical rows are absent (a chart not yet built).
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg")
import psycopg  # noqa: E402

_DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("DIRECT_DATABASE_URL") or os.environ.get("POSTGRES_URL")

pytestmark = pytest.mark.skipif(not _DB_URL, reason="no DATABASE_URL — live-DB recompute check skipped")

_CHARTS = {
    "abhisek": "482012f1-710e-4a25-994a-93821f5871aa",
    "abhinandan": "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
}
_AYA = "lahiri_chitrapaksha"
# (subject, day-pair, night-pair) — base is always Asc; pairs are (lord, subtracted)
_SAHAMS = {
    "SAHAM_PUNYA": (("Moon", "Sun"), ("Sun", "Moon")),
    "SAHAM_DHANA": (("Jupiter", "Sun"), ("Jupiter", "Moon")),
}
_SUBJ = {"Sun": "SUN", "Moon": "MOON", "Jupiter": "JUP"}
_TOL_DEG = 1e-6


def _graha_longs(conn, chart_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_value_num FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
              AND fact_key = 'longitude_sidereal'
              AND fact_subject IN ('SUN', 'MOON', 'JUP', 'LAGNA')
            """,
            (chart_id, _AYA),
        )
        return {r[0]: float(r[1]) for r in cur.fetchall()}


def _saham_row(conn, chart_id, subject):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fact_key, fact_value_num, formula_provenance_text, verification_pass_status
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'saham_position'
              AND fact_subject = %s AND fact_key IN ('longitude_sidereal', 'day_birth')
            """,
            (chart_id, _AYA, subject),
        )
        out = {}
        prov = status = None
        for key, num, p, s in cur.fetchall():
            out[key] = float(num) if num is not None else None
            prov, status = p, s
        return out, prov, status


@pytest.fixture(scope="module")
def conn():
    c = psycopg.connect(_DB_URL)
    try:
        yield c
    finally:
        c.close()


@pytest.mark.parametrize("chart_name", list(_CHARTS))
@pytest.mark.parametrize("subject", list(_SAHAMS))
def test_saham_longitude_recomputes_exactly_from_l1(conn, chart_name, subject):
    chart_id = _CHARTS[chart_name]
    longs = _graha_longs(conn, chart_id)
    if "LAGNA" not in longs:
        pytest.skip(f"chart {chart_name} not built (no graha_position rows)")
    row, provenance, status = _saham_row(conn, chart_id, subject)
    if "longitude_sidereal" not in row:
        pytest.skip(f"{subject} not present for {chart_name}")

    day_birth = bool(row.get("day_birth"))
    day_pair, night_pair = _SAHAMS[subject]
    lord, sub = day_pair if day_birth else night_pair
    expected = (longs[_SUBJ[lord]] - longs[_SUBJ[sub]] + longs["LAGNA"]) % 360.0

    assert abs(row["longitude_sidereal"] - expected) < _TOL_DEG, (
        f"{subject} {chart_name}: stored {row['longitude_sidereal']} != "
        f"recomputed {expected} (day_birth={day_birth})"
    )
    # Grounding + verification tier must be intact.
    assert provenance and "Tajik Neelakanthi" in provenance
    assert status == "two_pass_verified"


def test_dhana_saham_present_both_charts(conn):
    """Dhana Saham is the wealth-relevant point §0.2 flags as missing — assert
    it is present and grounded on both canonical charts (it is not missing; it
    is stored under `saham_position`)."""
    for chart_name, chart_id in _CHARTS.items():
        longs = _graha_longs(conn, chart_id)
        if "LAGNA" not in longs:
            pytest.skip(f"chart {chart_name} not built")
        row, provenance, _ = _saham_row(conn, chart_id, "SAHAM_DHANA")
        assert row.get("longitude_sidereal") is not None, f"Dhana missing for {chart_name}"
        assert provenance and "Dhana" in provenance
