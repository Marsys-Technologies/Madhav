"""SR-OD1 C2 — the window verifier's OWN vedha derivation (plan §3.4 "Verifier side"; `services/gochara_kernel/vedha_verifier.py`).

Doctrine (served corpus, Phaladīpikā XXVI.3–8, phaladeepika:PG322:C1 / PG323:C1): a favourable-house transit is NULLIFIED while a
cited obstructor occupies its vedha place; the pairs are the 36 cited rows of L0 `bg_transit_rules` (literal fixture
`tests/l3/gochara_rules/fixtures/l0_vedha_rows_2026_10_02.json`, read-only from production 2026-10-02: Sun 3→9, 6→12, 10→4, 11→5; Mercury
2→5 …); Sun↔Saturn and Moon↔Mercury never obstruct each other (M-8); the nodes obstruct the seven planets like any graha and a transiting
node carries no vedha factor (ND-NODE-VEDHA, owner-confirmed 2026-10-21; their six L0 rows stay flagged UNSOURCED); the Moon is not a stored agent (`excluding_on_demand_moon_obstruction`); an obstructor with no established
residence over the primary span is missing data, never "inactive" (Codex round 7 [6a]).

World used throughout: the native Moon in Aquarius (sign 11) ⇒ house h is sign (10 + h − 1) % 12 + 1, so the Sun in the 3rd is in Aries
(1) and its vedha place, the 9th, is Libra (7). No DB: a recording connection returns the rows the verifier's own SQL asks for.
SR-VEDHA-RESIDENCE-SOURCE: the obstructors' residence is DERIVED from a position source, not read from stored contacts — here a synthetic sky
(`_vedha_sky.py`; a connection that is asked for a stored contact FAILS the test). The real-ephemeris oracles are in `test_od1_vedha_residence.py`.

Claims, each with ONE oracle (the single planted reversion that must fail it is named):

  C2-1 an obstructor in the vedha house zeroes the primary's contribution over exactly the intersection, 1.0 elsewhere, with the Moon scope on
       every 1.0 and the segment edges as the COMPLETE boundary list
       (revert: the obstruction is read against the primary's own house instead of the vedha house);
  C2-2 a (graha, house) with no cited pair, and a node primary (UNSOURCED rows), is declared NOT APPLICABLE — the factor takes no part
       (revert: not-applicable read as a function-valued factor);
  C2-3 the M-8 exception: Saturn in the Sun's vedha house does not obstruct, Mars does
       (revert: the exception table is ignored);
  C2-4 an obstructor with no established residence over the primary span is `obstructor_residence_unknown` — never 1.0; a KNOWN obstruction still
       wins; a record unknown throughout is wholly unknown
       (revert: an empty residence list read as "not in the vedha house");
  C2-5 a node in the vedha house OBSTRUCTS like any graha (ND-NODE-VEDHA i; SR-OD1 D3 — the pre-ruling reading was `node_obstruction_undecided`)
       (revert: a node in the vedha house is ignored / undecided);
  C2-6 an obstructor the ephemeris cannot answer is a coverage gap — never inactivity, and said in the summary
       (revert: the unanswered stretch is read as "not in the vedha house");
  C2-7 the janma-rāśi sign is cross-checked against every stored house; disagreeing records are refused
       (revert: the stored house is trusted);
  C2-8 completeness is COMPUTED: segments that do not tile the record's supports raise
       (revert: `complete` asserted True);
  C2-9 the window verifier consumes the overlay per factor: not-applicable ⇒ no part in the product, wholly unknown ⇒ the record is unqualified
       under the named reason, an incomplete overlay ⇒ `state_boundaries_incomplete` even when the record-wide flag says complete, no overlay with
       a source bound is refused
       (revert: the record-wide boundary flag vouches for the vedha factor);
  C2-10 end to end through `verify_window_semantics`: the overlay is derived from the stored substrate by the verifier itself and the window
       it checks is reproduced (revert: the verifier answers `fn` / unqualified without deriving);
  C2-11 independence: the module imports no builder code, and its literal matches the sweep's.
"""
from __future__ import annotations

import ast
import inspect
import json
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import vedha_verifier as vv
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import vedha_derive as vd
from services.gochara_rules import vedha_oracle

from ._vedha_sky import longitude_at_for

FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "gochara_rules" / "fixtures" / "l0_vedha_rows_2026_10_02.json"
PAIR_ROWS = [tuple(r) for r in json.loads(FIXTURE.read_text())]
MOON = 11
T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
CHART, GEN, CLS = "482012f1-710e-4a25-994a-93821f5871aa", "5.0", "marriage"
SUN_SIGN_H3, SUN_VEDHA_SIGN_H9 = 1, 7           # Aries / Libra from an Aquarius Moon


def D(day: float) -> datetime:
    return T0 + timedelta(days=day)


class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    """Answers the verifier's own queries from literal rows; records every statement it was asked."""

    def __init__(self, *, records=(), pairs=PAIR_ROWS, windows=(), window_records=(), links=()):
        self.records, self.pairs = list(records), list(pairs)
        self.windows, self.window_records, self.links = list(windows), list(window_records), list(links)
        self.statements: list[str] = []

    def execute(self, sql, params=()):
        self.statements.append(sql)
        if "bg_transit_rules" in sql:
            return _Cursor(self.pairs)
        if "ka_gochara_contact" in sql:
            raise AssertionError("the verifier must not read stored contacts for the obstructors' residence")
        if "ka_gochara_sky_convention" in sql:
            return _Cursor([("lahiri_chitrapaksha", "mean")])
        if "canonical_target" in sql and "house_from_frame" in sql:
            return _Cursor(self.records)
        if "kala_gochara_publication" in sql:
            return _Cursor([])
        if "pg_attribute" in sql:
            return _Cursor([(0,)])
        if "FROM public.ka_gochara_eval_window_record" in sql:
            return _Cursor(self.links)
        if "FROM public.ka_gochara_eval_window WHERE" in sql:
            return _Cursor(self.windows)
        if "r.house_from_frame, lower(s.x)" in sql:
            return _Cursor(self.window_records)
        if "kala_gochara_coverage" in sql:
            return _Cursor([])
        raise AssertionError(f"unexpected statement: {sql[:120]}")


