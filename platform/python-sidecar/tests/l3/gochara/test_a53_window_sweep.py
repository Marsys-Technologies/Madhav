"""A5.3 — the window sweep (design v1.5; steward rulings M20261002T001617-5a34 / -dd2f).

Everything asserted here is the OUTPUT of `window_sweep` (and of the production registry / valence
code it calls); no rule is re-implemented in a test. Two registry states are exercised on purpose
(ruling 3): today's `activity_kernel@1.0.0` row (declares no applicability — every record's
operand is unevaluable, hence unqualified) and a row that DECLARES applicability (the shape of the
1.1.0 row, supplied by `_with_applicability` from the real 1.0.0 row; replaced by the real 1.1.0
row once Stream B's registry change is on main — see the skip-guarded test at the bottom).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.window_sweep import SweepRecord, SweepRefusal
from services.gochara_rules import registry as reg

UTC = timezone.utc
T0 = datetime(2010, 1, 1, tzinfo=UTC)


def _d(days: float) -> datetime:
    return T0 + timedelta(days=days)


def _rec(rid, *, root=None, path="P3", version="1.0.0", relation="residence", kind="sign_span",
         agent="jupiter", role="scored", admission="admitted", supports=((0, 10),), **kw):
    return SweepRecord(
        record_id=rid, root_id=root or f"root-{rid}", path_id=path, rule_version=version,
        relation=relation, object_kind=kind, agent=agent, operator_role=role,
        admission_state=admission,
        supports=tuple((_d(a), _d(b)) for a, b in supports), **kw)


def _with_applicability(rows, *, orb=None):
    """The REAL factor rows plus the applicability block the 1.1.0 row declares (AM-13): spans →
    membership step; points → angular with the row's own orb (None = ND-ORB open)."""
    out = []
    for row in rows:
        row = dict(row)
        if row["factor_id"] == "activity_kernel":
            row["applicability"] = {
                "span": {"object_kinds": ["sign_span", "house_span", "star"], "function": "step",
                         "inside": 1.0, "outside": 0.0},
                "angular": {"object_kinds": ["degree_point", "derived_point", "saham", "house_lord"],
                            "function": "linear", "orb_deg": orb},
            }
        elif row["factor_id"] == "graduated_drishti":
            row["applicability"] = {"relations": ["aspect"]}
        out.append(row)
    return out


def _rows_1_0_0(path, version):
    return ws.registry_factor_rows(path, version)


def _rows_declared(path, version, orb=None):
    return _with_applicability(ws.registry_factor_rows(path, version), orb=orb)


def _draft(records, rows_for=_rows_1_0_0, cls="marriage", **kw):
    return ws.draft_windows(cls, records, rows_for, **kw)


# ── union / admission ────────────────────────────────────────────────────────

def test_abutting_half_open_supports_are_one_window():
    comps = ws.union_components([(_d(0), _d(5)), (_d(5), _d(9)), (_d(20), _d(30))])
    assert comps == [(_d(0), _d(9)), (_d(20), _d(30))]


def test_overlapping_and_nested_supports_merge():
    assert ws.union_components([(_d(0), _d(10)), (_d(2), _d(4)), (_d(9), _d(12))]) == [(_d(0), _d(12))]


def test_inverted_support_refused():
    with pytest.raises(SweepRefusal):
        ws.union_components([(_d(5), _d(5))])


def test_window_interval_is_the_union_no_clipping_no_threshold():
    recs = [_rec("a", supports=((0, 40),)), _rec("b", supports=((40, 41),), root="rb")]
    drafts, _ = _draft(recs, _rows_declared)
    assert [d.interval for d in drafts] == [(_d(0), _d(41))]
    assert drafts[0].record_ids == ("a", "b")


