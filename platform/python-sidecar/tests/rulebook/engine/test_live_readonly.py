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
