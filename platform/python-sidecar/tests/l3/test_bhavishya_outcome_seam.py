"""
NIRMĀṆA L3-W3 — `kala_bhavishya`'s recorded outcomes must survive a rebuild.

`outcome_recorded` / `outcome_notes` are the only columns in this table a WRITER CANNOT
REGENERATE: they record what actually happened, which is an observation of the world, not a
derivation from L1/L2. The writer hardcoded `False, None` into every row after a full per-chart
DELETE, so the first outcome anyone ever recorded would be destroyed by the next ordinary rebuild,
silently.

Measured when this landed: **200/200 rows `outcome_recorded = false`, 0 notes** — nothing is lost
today, and that is exactly why it is the right moment to fix it. MACRO_PLAN parks P7 with the
instruction that *"nothing in this programme may make the later loop harder"*; a rebuild that eats
outcomes is that.

Re-attachment is by `(signal_id, peak_date)` — not `id` (a sequence, so it moves every rebuild) and
not `projection_rank` (re-ranking moves it).
"""
from __future__ import annotations

import datetime as dt

import pytest

from pipeline.orchestrator.writers.ka_bhavishya_lekha import _reattach_outcome

PEAK = dt.date(2027, 10, 20)
SIG = "11111111-1111-4111-8111-111111111111"


def test_a_recorded_outcome_is_carried_onto_the_matching_projection() -> None:
    preserved = {(SIG, PEAK): (True, "married, as projected")}
    assert _reattach_outcome(preserved, SIG, PEAK) == (True, "married, as projected")


def test_the_entry_is_consumed_so_leftovers_are_detectable() -> None:
    """
    The consume is what makes the refusal possible: anything left after the rebuild is an outcome
    that could not be re-attached, i.e. data the DELETE destroyed.
    """
    preserved = {(SIG, PEAK): (True, "x")}
    _reattach_outcome(preserved, SIG, PEAK)
    assert preserved == {}, "a re-attached outcome must be consumed from the preserved map"


def test_an_unmatched_projection_gets_a_fresh_outcome_never_someone_elses() -> None:
    """Giving a new prediction someone else's outcome would be worse than losing one."""
    preserved = {(SIG, PEAK): (True, "belongs to a different projection")}
    other_date = dt.date(2028, 1, 1)
    assert _reattach_outcome(preserved, SIG, other_date) == (False, None)
    assert _reattach_outcome(preserved, "22222222-2222-4222-8222-222222222222", PEAK) == (False, None)
    # ...and the real entry is still there, so it will trip the refusal rather than vanish.
    assert preserved != {}


def test_a_null_signal_id_is_keyed_consistently() -> None:
    preserved = {(None, PEAK): (True, "no signal")}
    assert _reattach_outcome(preserved, None, PEAK) == (True, "no signal")


def test_uuid_objects_and_their_strings_key_the_same() -> None:
    """The DB returns UUID objects; the row builder may carry either. Both must match."""
    import uuid

    u = uuid.UUID(SIG)
    preserved = {(SIG, PEAK): (True, "recorded")}
    assert _reattach_outcome(preserved, u, PEAK) == (True, "recorded")


def test_the_writer_refuses_rather_than_dropping_an_unattachable_outcome() -> None:
    """Source-shape: the refusal must exist, and must not be a WriterResult.notes line (#1738)."""
    import inspect
    from pipeline.orchestrator.writers import ka_bhavishya_lekha as mod

    src = inspect.getsource(mod)
    assert "if preserved_outcomes:" in src
    assert "raise RuntimeError" in src[src.index("if preserved_outcomes:"):]