def test_exclusion_ledger_accounts_every_non_member():
    recs = [
        _rec("ok"),
        _rec("tm", role="testimony"),
        _rec("na", admission="not_admitted"),
        _rec("uq", admission="unqualified"),
        _rec("ns", supports=()),
    ]
    drafts, excluded = _draft(recs, _rows_declared)
    assert excluded == {"not_admitted": 1, "admission_unqualified": 1, "testimony": 1, "no_support": 1}
    assert [d.record_ids for d in drafts] == [("ok",)]


def test_a_grain_is_one_path_version():
    with pytest.raises(SweepRefusal):
        _draft([_rec("a"), _rec("b", path="P4")])


def test_paths_without_a_sweep_refuse_loudly():
    with pytest.raises(SweepRefusal):
        _draft([_rec("a", path="P5")])


def test_a_factor_with_no_evaluator_refuses_never_skips():
    rows = _rows_declared("P3", "1.0.0") + [{"factor_id": "yoga_strength", "null_state": "unqualified"}]
    with pytest.raises(SweepRefusal):
        _draft([_rec("a")], lambda p, v: rows)


# ── registry state 1: today's rows (no applicability) ────────────────────────

def test_today_registry_every_p3_p4_record_is_unqualified_and_the_window_says_so():
    for path in ("P3", "P4"):
        drafts, _ = _draft([_rec("a", path=path, supports=((0, 30),))])
        (w,) = drafts
        assert w.interval == (_d(0), _d(30))
        assert (w.score, w.evidence_for, w.evidence_against, w.peak_instant) == (None, None, None, None)
        assert w.severity is None                       # a named null, never 0
        assert w.outcome_valence_for_native == "unqualified"
        assert w.null_states_used == ["unqualified"]
        assert w.unresolved == {"applicability_undeclared": 1}
        assert w.qualified_members == 0 and w.members == 1


# ── registry state 2: a row that declares applicability ──────────────────────

def test_declared_span_residence_is_a_step_one_and_peaks_at_the_earliest_instant():
    recs = [_rec("late", root="r2", supports=((20, 30),)), _rec("early", root="r1", supports=((5, 15),)),
            _rec("bridge", root="r3", supports=((15, 20),))]
    (w,), _ = _draft(recs, _rows_declared)
    assert w.interval == (_d(5), _d(30))
    assert w.score == 1.0
    assert w.peak_instant == _d(5)                      # earliest instant of the max on a plateau
    assert w.peak_instant in [w.interval[0]] or w.interval[0] <= w.peak_instant < w.interval[1]
    assert w.severity is None


def test_declared_state_p4_residence_span_qualifies():
    (w,), _ = _draft([_rec("a", path="P4", agent="saturn", supports=((0, 100),))], _rows_declared)
    assert w.score == 1.0 and w.null_states_used == []


def test_evidence_is_a_sum_over_roots_of_the_per_root_max_never_netted():
    recs = [
        _rec("a1", root="R1", supports=((0, 10),)),
        _rec("a2", root="R1", supports=((0, 10),)),      # same root: max, not sum
        _rec("b1", root="R2", supports=((0, 10),)),      # another root: adds
        _rec("c1", root="R3", supports=((10, 20),)),     # not live at the peak (t=0)
    ]
    (w,), _ = _draft(recs, _rows_declared)
    assert w.peak_instant == _d(0)
    assert w.evidence_for == 2.0
    assert w.evidence_against == 0.0                    # an evaluated empty sum on a qualified window
    assert w.score == 1.0


def test_valence_is_the_class_polarity_verdict_at_the_peak_never_copied():
    from services.gochara_rules.valence import compute_valence
    recs = [_rec("a", supports=((0, 10),))]
    for cls in ("marriage", "bereavement"):
        (w,), _ = _draft(recs, _rows_declared, cls=cls)
        want = compute_valence(cls, 1.0, 0.0, None).outcome_valence_for_native
        assert w.outcome_valence_for_native == want
    (a,), _ = _draft(recs, _rows_declared, cls="bereavement")
    (b,), _ = _draft(recs, _rows_declared, cls="marriage")
    assert a.outcome_valence_for_native != b.outcome_valence_for_native


