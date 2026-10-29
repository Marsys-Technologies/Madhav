"""Optional live check against the stored operands (read-only proxy). Skipped unless asked.

  RULEBOOK_ENGINE_LIVE_CHART_ID=<uuid> python3 -m pytest tests/rulebook/engine/test_live_readonly.py

Reads chart_facts / chart_dashas / charts / bg_sky_calendar over a read-only session, prints nothing
about the chart and asserts only structure (every operand the engine reads is present and unique).
"""

from __future__ import annotations

import os

import pytest

CHART = os.environ.get("RULEBOOK_ENGINE_LIVE_CHART_ID")
pytestmark = pytest.mark.skipif(not CHART, reason="set RULEBOOK_ENGINE_LIVE_CHART_ID to run against the read-only proxy")


def test_stored_operands_are_complete_and_the_session_is_read_only():
    from services.rulebook.engine import dbload
    from services.rulebook.engine.chart import readiness

    conn = dbload.connect_readonly()
    try:
        chart = dbload.load_chart(conn, CHART)
        sky = dbload.load_sky(conn)
        with pytest.raises(dbload.ReadOnlyViolation):
            conn.cursor().execute("DELETE FROM chart_facts")
    finally:
        conn.close()
    assert readiness(chart) == []
    assert all(v == 0 for v in sky.chain_defects.values())
    assert sky.coverage_end_jd is not None


def test_two_independent_sources_agree_at_the_birth_instant():
    """L0 ingress rows (sky calendar) and L1 natal signs are computed separately; at the birth
    instant they must give the same sign for the seven true grahas (checks the Lahiri alias,
    the sign vocabulary, the UTC->JD conversion and the IST birth instant in one go)."""
    from services.rulebook.engine import constants as K
    from services.rulebook.engine import dayatom, dbload
    from services.rulebook.engine.chart import utc_to_jd

    conn = dbload.connect_readonly()
    try:
        chart = dbload.load_chart(conn, CHART)
        sky = dbload.load_sky(conn)
    finally:
        conn.close()
    jd = utc_to_jd(dayatom.birth_utc(chart.birth))
    for g in K.GRAHAS:
        if g not in K.NODES:
            assert sky.sign_at(K.L0_BODY[g], jd) == chart.sign_of(g), g


def test_explicit_offset_path_accepts_a_real_ist_chart_and_its_stored_facts_pass_the_tripwires():
    """Feed the chart's own birth row back as a source record with the stated IST offset: the stated UT must equal the IST path's,
    and the stored L1 facts must pass the sky-sign and Vimshottari-start tripwires on real data."""
    from services.rulebook.engine import birthcheck, dayatom, dbload
    from services.rulebook.engine import birthrecord as B

    conn = dbload.connect_readonly()
    try:
        ist = dbload.load_chart(conn, CHART)
        rec = B.parse_birth_record(
            {
                "local_date": ist.birth.birth_date.isoformat(),
                "local_time": ist.birth.birth_time_local,
                "lat": ist.birth.lat,
                "lon": ist.birth.lon,
                "utc_offset_minutes": 330,
                "tz_iana": "Asia/Kolkata",
            }
        )
        resolved = B.resolve_birth(rec)
        chart = dbload.load_chart(conn, CHART, resolved)
        sky = dbload.load_sky(conn)
    finally:
        conn.close()
    assert resolved.utc == dayatom.birth_utc(ist.birth)
    assert birthcheck.utc_consistency_problems(chart, sky) == []
