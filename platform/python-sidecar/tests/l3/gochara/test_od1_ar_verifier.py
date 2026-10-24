"""SR-OD1 achievement_recognition, VERIFIER side — defects (1b) and (3) of AR_DIAG (job X-20261022T090833Z-ar-diag).

(1b) The builder blanks a P2 record whose vedha overlay is unknown over its WHOLE support under the ONE reason the unknown stretches name
(`window_sweep._named_reason_everywhere`; the C1 contract: "the sweep passes the reason through"), else under the generic
`operand_undeterminable_over_support`. The window verifier collapsed every such record to the generic name, so 31 of 32 P2 windows failed the
in-build self-check with `qualification {...} != re-derived {...}`. Doctrine for the names: Phaladīpikā XXVI.3-8 (the cited obstructors) +
ND-NODE-VEDHA (the nodes obstruct); `gochara_rules.vedha_derive` names a graha's missing residence `obstructor_residence_unknown` and a node's
`node_residence_unknown`; a missing residence is missing data, never inactivity (Codex round 7 [6a]).

(3) The verification job ran the contact certifier with no graze sink, so a legitimate NEAR-MISS (an in-band stretch that never crosses the exact
aspect level; the builder mints a point contact only around an exact root, ND-P2-20261005 rules 1-2 / AM-13, so its ledger rightly holds none and
the near-miss layer holds the stretch) raised as an omitted contact. The sink is not a forgiveness: what the certifier reports from the ephemeris
must pair with the stored near-miss rows in both directions, or the stage raises by name.

Claims, each with ONE oracle (the single planted reversion that must fail it is named):

  V-1  a wholly-unknown record is blank under the single named reason of its unknown stretches — the obstructor gap and the node gap each keep
       their own name — and that is the name the builder's own naming function gives on the same overlay
       (revert: `_row_state`/`_record_state` collapse back to `[WHOLLY_UNKNOWN_REASON]`);
  V-2  unknown stretches that name different reasons stay under the generic reason, never one picked among several
       (revert: `blank_reason` returns an arbitrary member of the set);
  V-3  end to end through `verify_window_semantics`: the window the builder stored under a named reason is reproduced, not disagreed with
       (revert: as V-1, observed through the whole verifier);
  G-1  a near-miss with a stored near-miss row passes the geometry stage (revert: drop `graze_sink=[]` -> the production message
       "expected contact [...) is not in the ledger" returns);
  G-2  a near-miss with NO stored row raises `near_miss_reported_but_unstored` (revert: skip the reconciliation: the sink silently forgives);
  G-3  a stored near-miss the ephemeris does not show raises `near_miss_stored_but_unreported` (revert: drop the stored-but-unreported loop);
  G-4  a stretch with a real crossing and no contact is still an omission, even beside a stored near-miss row (revert: collect-all policy);
  G-5  without the near-miss layer there is no sink — the old behaviour (revert: always pass a sink);
  G-6  `verify_class` runs the geometry stage through `certify_geometry` with the inventory horizon, and its failure is a named DISAGREEMENT
       (revert: `_verify_class` calls the bare certifier again).

Review B1 (lane review of this branch): the verifier's graduated-dṛṣṭi step reads the sky at a stored sign ingress, a JD double exact to one JD-ulp, so it
applies the platform's boundary convention (half-open, the NEW state owns the boundary instant, `p1_operands_check` NAMED LIMITS; SR-H2-1S / R-2) at
that precision, with its OWN code (K12):

  B-1  a stored ingress 20 µs either side of the true edge (inside one JD-ulp, ~40 µs) is VERIFIED
       (revert: `_drishti_step` reads the ephemeris at the raw instant, no ownership clamp);
  B-2  an ingress listed 1 s off still REFUTES (H2) (revert: the clamp becomes seconds-wide);
  B-3  an ingress listed 1 ms off still REFUTES (H2) — never looser than one ulp
       (revert: the tolerance becomes 1 ms)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from services.gochara_kernel import verification_job as vj
from services.gochara_kernel import vedha_verifier as vv
from services.gochara_kernel import window_verifier as wv

from .test_member_geometry_seam import DAY, RAY, T0, curve, curve_graze
from ._vedha_sky import longitude_at_for
from .test_od1_c2_vedha_verifier import CHART, CLS, FakeConn, GEN, MOON, SUN, _window_world, D, quiet

UTC = timezone.utc

OBSTRUCTOR_GAP = "obstructor_residence_unknown"
NODE_GAP = "node_residence_unknown"
ROWS = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
RECORD = {"id": "r-sun", "relation": "residence", "kind": "sign_span", "agent": "sun", "house": 3, "boundaries_complete": False}


# ── (1b) the named reason ─────────────────────────────────────────────────────────────────────────────────────────────────

def _without(*bodies):
    return [r for r in quiet() if r[0] not in bodies]


def _sky(rows, gaps=None):
    """The verifier's position source (SR-VEDHA-RESIDENCE-SOURCE: residence is DERIVED from the sky, no longer read from stored contacts) over `rows`, with `gaps` =
    {body: [(from, to)]} stretches where the sky cannot answer for that body. The shared synthetic sky can only run out AFTER a body's last row, so a gap EARLY in
    the support (the mixed case below) is stated here, not by omitting rows."""
    base = longitude_at_for(rows)

    def longitude_at(graha, t):
        if any(lo <= t < hi for lo, hi in (gaps or {}).get(graha.lower(), ())):
            raise vv.EphemerisUnavailable(f"synthetic sky: {graha} cannot be answered at {t.isoformat()}")
        return base(graha, t)
    longitude_at.max_speed_dps = base.max_speed_dps
    return longitude_at


def _overlay(records, longitude_at):
    return vv.derive_overlay(FakeConn(records=records), chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0",
                             moon_sign=MOON, longitude_at=longitude_at)


def _obstructor_gap():          # Mars has no residence the sky can answer: a graha's gap
    return _sky(_without("mars"))


def _node_gap():                # Rāhu has none: a node's gap (ND-NODE-VEDHA: the nodes obstruct, so their residence is needed)
    return _sky(_without("rahu"))


def _mixed_gap():               # days 10-25 only Mars is unanswered, days 25-40 only Rāhu: two names over one support
    return _sky(quiet(), {"mars": [(D(-1000), D(25))], "rahu": [(D(25), D(1000))]})


def _builder_name(ov):
    """The builder's own naming of the same overlay (`window_sweep` wires `Outcome.unknown_reason = overlay.unknown_reason_at` into the record program)."""
    from services.gochara_kernel import window_sweep as ws
    prog = SimpleNamespace(unknown_reason_at=ov.unknown_reason_at)
    return ws._named_reason_everywhere(prog, [(D(10), D(40))]) or "operand_undeterminable_over_support"