def test_declared_aspect_record_without_the_drishti_source_is_a_named_missing_input():
    (w,), _ = _draft([_rec("a", relation="aspect", supports=((0, 10),))], _rows_declared)
    assert w.score is None and w.outcome_valence_for_native == "unqualified"
    assert w.unresolved == {"graduated_drishti_source_not_landed": 1}


def test_declared_residence_is_not_an_aspect_so_drishti_is_not_applicable_never_1_by_default():
    rows = _rows_declared("P3", "1.0.0")
    prog = ws.build_program(_rec("a"), rows)
    assert [o.kind for o in prog.outcomes] == ["const", "na"]
    assert prog.qualified and prog.value_at(_d(1)) == 1.0


def test_drishti_is_called_through_the_supplied_source_for_aspect_records_only():
    calls = []

    def source(agent, offset):          # stands for Stream B's drishti.graduated_drishti
        calls.append((agent, offset))
        return {7: 1.0, 5: 0.5}[offset]

    rec = _rec("a", relation="aspect", agent="jupiter", supports=((0, 10),),
               aspect_offset_at=lambda t: 5)
    (w,), _ = _draft([rec], _rows_declared, drishti=source)
    assert w.score == 0.5 and calls and set(calls) == {("jupiter", 5)}
    assert w.peak_instant == _d(0)


def test_drishti_offset_undeterminable_makes_that_record_unqualified():
    rec = _rec("a", relation="aspect", supports=((0, 10),), aspect_offset_at=lambda t: None)
    (w,), _ = _draft([rec], _rows_declared, drishti=lambda a, o: 1.0)
    assert w.score is None


def test_point_record_orb_not_ratified_is_unqualified_and_a_caller_orb_is_not_accepted():
    rec = _rec("a", relation="conjunction", kind="house_lord", supports=((0, 10),),
               delta_lambda_at=lambda t: 0.0)
    (w,), _ = _draft([rec], _rows_declared)              # orb_deg None in the declared row
    assert w.score is None and w.unresolved == {"orb_not_ratified": 1}


def test_point_record_without_a_delta_lambda_source_is_a_named_missing_operand():
    rec = _rec("a", relation="conjunction", kind="house_lord", supports=((0, 10),))
    (w,), _ = _draft([rec], lambda p, v: _rows_declared(p, v, orb=5.0))
    assert w.unresolved == {"delta_lambda_operand_missing": 1}


def test_object_kind_outside_the_declared_applicability_is_unqualified_never_1():
    rec = _rec("a", kind="varga_position")
    (w,), _ = _draft([rec], _rows_declared)
    assert w.score is None and w.unresolved == {"object_kind_not_covered_by_applicability": 1}


# ── interior extrema (never endpoint-only — §7.2 inv 2, O-SM-4) ──────────────

def _tri(centre_day, half_width_days):
    """Δλ(t) in degrees = a V around the exact contact (|Δλ| = 0 at the centre)."""
    def f(t):
        return abs((t - _d(centre_day)).total_seconds() / 86400.0) * (5.0 / half_width_days)
    return f


def test_angular_kernel_interior_maximum_is_found_not_an_endpoint():
    rec = _rec("pt", relation="conjunction", kind="house_lord", supports=((0, 30),),
               delta_lambda_at=_tri(11.3, 15.0))
    (w,), _ = _draft([rec], lambda p, v: _rows_declared(p, v, orb=5.0))
    assert w.score == pytest.approx(1.0, abs=1e-6)
    assert abs((w.peak_instant - _d(11.3)).total_seconds()) < 5          # interior contact instant
    assert w.peak_instant != w.interval[0]


