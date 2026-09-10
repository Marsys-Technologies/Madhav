"""
NIRMĀṆA L3-W3 finding M3 (§N.8, C12) — ka_graha_sancara's two real defects.

The asset carried `service_health = 'unhealthy'` with `selftest_detail` reading
"ephemeris computation failed: 0" — which is `str(KeyError(0))`.

DEFECT 1. `_read_from_bg_ephemeris` opened a bare cursor and indexed rows POSITIONALLY
(`row[0]`…`row[3]`), while the orchestrator's connection is `row_factory=dict_row`
(`pipeline/orchestrator/db.py:57`). Every row arrived as a dict, so `row[0]` raised
`KeyError: 0`. The repo already documents the same trap from the other side:
`brahmagyan/phala/muhurta.py` opens a deliberate tuple-row connection because its helper indexes
positionally. Fixed by pinning the row factory at the cursor and reading by column name, so the
function no longer depends on the caller's connection default in EITHER direction — that coupling
was the defect; positional indexing was only how it surfaced.

DEFECT 2, the subtler one. Self-test check 4 asserted the FORENSIC natal Moon sign (Aquarius)
against whatever path `get_ephemeris` took. With a db_conn that is PATH-A, which reads
`ephemeris_daily` — TROPICAL longitudes computed at **12:00 UT**. The anchor is the birth
INSTANT, 10:43 IST = 05:13 UT. The Moon moves ~13.18°/day, so the two moments are ~3.7° apart —
enough to cross the Aquarius/Pisces boundary, and it does. **The check had never been green on
the writer's real path**; its 19/19 passing tests fed PATH-A a tuple-returning mock with synthetic
longitudes. Under C12 that is a proposal, not a gate, and C12's remedy is to correct the check
with the derivation. It is now asked of the instant-precision path.
"""
from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from services.ka_graha_sancara import engine as engine_mod
from pipeline.orchestrator.writers import ka_graha_sancara as writer_mod

IST = timezone(timedelta(hours=5, minutes=30))
BIRTH_DT = datetime.fromisoformat("1984-02-05T10:43:00").replace(tzinfo=IST)


def test_stored_read_no_longer_indexes_rows_positionally() -> None:
    """Defect 1, guarded by shape. Comments are stripped: the fix's own comment quotes the bug."""
    source = "\n".join(
        line.split("#", 1)[0] for line in inspect.getsource(engine_mod._read_from_bg_ephemeris).splitlines()
    )
    assert "row[0]" not in source, "positional row indexing restored — breaks under dict_row"
    assert 'row["body"]' in source, "the stored read must address columns by name"


def test_stored_read_pins_its_own_row_factory() -> None:
    """
    The real fix. Reading by name is not enough on its own: the function must not depend on the
    caller's connection default, in either direction.
    """
    source = inspect.getsource(engine_mod._read_from_bg_ephemeris)
    assert "row_factory" in source and "dict_row" in source, (
        "the cursor must pin its row factory rather than inherit the connection's"
    )


def test_the_forensic_anchor_is_asked_of_the_instant_precision_path() -> None:
    """Defect 2. A birth-instant anchor cannot be asserted of a noon-computed daily table."""
    source = inspect.getsource(writer_mod)
    idx = source.index("Check 4: FORENSIC")
    block = source[idx:idx + 3000]
    assert "force_live=True" in block, (
        "the FORENSIC natal anchor must be evaluated against the live instant-precision path; "
        "ephemeris_daily is computed at 12:00 UT and yields Pisces for this 10:43 IST birth"
    )
    assert "evaluated_against" in block, "the check must record which path answered it"


def test_the_forensic_anchor_actually_holds_on_that_path() -> None:
    """
    The behavioural half — without it the guard above only proves a string is present.
    Live swisseph at the exact birth instant: Moon at ~324.48° sidereal = Aquarius.
    """
    result = engine_mod.get_ephemeris(
        dt=BIRTH_DT, ayanamsha="lahiri", db_conn=None, force_live=True
    )
    moon = result.grahas["Moon"]
    assert moon.sign == "Aquarius", (
        f"FORENSIC anchor broken: Moon computed as {moon.sign} at {moon.sidereal_lon_deg:.4f}°"
    )
    assert 300.0 <= moon.sidereal_lon_deg < 330.0, "Aquarius spans sidereal 300–330°"
    assert result.source == "swisseph_live"


def test_the_day_grade_path_is_still_checked_for_what_it_can_answer() -> None:
    """
    PATH-A is not excused by defect 2's fix — it is checked against its own contract. Otherwise
    correcting the anchor would have quietly removed the only check that touches the stored read,
    which is where defect 1 lived.
    """
    source = inspect.getsource(writer_mod)
    assert "day_grade_path_reads" in source, (
        "the stored-read path must retain a check of its own, or defect 1 becomes undetectable"
    )
