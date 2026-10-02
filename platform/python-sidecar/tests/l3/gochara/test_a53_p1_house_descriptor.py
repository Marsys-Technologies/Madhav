"""A5.3 — AM-20 (ND-P1-FRAME), REVISED by Stream B's `P1_FRAME_ANSWER_v1_1` (steward M20261002T031247-e16e).

`house_from_frame` of a P1 transit record is the inclusive whole-sign count FROM THE LAGNA (Phaladīpikā XX.34
"the Bhava it represents when counted from the Lagna", XX.59) — a stored DESCRIPTOR only: no predicate, factor,
admission or channel reads it; P1 records stay unscored (`value_mapping_undeclared`). P1 transit-record MINTING is
gated on the applied schema carrying Stream B's additive migration 1233 (`period_anchor_lord`,
`period_anchor_level` — the anchor belongs in the natural key and no existing column can carry it): the named
switch `p1_minting_requires_period_anchor_columns`, read from the applied schema.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.record_verifier import verify_p1_house_descriptor
from services.gochara_rules import frames as rules_frames

from .test_a53_inventory import CHART, CHART_ID
from .test_a53_p1_support import GEN, _t, world  # noqa: F401  (fresh AM-5 database + P1 world)

SIDECAR = Path(__file__).resolve().parents[3]
CONTEXT = {"lagna_deg": CHART["lagna_deg"], "natal": CHART["natal"]}
SIGNS = rules_frames.SIGNS


def _p1_transit_edges():
    return [e for e in ev.enumerate_edges("marriage", "P1", CHART) if e.transit]


def _natal_idx(graha: str) -> int:
    return int(CHART["natal"][graha.title()] // 30)


# ── the resolver ─────────────────────────────────────────────────────────────────────────────────────

def test_the_dasha_lord_house_is_the_inclusive_count_from_the_lagna():
    house_for = writer_mod._house_resolver(CONTEXT, p1_minting=True)
    lagna_idx = int(CHART["lagna_deg"] // 30)
    edges = _p1_transit_edges()
    assert len(edges) == 31
    for e in edges:
        sign_no = int(e.obj.canonical_target.split(":")[1])
        assert house_for(e, SIGNS[sign_no - 1].lower()) == (sign_no - 1 - lagna_idx) % 12 + 1    # independent
    assert all((e.frame_kind, e.frame_arg) == ("dasha_lord", None) for e in edges)   # 1154: dasha_lord has no arg
    # the lord's NATAL sign is NOT the anchor (the superseded first reading): Saturn in Capricorn is the 10th
    # from the Aries lagna, not the 11th from natal Saturn in Pisces
    sat = next(e for e in edges if e.agent == "saturn" and e.obj.canonical_target == "span:10")
    assert house_for(sat, "capricorn") == 10 != (9 - _natal_idx("saturn")) % 12 + 1


def test_p1_occurrences_are_not_minted_unless_the_gate_is_open():
    closed = writer_mod._house_resolver(CONTEXT)                     # the default is CLOSED
    open_ = writer_mod._house_resolver(CONTEXT, p1_minting=True)
    e = _p1_transit_edges()[0]
    assert closed(e, "libra") is None and open_(e, "libra") is not None


def test_the_other_frames_are_unchanged_by_the_gate_and_the_natal_relation_stays_am15_lagna():
    for gate in (False, True):
        house_for = writer_mod._house_resolver(CONTEXT, p1_minting=gate)
        lagna_idx = int(CHART["lagna_deg"] // 30)
        p3 = next(e for e in ev.enumerate_edges("marriage", "P3", CHART) if e.transit)
        assert (p3.frame_kind, house_for(p3, "libra")) == ("lagna", (6 - lagna_idx) % 12 + 1)
        moon = next(e for e in ev.enumerate_edges("marriage", "P2", CHART) if e.transit)
        assert (moon.frame_kind, house_for(moon, "libra")) == ("moon", (6 - _natal_idx("moon")) % 12 + 1)


# ── nothing reads the descriptor ─────────────────────────────────────────────────────────────────────

def test_no_rule_module_and_no_p1_code_path_mentions_the_descriptor():
    rules = [p for p in (SIDECAR / "services" / "gochara_rules").glob("*.py")
             if "house_from_frame" in p.read_text()]
    assert rules == [], f"rule modules must not read the descriptor: {rules}"
    allowed = {"record_store.py", "window_store.py", "window_verifier.py", "window_sweep.py",
               "record_verifier.py"}
    users = {p.name for p in (SIDECAR / "services" / "gochara_kernel").glob("*.py")
             if "house_from_frame" in p.read_text()}
    assert users <= allowed, users - allowed
    # in the sweep the descriptor feeds exactly one thing: P2's Moon-frame direction (never P1)
    lines = [ln.strip() for ln in (SIDECAR / "services/gochara_kernel/window_sweep.py").read_text().splitlines()
             if "rec.house_from_frame" in ln]
    assert lines == ["return channel_for(p2_direction(rec.agent, rec.house_from_frame), event_class)"]


def _sweep_rec(house):
    from datetime import datetime, timezone
    d = lambda day: datetime(2025, 1, 1, tzinfo=timezone.utc).replace(day=day)       # noqa: E731
    return ws.SweepRecord(
        record_id="p1", root_id="r", path_id="P1", rule_version="1.0.0", relation="residence",
        object_kind="house_span", agent="venus", operator_role="scored", admission_state="admitted",
        supports=((d(2), d(20)),), canonical_target="span:7", house_from_frame=house,
        longitude_at=lambda t: 190.0)


def test_a_p1_window_does_not_depend_on_the_descriptor_at_all():
    rows = lambda p, v: ws.registry_factor_rows("P1", "1.0.0")                       # noqa: E731
    outs = []
    for house in range(1, 13):
        drafts, excluded = ws.draft_windows("marriage", [_sweep_rec(house)], rows)
        outs.append((drafts, excluded))
    assert all(o == outs[0] for o in outs[1:])
    (w,), _ = outs[0]
    assert w.score is None and w.severity is None                    # P1 stays unscored (value mapping undeclared)
    assert "value_mapping_undeclared" in str(w.unresolved)


def _dump(conn):
    """Everything a record stores EXCEPT the descriptor itself."""
    recs = conn.execute(
        "SELECT record_id::text, admission_state, temporal_support_state, temporal_support_intervals::text,"
        " evidence_for_occurrence, evidence_against_occurrence, outcome_valence_for_native, severity,"
        " frame_kind, frame_arg FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
        " ORDER BY record_id").fetchall()
    pre = conn.execute(
        "SELECT p.record_id::text, p.ordinal, p.predicate_id, p.predicate_rule_version, p.result"
        " FROM public.ka_gochara_record_prerequisite p JOIN public.ka_gochara_relationship_record r"
        " ON r.record_id = p.record_id WHERE r.path_id = 'P1' ORDER BY 1, 2").fetchall()
    return recs, pre


def _houses(conn):
    return [r[0] for r in conn.execute(
        "SELECT house_from_frame FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
        " ORDER BY record_id").fetchall()]


def _venus_libra(w):
    w.set_periods([(2, _t(1, 1), _t(2, 1))])
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])


def test_changing_the_descriptor_changes_nothing_else_a_record_stores_or_admits(world):
    w = world
    _venus_libra(w)
    real = writer_mod._house_resolver(CONTEXT, p1_minting=True)
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20), house_for=real)
    base, base_houses = _dump(w.conn), _houses(w.conn)
    assert base_houses == [7]                                         # Venus in Libra, counted from the Aries lagna
    for shift in (1, 5, 11):
        w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20),
                house_for=lambda e, s, _s=shift: (real(e, s) + _s - 1) % 12 + 1)
        assert _houses(w.conn) != base_houses                         # the descriptor DID change ...
        assert _dump(w.conn) == base                                  # ... and nothing else did
    assert all(r[4] is None and r[5] is None and r[7] is None for r in base[0])   # unscored: NULL, never 0.0
    assert {r[8:10] for r in base[0]} == {("dasha_lord", None)}


# ── the independent verifier ─────────────────────────────────────────────────────────────────────────

def test_the_verifier_rederives_the_descriptor_from_the_lagna_and_catches_a_lord_sign_count(world):
    w = world
    _venus_libra(w)
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20),
            house_for=writer_mod._house_resolver(CONTEXT, p1_minting=True))
    lagna_fact = w.conn.execute("SELECT fact_value_num FROM public.chart_facts WHERE fact_subject = 'LAGNA'"
                                ).fetchone()[0]
    assert int(float(lagna_fact) // 30) == int(CHART["lagna_deg"] // 30)   # the stub L1 facts ARE the fixture chart
    assert verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN,
                                      event_class="marriage") == {"records": 1}
    # the superseded first reading — counted from the period lord's natal sign (Venus, Sagittarius) — is caught
    venus_idx = _natal_idx("venus")
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20),
            house_for=lambda e, s: (SIGNS.index(s.title()) - venus_idx) % 12 + 1)
    with pytest.raises(RuntimeError, match="house-descriptor verification failed"):
        verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_the_verifier_has_nothing_to_check_when_nothing_was_minted(world):
    w = world
    assert verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN,
                                      event_class="marriage") == {"records": 0}


# ── the minting gate: p1_minting_requires_period_anchor_columns ──────────────────────────────────────

def _p1_record_count(conn):
    return conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
                        ).fetchone()[0]


def test_on_the_schema_without_1233_p1_is_not_minted_and_the_switch_is_named(world):
    w = world
    _venus_libra(w)
    assert writer_mod.P1_MINTING_GATE == "p1_minting_requires_period_anchor_columns"
    assert writer_mod.p1_minting_closed_reason(w.conn) == writer_mod.P1_MINTING_GATE
    res = w.step("record:marriage:P1")
    assert _p1_record_count(w.conn) == 0
    assert "P1 transit records NOT minted — p1_minting_requires_period_anchor_columns" in res.notes
    # the other paths are untouched by the gate
    assert "NOT minted" not in w.step("record:marriage:P3").notes


def test_the_gate_reads_the_applied_schema_and_a_writer_without_anchor_support_stays_closed(world, monkeypatch):
    """The columns are added to this DISPOSABLE database as a stand-in for 1233's DDL ONLY to exercise the
    switch (the real migration, its natural key and the anchored minting are the next step): present columns do
    NOT open the gate until the writer implements writing them — otherwise 1233 landing would silently turn on
    mis-keyed minting."""
    w = world
    _venus_libra(w)
    for col in ("period_anchor_lord", "period_anchor_level"):
        w.conn.execute(f"ALTER TABLE public.ka_gochara_relationship_record ADD COLUMN {col} text")
    assert writer_mod.RecordStore(w.conn).p1_anchor_columns_available() is True
    assert writer_mod.p1_minting_closed_reason(w.conn) == "p1_anchor_minting_not_implemented"
    assert "p1_anchor_minting_not_implemented" in w.step("record:marriage:P1").notes
    assert _p1_record_count(w.conn) == 0
    monkeypatch.setattr(writer_mod, "P1_ANCHOR_MINTING_IMPLEMENTED", True)
    assert writer_mod.p1_minting_closed_reason(w.conn) is None
    res = w.step("record:marriage:P1")
    assert res.rows_inserted > 0 and "NOT minted" not in res.notes, res.notes
    houses = _houses(w.conn)
    assert houses and all(1 <= h <= 12 for h in houses)
    verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_one_anchor_column_is_not_enough(world):
    w = world
    w.conn.execute("ALTER TABLE public.ka_gochara_relationship_record ADD COLUMN period_anchor_lord text")
    assert writer_mod.RecordStore(w.conn).p1_anchor_columns_available() is False
    assert writer_mod.p1_minting_closed_reason(w.conn) == writer_mod.P1_MINTING_GATE