def test_maximise_earliest_o_sm_4_parabola_interior_peak():
    # f(t) = x(1-x), x = fraction of the interval: endpoints are 0, the maximum 0.25 is at 0.5
    lo, hi = _d(0), _d(10)

    def f(t):
        x = (t - lo) / (hi - lo)
        return x * (1.0 - x)

    best, at = ws.maximise_earliest(f, lo, hi)
    assert best == pytest.approx(0.25, abs=1e-9)
    assert abs((at - _d(5)).total_seconds()) < 5


def test_maximise_earliest_plateau_returns_the_earliest_instant():
    best, at = ws.maximise_earliest(lambda t: 1.0, _d(3), _d(9))
    assert (best, at) == (1.0, _d(3))


def test_maximise_earliest_undeterminable_everywhere_is_none_not_zero():
    assert ws.maximise_earliest(lambda t: None, _d(0), _d(4)) is None


def test_peak_is_the_earliest_instant_of_the_window_maximum_across_members():
    rows = lambda p, v: _rows_declared(p, v, orb=5.0)
    near = _rec("near", relation="conjunction", kind="house_lord", root="R1", supports=((0, 30),),
                delta_lambda_at=_tri(20.0, 15.0))
    far = _rec("far", relation="conjunction", kind="house_lord", root="R2", supports=((0, 30),),
               delta_lambda_at=_tri(8.0, 15.0))
    (w,), _ = _draft([near, far], rows)
    # both reach 1.0; the earlier contact instant wins
    assert abs((w.peak_instant - _d(8.0)).total_seconds()) < 5


# ── mixed windows ────────────────────────────────────────────────────────────

def test_mixed_window_scores_from_qualified_members_and_discloses_the_unqualified_ones():
    q = _rec("q", root="Rq", supports=((0, 10),))
    u = _rec("u", root="Ru", kind="varga_position", supports=((0, 10),))
    (w,), _ = _draft([q, u], _rows_declared)
    assert w.score == 1.0 and w.evidence_for == 1.0
    assert w.null_states_used == ["unqualified"]
    assert w.unresolved == {"object_kind_not_covered_by_applicability": 1}
    assert (w.members, w.qualified_members) == (2, 1)


def test_two_components_make_two_windows_each_with_its_own_peak():
    recs = [_rec("a", root="R1", supports=((0, 5),)), _rec("b", root="R2", supports=((50, 60),))]
    drafts, _ = _draft(recs, _rows_declared)
    assert [(d.interval, d.peak_instant) for d in drafts] == [((_d(0), _d(5)), _d(0)),
                                                              ((_d(50), _d(60)), _d(50))]


def test_naive_datetimes_are_refused():
    with pytest.raises(SweepRefusal):
        ws.utc(datetime(2010, 1, 1))


# ── the real 1.1.0 rows (Stream B, PR #2897) — only when they are on main ────

@pytest.mark.skipif(("activity_kernel", "1.1.0") not in reg.FACTORS,
                    reason="activity_kernel@1.1.0 (AM-13) not on main yet")
def test_real_1_1_0_rows_light_the_sweep_up_with_no_code_change():
    (w,), _ = _draft([_rec("a", version="1.1.0", supports=((0, 10),))],
                     lambda p, v: ws.registry_factor_rows(p, v))
    assert w.score == 1.0


# ── the against channel is derived from the registry row, never from a path name ──────────────────

def _row(factor_id, direction):
    return {"factor_id": factor_id, "rule_version": "1.0.0", "null_state": "unqualified",
            "direction": direction, "applicability": {"span": {"object_kinds": ["sign_span"], "inside": 1.0}}}


def test_a_row_that_declares_only_magnitude_has_an_evaluated_empty_against_sum_for_any_path_name():
    for path in ("P3", "P4"):
        (w,), _ = _draft([_rec("a", path=path, supports=((0, 10),))],
                         lambda p, v: [_row("activity_kernel", "higher = stronger")])
        assert w.score == 1.0 and w.evidence_against == 0.0


