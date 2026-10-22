"""OD-1 / D-FLIP F-10 — the candidate manifest pins `scored_until`; the input-vector verifier re-derives it.

The served surface (`serving_reader._scored_until`) marks a window past the scored edge `served_not_scored`, but only when the sealed manifest's input
vector pins the edge; without the pin the status is null with `scored_until_not_pinned`. The governed source of the edge is the evaluation protocol's
observation-mask end `gochara_eval.registry.H1` (2026-04-17, an INCLUSIVE IST calendar date; protocol v2.3 §1/§3; the same date the density report's
scored span ends on), so the exclusive edge is the IST midnight that follows it. Each claim below fails on its single planted reversion:

  C1 the pin is DERIVED from the registry's H1, at call time, on the builder's side and on the verifier's side — never a constant (CLAUDE.md §N.7.3)
     and the edge is the exclusive end (the day AFTER H1, IST midnight);
  C2 the writer's manifest substep pins it (real writer, real chain) and the serving reader reads exactly that pin back;
  C3 the serializer is additive (no key unless supplied) and refuses a value that is not an aware instant, never normalising it;
  C4 the independent verifier refuses a tampered pin, a pin that is missing where it is required, and accepts the true one;
  C5 the writer's live check binds the pin to the governed source, never to the stored vector (a forged or stripped pin drifts by name);
  C6 the verification job REQUIRES the pin of a candidate;
  C7 the D-FLIP F-10 readback: the reader, given the builder's pin, labels windows at or after the edge `served_not_scored`, before it `scored_horizon`.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from pipeline.orchestrator.writers import ContextSpec  # noqa: F401  (fixtures below build their own)
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_eval import registry as eval_registry
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import serving_reader as rd
from services.gochara_kernel import verification_job as vj

from .test_a53_am5_writer import am5, run  # noqa: F401  (the real-writer chain fixtures)
from .test_a53_inventory import CHART_ID

GEN = writer_mod.GENERATION
from .test_a53_input_vector import _ivv, _vector, db, ephe  # noqa: F401  (fixtures + helpers of the vector suite)
from .test_g8_class_census import ALL26, _JobConn

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
EDGE = "2026-04-18T00:00:00+05:30"          # the protocol's H1 = 2026-04-17 (inclusive IST day) → the exclusive edge is the next IST midnight


# ── C1: derived from the governed source, exclusive, never a constant ───────────────────────────────────────────────────

def test_c1_the_edge_is_the_ist_midnight_after_the_protocols_last_scored_day():
    assert eval_registry.H1 == dt.date(2026, 4, 17)                                           # the fact the density report's scored span ends on
    want = dt.datetime.combine(eval_registry.H1 + dt.timedelta(days=1), dt.time(), IST)       # protocol §3: inclusive IST dates → exclusive edge = next midnight
    assert dt.datetime.fromisoformat(iv.scored_until_instant()) == want
    assert dt.datetime.fromisoformat(ivv.derive_scored_until()) == want
    assert iv.scored_until_instant() == ivv.derive_scored_until() == EDGE


def test_c1_both_sides_follow_the_registry_they_hold_no_constant_of_their_own(monkeypatch):
    monkeypatch.setattr(eval_registry, "H1", dt.date(2030, 1, 31))                            # a different governed value moves BOTH derivations
    assert iv.scored_until_instant() == "2030-02-01T00:00:00+05:30"
    assert ivv.derive_scored_until() == "2030-02-01T00:00:00+05:30"


def test_c1_the_serving_reader_and_the_builder_name_the_same_vector_key():
    assert rd.SCORED_UNTIL_VECTOR_KEY == iv.SCORED_UNTIL_KEY == "scored_until"


# ── C3: the serializer ──────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", ["2026-04-18", "2026-04-18T00:00:00", "soon", 20260418, ["2026-04-18T00:00:00+05:30"]])
def test_c3_a_pin_that_is_not_an_aware_instant_is_refused_never_normalised(bad):
    with pytest.raises(iv.InputDrift, match="scored_until"):
        iv._scored_until_component(bad)


def test_c3_the_key_is_additive_via_the_real_builder(db, ephe):
    plain = _vector(db, str(ephe))
    pinned = _vector(db, str(ephe), scored_until=iv.scored_until_instant())
    assert "scored_until" not in plain                                                        # absent unless supplied: frozen vectors keep their digests
    assert pinned["scored_until"] == EDGE
    assert {k: v for k, v in pinned.items() if k != "scored_until"} == plain                  # nothing else moved


# ── C4: the independent verifier ────────────────────────────────────────────────────────────────────────────────────────

def test_c4_the_verifier_accepts_the_true_pin_and_refuses_a_tampered_or_missing_one(db, ephe):
    good = _vector(db, str(ephe), scored_until=iv.scored_until_instant())
    assert "scored_until" in _ivv(db, good, str(ephe), require_scored_until=True)["derived"]
    for tampered in ("2026-04-19T00:00:00+05:30",          # a shifted day
                     "2026-04-18T00:00:00+00:00",          # the zone changed: a different instant
                     "2027-04-18T00:00:00+05:30",
                     "2026-04-18",                         # not an instant at all
                     None, 7):
        with pytest.raises(RuntimeError, match="scored_until: independently derived"):
            _ivv(db, {**good, "scored_until": tampered}, str(ephe), require_scored_until=True)
    stripped = {k: v for k, v in good.items() if k != "scored_until"}
    with pytest.raises(RuntimeError, match="pins no scored edge"):                             # REQUIRED for a real candidate
        _ivv(db, stripped, str(ephe), require_scored_until=True)
    _ivv(db, stripped, str(ephe))                                                             # a vector that predates the key is judged only when it carries one
    with pytest.raises(RuntimeError, match="scored_until: independently derived"):            # ... and a tampered pin is refused even when not required
        _ivv(db, {**good, "scored_until": "2026-04-19T00:00:00+05:30"}, str(ephe))


# ── C2 / C5: the real writer on a real database ─────────────────────────────────────────────────────────────────────────

def _vec(conn):
    from services.gochara_kernel.inventory_store import InventoryStore
    return InventoryStore(conn).manifest_vector(CHART_ID, GEN)


def _set_pin(conn, pin):
    """Rewrite (or strip, pin=None) the candidate manifest's pin in place — a candidate manifest is still mutable."""
    vec = {k: v for k, v in _vec(conn).items() if k != "scored_until"}
    if pin is not None:
        vec["scored_until"] = pin
    conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = %s::jsonb WHERE chart_id = %s AND generation = %s",
                 (json.dumps(vec), CHART_ID, GEN))