@pytest.mark.parametrize("residence,named", [(_obstructor_gap, OBSTRUCTOR_GAP), (_node_gap, NODE_GAP)])
def test_v1_a_wholly_unknown_record_is_blank_under_the_one_reason_its_stretches_name(residence, named):
    ov = _overlay([SUN], residence())("r-sun")
    assert ov.wholly_unknown
    assert wv._record_state(ROWS, RECORD, False, True, lambda rid: ov) == ("unq", [named])
    assert _builder_name(ov) == named                                  # the verifier and the builder name the same thing


def test_v2_stretches_that_name_different_reasons_stay_under_the_generic_reason():
    ov = _overlay([SUN], _mixed_gap())("r-sun")
    assert ov.wholly_unknown and {s.reason for s in ov.segments} == {OBSTRUCTOR_GAP, NODE_GAP}
    assert wv._record_state(ROWS, RECORD, False, True, lambda rid: ov) == ("unq", [vv.WHOLLY_UNKNOWN_REASON])
    assert _builder_name(ov) == vv.WHOLLY_UNKNOWN_REASON               # sampled, the builder lands on the same answer here


@pytest.mark.parametrize("residence,named", [(_obstructor_gap, OBSTRUCTOR_GAP), (_node_gap, NODE_GAP), (_mixed_gap, vv.WHOLLY_UNKNOWN_REASON)])
def test_v3_the_window_stored_under_the_named_reason_is_reproduced_end_to_end(residence, named, monkeypatch):
    monkeypatch.setattr(vv, "swiss_longitude", lambda path, convention: residence())      # the Swiss reader has its own oracles (test_od1_vedha_residence)
    conn = _window_world(None, reason=named, unqualified=True)
    out = wv.verify_window_semantics(conn, chart_id="c", generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0",
                                     factor_rows=ROWS, vedha_bound=True, policy=wv.POLICY_VERSION, moon_sign=MOON)
    assert out["windows_detail"][0]["unqualified_reason"] == named
    assert out["windows_detail"][0]["unresolved"] == {named: 1}
    assert out["status"] == "VERIFIED"