def quiet(*bodies):
    """Every obstructor parked in sign 2 (Taurus) for all of 2025 — it touches no vedha place used below — except the ones overridden."""
    names = ("sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
    return [(b, "span:2", D(-5), D(400)) for b in names if b not in bodies]


def rec(rid, agent, house, sign, lo, hi):
    return (rid, agent, house, f"span:{sign}", D(lo), D(hi))


def overlay(records, residence, **kw):
    conn = FakeConn(records=records)
    return vv.derive_overlay(conn, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0",
                             moon_sign=kw.get("moon_sign", MOON), longitude_at=longitude_at_for(residence))


SUN = rec("r-sun", "sun", 3, SUN_SIGN_H3, 10, 40)


# ── C2-1 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_1_an_obstructor_in_the_vedha_house_zeroes_exactly_the_intersection_and_the_edges_are_complete():
    # Mars in Libra (the Sun's 9th-house vedha place) for days 20–30, inside the Sun's stay in Aries (its 3rd) days 10–40
    ov = overlay([SUN], quiet("mars") + [("mars", "span:2", D(-5), D(20)), ("mars", f"span:{SUN_VEDHA_SIGN_H9}", D(20), D(30)),
                                          ("mars", "span:8", D(30), D(400))])
    r = ov("r-sun")
    assert r.applicable and r.complete
    assert (r.value_at(D(15)), r.value_at(D(25)), r.value_at(D(35))) == (1.0, 0.0, 1.0)
    assert r.value_at(D(20)) == 0.0 and r.value_at(D(30)) == 1.0                       # half-open: [20, 30)
    assert r.boundaries(D(10), D(40)) == [D(20), D(30)]                                  # exactly the intersection's edges
    assert r.scopes == [vd.MOON_SCOPE]                                                   # every 1.0 says the Moon was not checked
    # a Mars in the Sun's OWN house (Aries) obstructs nothing — the check is against the vedha house, not the primary's
    ov2 = overlay([SUN], quiet("mars") + [("mars", f"span:{SUN_SIGN_H3}", D(-5), D(400))])
    assert ov2("r-sun").value_at(D(25)) == 1.0


def test_c2_1_agrees_pointwise_with_the_independent_oracle_on_a_busy_world():
    res = (quiet("mars", "venus", "ketu")
           + [("mars", "span:2", D(-5), D(15)), ("mars", "span:7", D(15), D(22)), ("mars", "span:9", D(22), D(400)),
              ("venus", "span:2", D(-5), D(25)), ("venus", "span:7", D(25), D(33)), ("venus", "span:3", D(33), D(400)),
              ("ketu", "span:2", D(-5), D(12)), ("ketu", "span:7", D(12), D(18)), ("ketu", "span:2", D(18), D(400))])
    ov = overlay([SUN], res)("r-sun")
    pairs = vd.pairs_from_rows(PAIR_ROWS)
    residence = {}
    for body, target, a, b in res:
        residence.setdefault(body.capitalize(), []).append((int(target[5:]), a.isoformat(), b.isoformat()))
    for k in range(0, 59):                                  # every half day of the stay
        t = D(10 + k * 0.5)
        want = vedha_oracle.state_at(t.isoformat(), "Sun", 3, moon_sign=MOON, residence=residence, pairs=pairs)
        assert ov.value_at(t) == want["value"], (t, want)
        if want["value"] is None:
            assert ov.unknown_reason_at(t) == want["reason"]


# ── C2-2 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_2_an_uncited_house_and_a_node_primary_are_declared_not_applicable():
    sun_h8 = rec("r-h8", "sun", 8, 6, 10, 40)                  # Sun's 8th: no cited vedha pair (cited: 3, 6, 10, 11)
    rahu_h3 = rec("r-rahu", "rahu", 3, SUN_SIGN_H3, 10, 40)    # the L0 node rows are UNSOURCED — never usable
    ov = overlay([sun_h8, rahu_h3], quiet())
    for rid in ("r-h8", "r-rahu"):
        r = ov(rid)
        assert r.applicable is False and r.not_applicable_reason == "no_cited_vedha_pair_for_this_house"
    rows = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
    state = wv._record_state(rows, {"id": "r-h8", "relation": "residence", "kind": "sign_span", "agent": "sun", "house": 8,
                                    "boundaries_complete": False}, False, True, ov)
    assert state == ("const", 1.0)                              # takes no part in the product: neither a missing operand nor a silent factor


# ── C2-3 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_3_saturn_never_obstructs_the_sun_but_mars_does():
    in_vedha = f"span:{SUN_VEDHA_SIGN_H9}"
    saturn = overlay([SUN], quiet("saturn") + [("saturn", in_vedha, D(-5), D(400))])("r-sun")
    mars = overlay([SUN], quiet("mars") + [("mars", in_vedha, D(-5), D(400))])("r-sun")
    assert saturn.value_at(D(25)) == 1.0 and mars.value_at(D(25)) == 0.0


# ── C2-4 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_4_a_missing_residence_is_unknown_never_inactive_and_a_known_obstruction_still_wins():
    # Mercury is stored only up to day 25: days 25–40 are missing data
    ov = overlay([SUN], quiet("mercury") + [("mercury", "span:2", D(-5), D(25))])("r-sun")
    assert ov.value_at(D(15)) == 1.0
    assert ov.value_at(D(30)) is None and ov.unknown_reason_at(D(30)) == "obstructor_residence_unknown"
    assert D(25) in ov.boundaries(D(10), D(40))
    # ... but Mars known in the vedha house settles it at 0.0 whatever else is unknown
    both = overlay([SUN], quiet("mercury", "mars") + [("mercury", "span:2", D(-5), D(25)),
                                                       ("mars", f"span:{SUN_VEDHA_SIGN_H9}", D(-5), D(400))])("r-sun")
    assert both.value_at(D(30)) == 0.0
    # no residence at all: unknown throughout, and the window verifier makes the RECORD unqualified under the named reason
    nothing = overlay([SUN], [])("r-sun")
    assert nothing.wholly_unknown and nothing.value_at(D(25)) is None
    rows = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
    r = {"id": "r-sun", "relation": "residence", "kind": "sign_span", "agent": "sun", "house": 3, "boundaries_complete": False}
    assert wv._record_state(rows, r, False, True, lambda rid: nothing) == ("unq", [vv.WHOLLY_UNKNOWN_REASON])
    assert wv._record_state(rows, r, False, True, lambda rid: ov) == ("fn", None)      # partly known: a complete-edged step function


# ── C2-5 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_5_a_node_in_the_vedha_house_obstructs_like_any_graha():
    ov = overlay([SUN], quiet("rahu") + [("rahu", "span:2", D(-5), D(22)), ("rahu", f"span:{SUN_VEDHA_SIGN_H9}", D(22), D(400))])("r-sun")
    assert ov.value_at(D(15)) == 1.0
    assert ov.value_at(D(30)) == 0.0 and ov.unknown_reason_at(D(30)) is None            # Rāhu in the 9th from the Moon nullifies the Sun in the 3rd
    assert [(s.t_in, s.t_out, s.state) for s in ov.segments if s.state == "active"] == [(D(22), D(40), "active")]


# ── C2-6 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_6_an_obstructor_the_ephemeris_cannot_answer_is_a_coverage_gap_not_inactivity():
    ov = overlay([SUN], quiet("jupiter") + [("jupiter", "span:2", D(-5), D(20))])      # the sky answers for Jupiter until day 20, not after
    r = ov("r-sun")
    assert r.value_at(D(15)) == 1.0
    assert r.value_at(D(25)) is None and r.unknown_reason_at(D(25)) == "obstructor_residence_unknown"
    assert ov.summary()["residence_unanswered_seconds"].get("Jupiter", 0) > 0 and "Mars" not in ov.summary()["residence_unanswered_seconds"]
    assert ov.summary()["residence_source"] == vv.RESIDENCE_SOURCE


# ── C2-7 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_7_the_janma_rashi_sign_is_cross_checked_against_every_stored_house():
    liar = rec("r-liar", "sun", 6, SUN_SIGN_H3, 50, 60)          # Aries is the 3rd, not the 6th, from an Aquarius Moon
    with pytest.raises(vv.VedhaDerivationError, match="disagrees with the janma"):
        overlay([SUN, liar], quiet())
    with pytest.raises(vv.VedhaDerivationError, match="different janma"):    # no sign supplied: the records must agree among themselves
        overlay([SUN, liar], quiet(), moon_sign=None)
    ok = overlay([SUN], quiet(), moon_sign=None)                              # …and a single consistent record implies the sign
    assert ok.moon_sign == MOON and ok("r-sun").applicable
    with pytest.raises(vv.VedhaDerivationError, match="moon_sign must be"):
        overlay([SUN], quiet(), moon_sign=13)


# ── C2-8 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_8_completeness_is_computed_segments_that_leave_a_hole_raise(monkeypatch):
    real = vd.derive_vedha

    def holed(*a, **kw):
        d = real(*a, **kw)
        d["segments"] = [s for i, s in enumerate(d["segments"]) if i != 0] if len(d["segments"]) > 1 else []
        return d
    monkeypatch.setattr(vd, "derive_vedha", holed)
    res = quiet("mars") + [("mars", "span:2", D(-5), D(20)), ("mars", f"span:{SUN_VEDHA_SIGN_H9}", D(20), D(30)), ("mars", "span:8", D(30), D(400))]
    with pytest.raises(vv.VedhaDerivationError, match="do not tile"):
        overlay([SUN], res)


# ── C2-9 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_9_the_record_wide_boundary_flag_never_vouches_for_the_vedha_factor():
    rows = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
    r = {"id": "x", "relation": "residence", "kind": "sign_span", "agent": "sun", "house": 3, "boundaries_complete": True}
    incomplete = lambda rid: vv.RecordVedha(applicable=True, complete=False)         # noqa: E731
    assert wv._record_state(rows, r, False, True, incomplete) == ("unq", [wv.STATE_BOUNDARIES_REASON])
    assert wv._record_state(rows, r, False, False) == ("unq", ["vedha_overlay_not_bound"])    # no source bound: as before
    with pytest.raises(RuntimeError, match="no independent vedha derivation"):
        wv._record_state(rows, r, False, True)                                         # bound but nothing derived: refused, never assumed


# ── C2-10 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _window_world(_sky, *, reason=wv.DYNAMIC_SWITCH_REASON, unqualified=False):
    """One P2 record (Sun in the 3rd, days 10–40) and its one stored window, NULL under `reason` (the dynamic switch, or an unqualified member)."""
    lo, hi = D(10), D(40)
    null_valence = wv._expected_valence(CLS, 0.0, 0.0, reason)
    window = ("w1", lo, hi, None, None, None, None, None, ["unqualified"] if unqualified else [], null_valence, None, None, None)
    return FakeConn(records=[SUN], windows=[window], links=[("w1", "r-sun")],
                    window_records=[("r-sun", "c-sun", "residence", "sign_span", "sun", 3, lo, hi)])


def test_c2_10_verify_window_semantics_derives_the_overlay_itself_and_reproduces_the_window(monkeypatch):
    sky = quiet("mars") + [("mars", "span:2", D(-5), D(20)), ("mars", f"span:{SUN_VEDHA_SIGN_H9}", D(20), D(30)), ("mars", "span:8", D(30), D(400))]
    seen = []
    monkeypatch.setattr(vv, "swiss_longitude", lambda path, convention: seen.append((path, convention)) or longitude_at_for(sky))    # the Swiss reader has its own oracles
    conn = _window_world(sky)
    rows = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
    # S3: the stored window is the RETIRED switch's blank, so this is the legacy-switch world (`dynamic_enabled=False`); the solver world is test_od1_s3_integration
    out = wv.verify_window_semantics(conn, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0",
                                     factor_rows=rows, vedha_bound=True, policy=wv.POLICY_VERSION, moon_sign=MOON, dynamic_enabled=False,
                                     ephe_path="/ephe/under/test")
    assert seen == [("/ephe/under/test", {"ayanamsha": "lahiri_chitrapaksha", "node_convention": "mean"})]   # the PINNED convention, the caller's directory
    assert out["status"] == "VERIFIED" and out["fully_reproduced"] == 1
    assert out["vedha_derivation"]["applicable"] == 1 and out["vedha_derivation"]["moon_sign"] == MOON
    assert out["vedha_derivation"]["scopes"] == [vd.MOON_SCOPE] and len(out["vedha_derivation"]["pairs_digest"]) == 64
    assert any("bg_transit_rules" in s for s in conn.statements) and not any("ka_gochara_contact" in s for s in conn.statements)


def test_c2_10_a_record_unknown_throughout_makes_the_window_blank_under_the_named_reason(monkeypatch):
    monkeypatch.setattr(vv, "swiss_longitude", lambda path, convention: longitude_at_for([]))           # a sky that answers for nobody
    conn = _window_world([], reason=vv.WHOLLY_UNKNOWN_REASON, unqualified=True)
    rows = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
    out = wv.verify_window_semantics(conn, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0",
                                     factor_rows=rows, vedha_bound=True, policy=wv.POLICY_VERSION, moon_sign=MOON)
    assert out["windows_detail"][0]["unqualified_reason"] == vv.WHOLLY_UNKNOWN_REASON
    assert out["windows_detail"][0]["unresolved"] == {vv.WHOLLY_UNKNOWN_REASON: 1}


def test_c2_10_without_a_bound_source_nothing_is_derived_and_the_record_stays_blank():
    conn = _window_world([], reason="vedha_overlay_not_bound", unqualified=True)
    rows = [{"factor_id": "vedha_attenuation", "rule_version": "9.0.0", "null_state": "unqualified"}]
    out = wv.verify_window_semantics(conn, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0",
                                     factor_rows=rows, vedha_bound=False, policy=wv.POLICY_VERSION)
    assert out["windows_detail"][0]["unqualified_reason"] == "vedha_overlay_not_bound"
    assert "vedha_derivation" not in out and not any("bg_transit_rules" in s for s in conn.statements)


# ── C2-11 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_c2_11_the_module_imports_no_builder_code_and_its_reason_literal_is_the_sweeps():
    tree = ast.parse(pathlib.Path(inspect.getsourcefile(vv)).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add(("." * node.level) + (node.module or ""))
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert imported <= {"__future__", "os", "re", "dataclasses", "datetime", "typing", "swisseph", "panchang_engine.swiss_state",
                        "services.gochara_rules"}, imported          # the Swiss library, its process lock, the L0/doctrine module: no kernel (builder) module
    from services.gochara_kernel import window_sweep as ws
    assert f'"{vv.WHOLLY_UNKNOWN_REASON}"' in inspect.getsource(ws)
