"""
test_ph_muhurta_nakshatra_spelling.py -- SS N-471 (one canonical nakshatra spelling).

ph_muhurta used to resolve the natal-Moon nakshatra through two hand-typed dicts keyed on the OLD L1
spellings (Mrigashira / Mula) and read them with ``.get(name, 0)`` -- so a canonically spelled name
(Mrigasira / Moola), a stray spelling or any unknown name silently became 0 (Ashwini): a WRONG value
(CLAUDE.md §N.7 item 6: an honest null beats an invented judgment).

Now the lookup is the L0 lexicon (``brahmagyan.nakshatra_vocabulary``), tolerant of the canonical and the
old L1 spellings, honest-null (None) when chart_facts has no natal-Moon nakshatra, and FAILS LOUDLY
(ValueError, not swallowed by the read-failure handler) on a name that is none of the 27.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from brahmagyan.nakshatra_vocabulary import CANONICAL_NAKSHATRA_NAMES
from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter


def _conn(fetchone_return=None, execute_raises: Exception | None = None):
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchone.return_value = fetchone_return
    if execute_raises is not None:
        def _execute(sql, *a, **k):
            if "chart_facts" in str(sql):
                raise execute_raises
        cur.execute.side_effect = _execute
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


def _writer() -> PhMuhurtaWriter:
    return PhMuhurtaWriter.__new__(PhMuhurtaWriter)


@pytest.mark.parametrize(
    "number, name",
    [
        (5, "Mrigasira"), (5, "Mrigashira"),
        (19, "Moola"), (19, "Mula"),
        (23, "Dhanishtha"), (23, "Dhanishta"),
    ],
)
def test_both_spellings_resolve_for_ids_5_19_23(number, name):
    w = _writer()
    assert w._load_natal_moon_nakshatra_id(_conn((name,)), "c") == number
    assert w._load_natal_moon_nakshatra_idx(_conn((name,)), "c") == number - 1


def test_every_canonical_name_resolves_to_its_own_number():
    w = _writer()
    for i, name in enumerate(CANONICAL_NAKSHATRA_NAMES, start=1):
        assert w._load_natal_moon_nakshatra_id(_conn((name,)), "c") == i, name
        assert w._load_natal_moon_nakshatra_idx(_conn((name,)), "c") == i - 1, name


def test_forensic_anchor_purva_bhadrapada():
    """Moon = Purva Bhadrapada -> 25 (1-indexed) / 24 (0-based)."""
    w = _writer()
    assert w._load_natal_moon_nakshatra_id(_conn(("Purva Bhadrapada",)), "c") == 25
    assert w._load_natal_moon_nakshatra_idx(_conn(("Purva Bhadrapada",)), "c") == 24


@pytest.mark.parametrize("bad", ["Atlantis", "Abhijit", "Purva", "Mulaa", "Mrigashiraa", "27"])
def test_unknown_name_fails_loudly_never_ashwini(bad):
    w = _writer()
    with pytest.raises(ValueError, match="not one of the 27"):
        w._load_natal_moon_nakshatra_id(_conn((bad,)), "c")
    with pytest.raises(ValueError, match="not one of the 27"):
        w._load_natal_moon_nakshatra_idx(_conn((bad,)), "c")


def test_absent_fact_is_an_honest_none_not_zero():
    w = _writer()
    assert w._load_natal_moon_nakshatra_id(_conn(None), "c") is None
    assert w._load_natal_moon_nakshatra_idx(_conn(None), "c") is None
    assert w._load_natal_moon_nakshatra_idx(_conn((None,)), "c") is None


def test_db_read_failure_is_still_an_honest_none():
    w = _writer()
    conn = _conn(execute_raises=RuntimeError("db down"))
    assert w._load_natal_moon_nakshatra_id(conn, "c") is None
    assert w._load_natal_moon_nakshatra_idx(conn, "c") is None


def test_no_hand_typed_spelling_table_remains():
    assert not hasattr(PhMuhurtaWriter, "_NAKSHATRA_ID_1INDEXED")


def test_engine_echoes_none_not_zero_when_natal_moon_unavailable():
    from datetime import datetime
    from services.ph_muhurta.engine import MuhurtaContext, derive_muhurta_record

    ctx = MuhurtaContext(
        action_class="general", window_start=datetime(2026, 8, 1), window_end=datetime(2026, 8, 3),
        hora_lord="jupiter", panchanga_score=0.6, panchanga_snapshot={},
        classical_citation="test", condition_score=0.5, transit_score=0.5,
    )
    assert ctx.natal_moon_nakshatra_idx is None
    rec = derive_muhurta_record(ctx)
    assert rec.tarabala_chandrabala_jsonb["natal_moon_nakshatra_idx"] is None