# ── (3) the graze sink and its reconciliation ─────────────────────────────────────────────────────────────────────────────

LO, HI = T0 - 40 * DAY, T0 + 40 * DAY
TARGET = f"point:{RAY}"
KEY = ("venus", "conjunction", TARGET)
STRETCH_EDGE = (0.3 / 0.02) ** 0.5      # curve_graze: |lambda - RAY| = 1 at 0.3 + 0.02 d^2 = 1 -> d = sqrt(35); in band for |d| < sqrt(35)
NM_IN, NM_OUT = T0 - 5.9 * DAY, T0 + 5.9 * DAY


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class GeoConn:
    """Answers, from literal rows, the statements of the certifier and of the verifier's own near-miss reconciliation."""

    def __init__(self, *, layer=True, contacts=(), stored=(), obligations=(KEY,)):
        self.layer, self.contacts, self.stored, self.obligations = layer, list(contacts), list(stored), list(obligations)

    def execute(self, sql, params=()):
        flat = " ".join(sql.split())
        if "to_regclass" in flat:
            return _Cur([(self.layer,)])
        if "FROM public.ka_gochara_search_inventory" in flat:
            return _Cur([(LO, HI)])
        if "FROM public.ka_gochara_search_obligation" in flat:
            return _Cur(self.obligations)
        if "FROM public.ka_gochara_contact c" in flat:
            return _Cur(self.contacts)
        if "FROM public.ka_gochara_near_miss n" in flat:
            return _Cur(self.stored)
        if "FROM public.ka_gochara_near_miss_search s" in flat:
            return _Cur([])                                    # no searched object, so no disclosed identity-domain tail (test_near_miss_geometry_tail_reconcile)
        raise AssertionError(flat[:160])


def _stored(t_in=NM_IN, t_out=NM_OUT, key=KEY, nm_id="nm-1"):
    return (*key, nm_id, t_in, t_out, 0.3)


def _geometry(conn, position_at=curve_graze):
    return vj.certify_geometry(conn, chart_id="c", generation=GEN, event_class=CLS, position_at=position_at, horizon=(LO, HI))


def test_g1_a_near_miss_with_a_stored_row_passes_the_geometry_stage():
    out = _geometry(GeoConn(stored=[_stored()]))
    assert out["obligations_certified"] == 1 and len(out["grazes"]) == 1 and out["grazes"][0]["target"] == TARGET


def test_g2_a_near_miss_with_no_stored_row_is_raised_by_name():
    with pytest.raises(RuntimeError, match=r"near-miss reconciliation failed marriage: near_miss_reported_but_unstored: venus conjunction point:120\.0"):
        _geometry(GeoConn(stored=[]))