def test_a_synthetic_path_that_declares_an_against_operand_leaves_the_against_sum_null():
    rows = [_row("activity_kernel", "higher = stronger"),
            _row("graduated_drishti", "benefic -> favourable channel; malefic -> adverse channel")]
    assert ws.against_channel_state(rows) == "declared"
    (w,), _ = _draft([_rec("a", supports=((0, 10),))],
                     lambda p, v: [rows[0]])             # only the magnitude factor evaluated...
    assert w.evidence_against == 0.0
    # ...whereas the SAME record under a row set that declares the operand cannot claim an empty sum:
    rec = _rec("a", relation="aspect", supports=((0, 10),), aspect_offset_at=lambda t: 7)
    (w2,), _ = _draft([rec], lambda p, v: rows, drishti=lambda a, o: 1.0)
    assert w2.score == 1.0 and w2.evidence_for == 1.0
    assert w2.evidence_against is None                    # declared, not evaluated here ⇒ NULL
    assert w2.outcome_valence_for_native == "unqualified"  # contested-vs-plain cannot be stated


def test_a_silent_or_ambiguous_direction_leaves_the_against_sum_null():
    for direction in (None, "", "sideways", "doctrine-ordered"):
        rows = [_row("activity_kernel", direction)]
        assert ws.against_channel_state(rows) == "ambiguous"
        (w,), _ = _draft([_rec("a", supports=((0, 10),))], lambda p, v, r=rows: r)
        assert w.score == 1.0 and w.evidence_against is None


def test_todays_p3_p4_registry_rows_declare_no_against_channel():
    for path in ("P3", "P4"):
        assert ws.against_channel_state(ws.registry_factor_rows(path, "1.0.0")) == "none_declared"


# ── a mixed window's score and evidence are LOWER BOUNDS, said machine-readably ─────────────────────

def test_mixed_window_discloses_lower_bound_in_the_stored_encoding():
    q = _rec("q", root="Rq", supports=((0, 10),))
    u = _rec("u", root="Ru", kind="varga_position", supports=((0, 10),))
    (w,), _ = _draft([q, u], _rows_declared)
    assert w.score_is_lower_bound is True
    assert w.score is not None and "unqualified" in w.null_states_used     # the stored encoding


def test_a_fully_qualified_window_is_not_a_lower_bound_and_an_unqualified_one_has_no_score_to_bound():
    (a,), _ = _draft([_rec("q", supports=((0, 10),))], _rows_declared)
    assert a.score_is_lower_bound is False and a.null_states_used == []
    (b,), _ = _draft([_rec("u", kind="varga_position", supports=((0, 10),))], _rows_declared)
    assert b.score is None and b.score_is_lower_bound is False


# ── P2: a direction per record, vedha a named missing input ──────────────────────────────────────────

def _p2(rid, agent, house, **kw):
    return _rec(rid, path="P2", agent=agent, house_from_frame=house, **kw)


def _p2_rows(path, version):
    return ws.registry_factor_rows(path, version)


def test_p2_without_a_vedha_source_is_a_named_missing_input_never_1():
    (w,), _ = _draft([_p2("a", "saturn", 8, supports=((0, 10),))], _p2_rows, cls="bereavement")
    assert w.score is None and w.unresolved == {"vedha_overlay_not_bound": 1}
    assert w.outcome_valence_for_native == "unqualified"


def test_p2_direction_is_stream_bs_cited_sets_called_not_copied():
    assert ws.p2_direction("saturn", 8) == "adverse"        # adverse-residence set (D-RQ5)
    assert ws.p2_direction("saturn", 3) == "favourable"     # Phaladīpikā XXVI favourable set
    with pytest.raises(SweepRefusal):
        ws.p2_direction("saturn", 2)                         # in neither set: refused, never defaulted
    with pytest.raises(SweepRefusal):
        ws.p2_direction("saturn", None)