def test_c2_the_writers_manifest_substep_pins_the_edge_and_the_serving_reader_reads_it_back(run):
    step, conn = run
    step(writer_mod.CONVENTION_SUBSTEP)
    step(writer_mod.MANIFEST_SUBSTEP)
    vector = _vec(conn)
    assert vector["scored_until"] == EDGE                                                     # pinned by the real manifest substep, not a fixture
    edge, reason = rd._scored_until(vector)                                                   # what the served surface does with the stored vector
    assert reason is None and edge == dt.datetime(2026, 4, 18, tzinfo=IST)


def test_c5_a_forged_or_stripped_pin_drifts_by_name_at_the_next_substep(run):
    step, conn = run
    step(writer_mod.CONVENTION_SUBSTEP)
    step(writer_mod.MANIFEST_SUBSTEP)
    step(writer_mod.SNAPSHOT_SUBSTEP)                                                         # positive control: the untouched candidate passes the live check
    _set_pin(conn, "2026-12-31T00:00:00+05:30")                                               # forged: the stored vector must not vouch for itself
    with pytest.raises(iv.InputDrift, match="scored_until"):
        step("inventory:marriage")
    _set_pin(conn, None)                                                                      # stripped: the live check expects the governed value
    with pytest.raises(iv.InputDrift, match="scored_until"):
        step("inventory:marriage")


# ── C6: the verification job ────────────────────────────────────────────────────────────────────────────────────────────

def test_c6_the_verification_job_requires_the_pin(monkeypatch):
    seen = {}

    def sentinel(conn, vec, **kw):
        seen["require_until"] = kw.get("require_scored_until")
        raise RuntimeError("sentinel: past the census")
    monkeypatch.setattr(ivv, "verify_inputs", sentinel)
    conn = _JobConn({"scored_classes": ALL26}, ALL26, ALL26)
    with pytest.raises(vj.VerificationRefused) as exc:
        vj.check_preconditions(conn, chart_id=CHART_ID, generation="5.0", ephe_path="/x", modules={"geometry": ()})
    assert exc.value.code == "stale_inputs" and seen["require_until"] is True


# ── C7: the D-FLIP F-10 readback ────────────────────────────────────────────────────────────────────────────────────────

def test_c7_windows_at_or_after_the_pinned_edge_read_served_not_scored(db, ephe):
    vector = _vector(db, str(ephe), scored_until=iv.scored_until_instant())
    edge, reason = rd._scored_until(vector)
    assert reason is None
    utc = dt.timezone.utc
    day = dt.timedelta(days=1)
    assert rd._scoring_status(edge - 3 * day, edge, edge, None)[0] == rd.SCORED_HORIZON                  # ends exactly at the edge (half-open): scored
    assert rd._scoring_status(edge - 3 * day, edge + day, edge, None)[0] == rd.STRADDLES_SCORED_EDGE
    assert rd._scoring_status(edge, edge + 3 * day, edge, None)[0] == rd.SERVED_NOT_SCORED              # starts at the edge: served, not scored
    assert rd._scoring_status(dt.datetime(2026, 4, 17, 18, 30, tzinfo=utc), dt.datetime(2026, 5, 1, tzinfo=utc), edge, None)[0] == rd.SERVED_NOT_SCORED
    unpinned_edge, unpinned_reason = rd._scored_until(_vector(db, str(ephe)))
    assert unpinned_edge is None and unpinned_reason == rd.REASON_SCORED_UNTIL_NOT_PINNED              # no pin: null with its reason, never a default