def test_g3_a_stored_near_miss_the_ephemeris_does_not_show_is_raised_by_name():
    elsewhere = _stored(T0 + 20 * DAY, T0 + 30 * DAY, nm_id="nm-phantom")             # the sky shows its one stretch around T0
    with pytest.raises(RuntimeError, match=r"near_miss_stored_but_unreported: venus conjunction point:120\.0 .*\(id nm-phantom\)"):
        _geometry(GeoConn(stored=[_stored(), elsewhere]))
    with pytest.raises(RuntimeError, match="near_miss_reported_but_unstored"):
        _geometry(GeoConn(stored=[elsewhere]))                                         # ... and the real stretch has no row


def test_g3b_a_stored_row_of_another_object_never_pairs_with_this_objects_graze():
    other = _stored(key=("venus", "aspect", TARGET), nm_id="nm-other")
    with pytest.raises(RuntimeError, match="near_miss_reported_but_unstored"):
        _geometry(GeoConn(stored=[other]))


def test_g4_a_real_crossing_with_no_contact_is_still_an_omission_beside_a_stored_near_miss():
    with pytest.raises(RuntimeError, match=r"contact geometry certification failed marriage: .*expected contact \[.*\) is not in the ledger"):
        _geometry(GeoConn(stored=[_stored()]), position_at=curve)


def test_g5_without_the_near_miss_layer_there_is_no_sink_and_a_graze_raises_as_before():
    with pytest.raises(RuntimeError, match=r"expected contact \[.*\) is not in the ledger"):
        _geometry(GeoConn(layer=False, stored=[_stored()]))


def test_g6_verify_class_runs_the_geometry_stage_through_the_reconciling_function_and_fails_by_name(monkeypatch):
    from services.gochara_kernel import inventory_verifier as inv_v
    horizon = (D(0), D(100))
    seen = {}

    def boom(conn, **kw):
        seen.update(kw)
        raise RuntimeError("near-miss reconciliation failed: sentinel")
    monkeypatch.setattr(vj, "take_locks", lambda *a, **k: None)
    monkeypatch.setattr(vj, "_inventory_header", lambda *a: (*horizon, "d-inv", "d-led"))
    monkeypatch.setattr(vj, "_sealed_paths", lambda c: [])
    monkeypatch.setattr(vj, "class_fingerprint", lambda *a: {})
    monkeypatch.setattr(vj, "fingerprint_digest", lambda fp: "fp")
    monkeypatch.setattr(vj, "certify_geometry", boom)
    from services.gochara_kernel import window_gate as wg
    monkeypatch.setattr(wg, "generation_output_problems", lambda *a: [])
    from services.gochara_kernel import result_policy
    monkeypatch.setattr(result_policy, "manifest_policy", lambda *a: "p")
    monkeypatch.setattr(inv_v, "stored_selection", lambda *a, **k: {})
    monkeypatch.setattr(inv_v, "rederive_inventory_digest", lambda *a, **k: {"digest": "d-inv", "obligations": []})
    monkeypatch.setattr(inv_v, "rederive_ledger_digest", lambda *a, **k: "d-led")
    with pytest.raises(vj.VerificationDisagrees) as exc:
        vj._verify_class(object(), chart_id="c", generation=GEN, event_class=CLS, position_at=curve_graze, configured_selection={},
                         path_rulings={}, h_unknown={}, moon_scope_domain=False, factor_rows_for=lambda *a: [], drishti_bound=False,
                         vedha_bound=False, persist=False)
    assert exc.value.stage == "contact_geometry" and "sentinel" in str(exc.value)
    assert seen["horizon"] == horizon and seen["event_class"] == CLS and seen["position_at"] is curve_graze


# ── review B1: the half-open, new-state-owns-the-boundary convention at one JD-ulp, verifier side ──────────────────────────────────

TRUE_EDGE = datetime(2011, 6, 4, 12, 0, 0, tzinfo=UTC)          # JD ~2455717.0: one JD-ulp is ~40 µs here (math.ulp(2455717) * 86400e6)