def test_p2_channel_is_class_relative_through_score_channel_for():
    from services.gochara_rules.score import channel_for
    for cls in ("bereavement", "marriage"):                  # an adverse class and a gain class
        for house, direction in ((8, "adverse"), (3, "favourable")):
            rec = _p2("a", "saturn", house, supports=((0, 10),))
            assert ws.record_channel(cls, rec) == channel_for(direction, cls)
    assert ws.record_channel("bereavement", _p2("a", "saturn", 8)) == ws.CHANNEL_FOR
    assert ws.record_channel("marriage", _p2("a", "saturn", 8)) == ws.CHANNEL_AGAINST


def test_p2_with_a_bound_vedha_source_evaluates_both_channels_never_netted():
    vedha = lambda rec, t: 0.5                               # a stand-in for the bound overlay + mapping
    recs = [_p2("adv", "saturn", 8, root="R1", supports=((0, 10),)),    # adverse residence
            _p2("fav", "jupiter", 5, root="R2", supports=((0, 10),))]   # favourable residence
    (w,), _ = _draft(recs, _p2_rows, cls="bereavement", vedha=vedha)
    assert w.score == 0.5                                    # for-channel for an adverse class = the adverse record
    assert w.evidence_for == 0.5 and w.evidence_against == 0.5
    assert w.outcome_valence_for_native == "adverse"
    (g,), _ = _draft(recs, _p2_rows, cls="marriage", vedha=vedha)
    assert g.evidence_for == 0.5 and g.evidence_against == 0.5   # channels swap for a gain class


def test_p2_window_whose_members_are_all_against_scores_an_evaluated_zero_peaking_at_its_start():
    vedha = lambda rec, t: 1.0
    (w,), _ = _draft([_p2("a", "saturn", 8, supports=((3, 9),))], _p2_rows, cls="marriage", vedha=vedha)
    assert (w.score, w.evidence_for, w.evidence_against) == (0.0, 0.0, 1.0)
    assert w.peak_instant == _d(3)


def test_p2_vedha_state_undeterminable_everywhere_is_unqualified_not_zero():
    (w,), _ = _draft([_p2("a", "saturn", 8, supports=((0, 10),))], _p2_rows, cls="bereavement",
                     vedha=lambda rec, t: None)
    assert w.score is None and w.unresolved == {"operand_undeterminable_over_support": 1}


# ── steps: the earliest instant of the max is the exact breakpoint, not the next grid point ──────────

def test_maximise_earliest_finds_a_step_breakpoint_off_the_sample_grid():
    lo, hi = _d(0), _d(1000)
    breakpoint_day = 333.3333                                    # not a multiple of 1000/64 days
    f = lambda t: 1.0 if (t - lo).total_seconds() / 86400.0 >= breakpoint_day else 0.25
    best, at = ws.maximise_earliest(f, lo, hi)
    assert best == 1.0
    assert abs((at - _d(breakpoint_day)).total_seconds()) < 2.0


def test_a_drishti_step_inside_one_aspect_record_peaks_at_the_offset_change():
    # the aspect offset moves 5 -> 7 on day 41.7 (the body leaves one source sign for the next):
    # half then full; the window's peak is the instant it reaches FULL, exactly
    table = {5: 0.5, 7: 1.0}
    rec = _rec("a", relation="aspect", supports=((0, 100),),
               aspect_offset_at=lambda t: 5 if (t - _d(0)).total_seconds() / 86400.0 < 41.7 else 7)
    (w,), _ = _draft([rec], _rows_declared, drishti=lambda a, o: table[o])
    assert w.score == 1.0
    assert abs((w.peak_instant - _d(41.7)).total_seconds()) < 2.0


def test_a_drishti_source_returning_none_makes_that_instant_undeterminable():
    rec = _rec("a", relation="aspect", supports=((0, 10),), aspect_offset_at=lambda t: 6)
    (w,), _ = _draft([rec], _rows_declared, drishti=lambda a, o: None)   # e.g. 'no_aspect_at_this_offset'
    assert w.score is None and w.unresolved == {"operand_undeterminable_over_support": 1}


# ── the writer's real drishti source (Stream B's cited table, called) ────────────────────────────────

def test_the_writers_drishti_source_is_streamb_graduated_drishti_not_a_copy():
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    from services.gochara_rules import drishti
    for agent in ("saturn", "sun", "mars", "jupiter", "rahu"):
        for off in range(0, 14):
            assert writer_mod.DRISHTI_SOURCE(agent, off) == drishti.graduated_drishti(
                agent.title(), off)["value"]


def test_an_aspect_record_scores_through_the_real_table():
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    full = _rec("s", relation="aspect", agent="saturn", supports=((0, 10),), aspect_offset_at=lambda t: 3)
    quarter = _rec("m", relation="aspect", agent="sun", supports=((0, 10),), aspect_offset_at=lambda t: 3)
    (a,), _ = _draft([full], _rows_declared, drishti=writer_mod.DRISHTI_SOURCE)
    (b,), _ = _draft([quarter], _rows_declared, drishti=writer_mod.DRISHTI_SOURCE)
    assert (a.score, b.score) == (1.0, 0.25)                    # Saturn's special 3rd; the Sun's ordinary 3rd
    node = _rec("n", relation="aspect", agent="rahu", supports=((0, 10),), aspect_offset_at=lambda t: 7)
    (c,), _ = _draft([node], _rows_declared, drishti=writer_mod.DRISHTI_SOURCE)
    assert c.score is None                                       # N-14: a node casts no dṛṣṭi


# ── P1: windows are formed; the categorical factors declare no value mapping ─────────────────────────

def test_p1_window_is_formed_and_stored_unqualified_with_the_named_reason():
    rows = ws.registry_factor_rows("P1", "1.0.0")
    assert {r["factor_id"] for r in rows} == {"dignity_of_transit_sign", "combustion", "agent_nature",
                                              "maitri_compound"}
    recs = [_rec("a", path="P1", relation="aspect", kind="house_span", supports=((0, 30),)),
            _rec("b", path="P1", root="rb", supports=((20, 50),))]
    (w,), _ = _draft(recs, ws.registry_factor_rows)
    assert w.interval == (_d(0), _d(50))
    assert (w.score, w.evidence_for, w.evidence_against, w.peak_instant) == (None, None, None, None)
    assert w.unresolved == {"value_mapping_undeclared": 2} and w.outcome_valence_for_native == "unqualified"


def test_p1_row_that_declares_a_value_mapping_is_refused_not_ignored():
    rows = [dict(r, value_mapping={"benefic": 1.0}) if r["factor_id"] == "agent_nature" else r
            for r in ws.registry_factor_rows("P1", "1.0.0")]
    with pytest.raises(SweepRefusal):
        _draft([_rec("a", path="P1")], lambda p, v: rows)


def test_p1_channel_assignment_is_not_implemented_and_says_so():
    with pytest.raises(SweepRefusal):
        ws.record_channel("marriage", _rec("a", path="P1"))


def test_builder_and_verifier_agree_on_every_factor_state_of_every_swept_path_today():
    """The verifier re-derives qualification from the same rows with its own code; for every swept
    path and a record of every relation they must name the SAME missing operand."""
    from services.gochara_kernel import window_verifier as wv
    for path in ("P1", "P2", "P3", "P4"):
        rows = ws.registry_factor_rows(path, "1.0.0")
        for relation in ("residence", "aspect", "conjunction"):
            rec = _rec("a", path=path, relation=relation, supports=((0, 10),))
            prog = ws.build_program(rec, rows)
            built = sorted({r for _f, r in prog.reasons})
            derived = wv._record_state(rows, {"kind": rec.object_kind, "relation": relation}, False, False)
            assert (built == []) == (derived[0] != "unq"), (path, relation)
            if built:
                assert built == derived[1], (path, relation, built, derived)