def _crossing_longitude(body, t):
    """A body at 0.1 deg/day whose sidereal longitude reaches 30 deg (Aries -> Taurus) at TRUE_EDGE: sign(t) = 0 before, 1 from TRUE_EDGE on."""
    return 30.0 + (t - TRUE_EDGE).total_seconds() / 86400.0 * 0.1


class _IngressConn:
    def __init__(self, ingress):
        self.ingress = ingress

    def execute(self, sql, params=()):
        rows = [(x,) for x in self.ingress]
        return type("C", (), {"fetchall": lambda s: rows})()


def _check_with_listed_ingress(listed):
    """The verifier's prover over one 4-day support that contains the real sign change, the change instant listed as `listed`."""
    from services.gochara_kernel import window_solver_check as chk
    st = wv._drishti_step(_IngressConn([listed]), {"id": "r", "agent": "jupiter", "boundaries_complete": True},
                          {"factor_id": "graduated_drishti", "rule_version": "1.0.0"}, "span:5", _crossing_longitude)
    lo, hi = TRUE_EDGE - timedelta(days=2), TRUE_EDGE + timedelta(days=2)
    before, after = st.value_at(lo), st.value_at(hi - timedelta(seconds=1))
    assert before != after                                          # the oracle can read false: the dṛṣṭi value really steps at the sign change
    best, peak = (before, lo) if before >= after else (after, TRUE_EDGE)
    return chk, chk.check_window(
        lo=lo, hi=hi, records=[chk.CheckRecord(record_id="r", root="R", agent="jupiter", supports=((lo, hi),), steps=(st,))],
        objective=chk.OBJ_SUM, stored=chk.StoredWindow(peak_instant=peak, objective_value=best), position_at=_crossing_longitude)


@pytest.mark.parametrize("off_us", [-20, 20])
def test_b1_an_ingress_within_one_jd_ulp_of_the_true_edge_is_verified(off_us):
    chk, rep = _check_with_listed_ingress(TRUE_EDGE + timedelta(microseconds=off_us))
    assert rep.status == chk.VERIFIED, [f.detail for f in rep.findings]


@pytest.mark.parametrize("off", [timedelta(seconds=-1), timedelta(seconds=1), timedelta(milliseconds=-1), timedelta(milliseconds=1)])
def test_b1_an_ingress_listed_a_millisecond_or_more_off_is_still_refuted_never_looser_than_one_ulp(off):
    chk, rep = _check_with_listed_ingress(TRUE_EDGE + off)
    assert rep.status != chk.VERIFIED and chk.F_H2 in {f.code for f in rep.findings}


def test_b1_the_edge_ulp_is_the_jd_double_spacing_in_whole_microseconds_widened_by_the_storage_grain():
    import math
    jd = 2440587.5 + TRUE_EDGE.timestamp() / 86400.0
    assert wv._edge_ulp(TRUE_EDGE) == timedelta(microseconds=math.ceil(math.ulp(jd) * 86400e6) + 1)
    assert timedelta(microseconds=39) < wv._edge_ulp(TRUE_EDGE) < timedelta(microseconds=50)


# ── K12 (edge-pair review N1, added at the merge-back wave 3c-a) ───────────────────────────────────────────────────────
def test_k12_the_window_verifier_imports_no_builder_module_so_its_ulp_clamp_is_its_own_code():
    """The verifier's JD-ulp edge clamp (`_edge_ulp`) is its own restatement, not the builder's `window_sweep.jd_ulp_tolerance`: a verifier that borrowed the builder's helper would agree with the builder
    by construction on the boundary convention (the second-set-of-eyes claim of B-1). Revert: `from .window_sweep import jd_ulp_tolerance as _edge_ulp` in window_verifier. Sibling pattern:
    test_od1_c2_vedha_verifier::test_c2_11."""
    import ast
    import inspect
    builder = {"window_sweep", "window_store", "window_solver", "p1_operands", "record_store", "materialise", "contacts", "substrate", "near_miss"}
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(wv))):
        if isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[-1])
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name.split(".")[-1] for a in node.names)
    assert not names & builder, names & builder
