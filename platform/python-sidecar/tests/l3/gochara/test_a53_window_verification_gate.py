"""A5.3 — the generation-bound window verification RESULT and the candidate gate (Codex round 8, R8-4; migration 1240).

A candidate is gate-ready only when every INCLUDED P1–P4 grain of the generation's inventory has a VERIFIED, current,
input-bound verification result that matches the database's own recomputation of the expected window set. Missing,
UNVERIFIED_DYNAMIC, stale, count-mismatched, expected-set-mismatched and wrong-input results each fail it — in the
database function (`ka_gochara_window_verification_violations`), in `window_gate.candidate_gate`, and at the writer's
`verify:<class>` step, which refuses a class that cannot pass.

Everything runs on the real applied schema (1081 + 1152–1157 + 1206 + 1240) with the L1 tables stubbed.
"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_verifier as wv
from services.gochara_kernel.dasha_read import make_period_rows_for
from services.gochara_kernel.substrate import SkyEventStore

from .test_a53_inventory import CHART, CHART_ID, DASHA, FULL, H0, H1, P5_EXCL
from .test_a53_p1_support import GEN, _lagna_house, _t, world  # noqa: F401  (fresh AM-5 DB incl. 1240)

CLS = "marriage"
UTC = timezone.utc
SPANS: dict = {}             # {body: [(a, b)]} the seeded residence geometry (Libra) the Swiss stand-in agrees with


@pytest.fixture(autouse=True)
def _consistent_sky(world, monkeypatch):
    """The window phase now verifies each contact span against the ephemeris itself (R8-4): the stand-in must place a
    body in Libra exactly while the seeded crossings say it is there."""
    SPANS.clear()

    def calc(body, jd, ephe):
        t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=UTC)
        return (195.0 if any(a <= t < b for a, b in SPANS.get(body.lower(), ())) else 15.0), 2
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc)


@pytest.fixture(autouse=True)
def _qualification_policy(world):
    """These suites exercise the numbers-enabled `window_qualification/1` semantics; the all-NULL policy has its own
    suites (test_a53_all_null_policy*.py). The policy is the MANIFEST's: the world's manifest step binds it."""
    world.result_policy = "window_qualification/1"


def _libra_edges(path):
    return [e for e in ev.enumerate_edges(CLS, path, CHART)
            if e.transit and e.relation == "residence" and e.obj.canonical_target == "span:7"]


def _materialise(w, path, agents_in_sign, with_natal=False):
    """Materialise `path`'s Libra-residence record(s); `agents_in_sign` = {agent: (in_day_a, in_day_b)} datetimes.
    `with_natal` adds the path's natal-fact edges (P3's māraka testimony rows) — a COMPLETE grain (R10-1)."""
    edges = [e for e in _libra_edges(path) if e.agent in agents_in_sign]
    if with_natal:
        edges += [e for e in ev.enumerate_edges(CLS, path, CHART) if not e.transit]
    rows_for, _ = make_period_rows_for(w.conn, CHART_ID)
    store = rs.RecordStore(w.conn)
    sky = SkyEventStore(w.conn).register_convention()

    def position_at(body, t):
        lo_hi = agents_in_sign.get(body)
        return 195.0 if lo_hi and lo_hi[0] <= t < lo_hi[1] else 15.0
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        return rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, edges=edges,
            horizon=(H0, H1), position_at=position_at, house_for=_lagna_house, sky_convention_id=sky,
            source_fact_ids=["fact-1"], chart=CHART, dasha_rows_for=rows_for)


def _boot_p3(w):
    """A booted generation with ONE admitted P3 record (Saturn in Libra, Jan 10 – Feb 20) and a window for every
    windowed path of the class (P1 and P2 hold no records; P4 needs Jupiter too — zero windows)."""
    w.set_periods([(2, _t(1, 1), _t(2, 1))])
    w.boot()
    w.seed("saturn", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    SPANS["saturn"] = [(_t(1, 10), _t(2, 20))]
    counts = _materialise(w, "P3", {"saturn": (_t(1, 10), _t(2, 20))})
    assert counts["records"] == 1
    return counts


def _windows(w, paths=("P1", "P2", "P3", "P4")):
    """The builder's window steps, then what the SEPARATE verification job persists (R9-6.1: the builder writes no
    verification row; this fixture connects as a superuser, so the job's window half is run on it explicitly)."""
    from ._verification_persist import persist_window_verification
    out = {p: w.step(f"window:{CLS}:{p}") for p in paths}
    persist_window_verification(w.conn, writer_mod, event_class=CLS, generation=GEN, paths=paths)
    return out


def _violations(w):
    return {(v["path_id"], v["violation"]) for v in wg.candidate_gate(w.conn, CHART_ID, GEN, CLS)}


def _db_violations(w):
    return {(r[1], r[3]) for r in w.conn.execute(
        "SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()
        if r[0] == CLS}


def _rows(w):
    return w.conn.execute(
        "SELECT path_id, status, windows_expected, windows_stored, windows_reproduced, windows_unverified,"
        " policy_version FROM public.ka_gochara_eval_window_verification ORDER BY path_id").fetchall()


# ── the writer persists a result per included grain and the gate passes ─────────────────────────────────

def test_the_window_phase_persists_a_verified_result_for_every_included_grain_and_the_gate_passes(world):
    w = world
    _boot_p3(w)
    out = _windows(w)
    # R9-6.1: the BUILDER persists nothing — its notes say so; the rows below are the verification job's (see `_windows`)
    assert all("NOT persisted by the builder" in r.notes for r in out.values()), [r.notes for r in out.values()]
    assert _rows(w) == [("P1", "VERIFIED", 0, 0, 0, 0, "window_qualification/1"),
                        ("P2", "VERIFIED", 0, 0, 0, 0, "window_qualification/1"),
                        ("P3", "VERIFIED", 1, 1, 1, 0, "window_qualification/1"),
                        ("P4", "VERIFIED", 0, 0, 0, 0, "window_qualification/1")]
    assert _violations(w) == set() and _db_violations(w) == set()
    wg.require_candidate_gate(w.conn, CHART_ID, GEN, CLS)                       # does not raise


def test_the_window_persists_its_objective_and_structured_provenance_and_the_verifier_checks_it(world):
    """1240: the objective name/value and the qualification provenance are PERSISTED with the window (not reconstructed
    on demand) and the independent verifier requires them to equal what it derives from the members."""
    w = world
    _boot_p3(w)
    _windows(w, ("P3",))
    (objective, value, qual, score) = w.conn.execute(
        "SELECT objective, objective_value, qualification, score FROM public.ka_gochara_eval_window"
        " WHERE path_id = 'P3'").fetchone()
    # at the 1.0.0 registry the P3 activity_kernel declares no applicability ⇒ the member is unqualified ⇒ the window
    # is NULL — and the persisted provenance says WHY, in structured form
    assert objective == "evidence_for_per_root_sum" and value is None and score is None
    assert qual == {"policy": "window_qualification/1", "unqualified_reason": "applicability_undeclared",
                    "members": 1, "qualified_members": 0,
                    "unresolved": {"applicability_undeclared": 1}, "affected_channels": ["evidence_for_occurrence"]}
    fields = w.conn.execute("SELECT fields_verified FROM public.ka_gochara_eval_window_verification"
                            " WHERE path_id = 'P3'").fetchone()[0]
    assert set(fields) == set(wv.GOVERNED_FIELDS) >= {"objective", "objective_value", "qualification"}
    # a persisted provenance that differs from the verifier's derivation is refused
    for column, bad in (("objective", "'max_min_agent_activity'"),
                        ("qualification", """'{"policy": "window_qualification/1", "unqualified_reason": "other", "members": 1, "qualified_members": 0,
                         "unresolved": {"applicability_undeclared": 1}, "affected_channels": ["evidence_for_occurrence"]}'::jsonb""")):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute(f"UPDATE public.ka_gochara_eval_window SET {column} = {bad} WHERE path_id = 'P3'")
        with pytest.raises(RuntimeError, match="re-derived"):
            wv.verify_window_semantics(
                w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0",
                factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0"))
        _windows(w, ("P3",))                                            # rebuild restores the honest provenance


def test_a_window_without_provenance_is_refused_by_the_verifier_and_the_gate(world):
    w = world
    _boot_p3(w)
    _windows(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("UPDATE public.ka_gochara_eval_window SET objective = NULL, qualification = NULL"
                       " WHERE path_id = 'P3'")
    with pytest.raises(RuntimeError, match="carries no objective/qualification provenance"):
        wv.verify_window_semantics(
            w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0",
            factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0"))
    assert ("P3", "window_provenance_missing") in _db_violations(w)


def test_the_window_table_refuses_an_unqualified_window_that_carries_a_number_and_a_malformed_provenance(world):
    import psycopg
    w = world
    _boot_p3(w)
    _windows(w, ("P3",))
    for label, setter in (
            ("a number on an unqualified window", "score = 0.5"),
            ("an unknown provenance key", """qualification = qualification || '{"extra": 1}'::jsonb"""),
            ("a bad objective token", "objective = 'Bad Objective'"),
            ("provenance without an objective", "objective = NULL")):
        with pytest.raises(psycopg.errors.CheckViolation):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute(f"UPDATE public.ka_gochara_eval_window SET {setter} WHERE path_id = 'P3'")


def test_a_missing_result_fails_the_gate_in_both_the_database_and_the_python_gate(world):
    w = world
    _boot_p3(w)
    _windows(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
    want = {("P3", "window_verification_missing")}
    assert _violations(w) == want and _db_violations(w) == want
    with pytest.raises(wg.CandidateGateRefused, match="window_verification_missing"):
        wg.require_candidate_gate(w.conn, CHART_ID, GEN, CLS)


def test_a_grain_with_no_verification_at_all_is_missing_for_every_included_pin(world):
    w = world
    _boot_p3(w)
    # every included pin is missing its verification; P3 also holds an admitted record that sits in no window yet (the
    # windows were not built) — the R9-2 membership check says so, it is not a verification gap
    assert _violations(w) == {("P1", "window_verification_missing"), ("P2", "window_verification_missing"),
                              ("P3", "window_verification_missing"), ("P4", "window_verification_missing"),
                              ("P3", "window_membership_not_expected")}


def test_unverified_dynamic_and_failed_results_cannot_satisfy_the_gate(world):
    w = world
    _boot_p3(w)
    _windows(w)
    base = wv.verify_window_semantics(
        w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0",
        factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0"))
    digest = w.conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot").fetchone()[0]
    grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
    for status, extra in (("UNVERIFIED_DYNAMIC", dict(unverified_dynamic=1, fully_reproduced=0)),
                          ("FAILED", dict(fully_reproduced=0))):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            wg.record_verification(w.conn, report={**base, "status": status, **extra}, input_digest=digest, **grain)
        assert ("P3", "window_verification_not_verified") in _violations(w)
        assert ("P3", "window_verification_not_verified") in _db_violations(w)
    assert wv.satisfies_gate({**base, "status": "UNVERIFIED_DYNAMIC", "unverified_windows": ["w"]}) is False


def test_a_window_changed_after_verification_is_stale_and_one_deleted_breaks_the_expected_set(world):
    w = world
    _boot_p3(w)
    _windows(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("UPDATE public.ka_gochara_eval_window SET outcome_valence_for_native = 'mixed' WHERE path_id = 'P3'")
    assert ("P3", "window_verification_stale") in _violations(w) and _db_violations(w) == _violations(w)
    # restore, then delete the window itself: an EXPECTED window is now omitted
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window WHERE path_id = 'P3'")
    got = _violations(w)
    assert {("P3", "window_verification_count_mismatch"), ("P3", "window_verification_stale"),
            ("P3", "window_verification_expected_set_mismatch")} <= got and _db_violations(w) == got


def test_a_result_bound_to_another_input_identity_or_an_unknown_policy_is_refused(world):
    w = world
    _boot_p3(w)
    _windows(w)
    base = wv.verify_window_semantics(
        w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0",
        factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0"))
    grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        wg.record_verification(w.conn, report=base, input_digest="f" * 64, **grain)
    assert ("P3", "window_verification_input_mismatch") in _violations(w)
    digest = w.conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot").fetchone()[0]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        wg.record_verification(w.conn, report={**base, "policy_version": "window_qualification/0"},
                               input_digest=digest, **grain)
    assert ("P3", "window_verification_policy_unknown") in _violations(w)
    assert ("P3", "window_verification_policy_unknown") in _db_violations(w)


def test_the_stored_windows_must_be_the_independently_expected_ones_or_nothing_is_persisted(world):
    """A window OMITTED from, or INVENTED in, the stored set is refused before any result row exists."""
    w = world
    _boot_p3(w)
    _windows(w, ("P3",))
    base = wv.verify_window_semantics(
        w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0",
        factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0"))
    grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
    digest = w.conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot").fetchone()[0]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window WHERE path_id = 'P3'")     # OMIT the window
    with pytest.raises(RuntimeError, match="omitted"):
        with w.conn.transaction():
            wg.record_verification(w.conn, report=dict(base, windows_detail=[]), input_digest=digest, **grain)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0


def test_the_python_expected_set_equals_the_databases_recomputation_for_p3_and_p4(world):
    w = world
    w.set_periods([(2, _t(1, 1), _t(2, 1))])
    w.boot()
    w.seed("saturn", [(180.0, _t(1, 25)), (210.0, _t(3, 10))])
    w.seed("jupiter", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    SPANS["saturn"], SPANS["jupiter"] = [(_t(1, 25), _t(3, 10))], [(_t(1, 10), _t(2, 20))]
    _materialise(w, "P3", {"saturn": (_t(1, 25), _t(3, 10))})
    _materialise(w, "P4", {"jupiter": (_t(1, 10), _t(2, 20)), "saturn": (_t(1, 25), _t(3, 10))})
    _windows(w)
    for path, n in (("P3", 1), ("P4", 1)):
        grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, rule_version="1.0.0")
        py = wg.expected_windows(w.conn, **grain)
        sql = w.conn.execute(
            "SELECT public.ka_gochara_eval_window_expected_digest(%s::uuid,%s,%s,%s,%s)",
            (CHART_ID, GEN, CLS, path, "1.0.0")).fetchone()[0]
        assert len(py) == n and wg.intervals_digest(py) == sql, path
        assert wg.intervals_digest(wg.stored_windows(w.conn, **grain)) == w.conn.execute(
            "SELECT public.ka_gochara_eval_window_stored_digest(%s::uuid,%s,%s,%s,%s)",
            (CHART_ID, GEN, CLS, path, "1.0.0")).fetchone()[0]
    # P4's window is the INTERSECTION: [Jan 25, Feb 20), not the union
    (lo, hi), = wg.expected_windows(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P4",
                                    rule_version="1.0.0")
    assert (lo, hi) == (_t(1, 25), _t(2, 20))
    assert _violations(w) == set()


# ── the table's own contract ────────────────────────────────────────────────────────────────────────────

def test_the_table_refuses_an_incoherent_verified_row_and_any_update(world):
    import psycopg
    w = world
    _boot_p3(w)
    _windows(w, ("P3",))
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
    cols = ("chart_id, generation, event_class, path_id, rule_version, verifier_id, verifier_version, status,"
            " policy_version, windows_expected, windows_stored, windows_reproduced, windows_unverified,"
            " expected_windows_digest, stored_windows_digest, windows_content_digest, fields_verified,"
            " input_digest, derivation_inputs_digest, runner_identity")
    h = "a" * 64
    runner = '{"commit": "c0ffee", "implementation_digest": "' + h + '"}'
    ok = [CHART_ID, GEN, CLS, "P3", "1.0.0", "other", "1", "VERIFIED", "p", 1, 1, 1, 0, h, h, h, ["interval"], h, h, runner]
    ins = (f"INSERT INTO public.ka_gochara_eval_window_verification ({cols})"
           " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)")
    for label, mutate in (
            ("VERIFIED with an unverified window", lambda r: r.__setitem__(12, 1)),
            ("VERIFIED reproducing fewer than stored", lambda r: r.__setitem__(11, 0)),
            ("VERIFIED with expected != stored", lambda r: r.__setitem__(9, 2)),
            ("VERIFIED with different interval digests", lambda r: r.__setitem__(14, "b" * 64)),
            ("unknown status", lambda r: r.__setitem__(7, "PASS")),
            ("malformed digest", lambda r: r.__setitem__(13, "xyz")),
            ("empty field coverage", lambda r: r.__setitem__(16, [])),
            ("UNVERIFIED_DYNAMIC with nothing unverified", lambda r: (r.__setitem__(7, "UNVERIFIED_DYNAMIC")))):
        row = list(ok)
        mutate(row)
        with pytest.raises(psycopg.errors.CheckViolation):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute(ins, row)
    with w.conn.transaction():                                              # the coherent row IS accepted ...
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute(ins, ok)
    with pytest.raises(psycopg.errors.Error):                                # ... but rows are immutable
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute("UPDATE public.ka_gochara_eval_window_verification SET status = 'FAILED'")
    with pytest.raises(psycopg.errors.Error):
        w.conn.execute("TRUNCATE public.ka_gochara_eval_window_verification")


def test_a_verification_row_needs_a_finalised_inventory_and_an_included_pin(world):
    import psycopg
    w = world
    _boot_p3(w)
    h = "a" * 64
    ins = ("INSERT INTO public.ka_gochara_eval_window_verification (chart_id, generation, event_class, path_id,"
           " rule_version, verifier_id, verifier_version, status, policy_version, windows_expected, windows_stored,"
           " windows_reproduced, windows_unverified, expected_windows_digest, stored_windows_digest,"
           " windows_content_digest, fields_verified, input_digest, derivation_inputs_digest, runner_identity) VALUES"
           " (%s,%s,%s,%s,'1.0.0','v','1','VERIFIED','p',0,0,0,0,%s,%s,%s,ARRAY['interval'],%s,%s,"
           " '{\"commit\": \"c0ffee\", \"implementation_digest\": \"" + h + "\"}'::jsonb)")
    for cls, path in (("career_entry", "P3"), (CLS, "P5")):         # no inventory for the class / no included pin
        with pytest.raises(psycopg.errors.Error):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute(ins, (CHART_ID, GEN, cls, path, h, h, h, h, h))


def test_the_writers_verify_step_only_reports_and_the_gate_refuses_a_class_without_a_verification(world, monkeypatch):
    """R9-6.1: `verify:<class>` is the builder's in-build self-check — REPORT ONLY. It never raises the candidate gate (the
    builder cannot read it) and never persists; the gate itself refuses a class with no verification result."""
    w = world
    _boot_p3(w)
    _windows(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
    monkeypatch.setattr(writer_mod.gk_contact_certify, "certify_contact_geometry",     # its own suite (R9-3)
                        lambda *a, **k: {"obligations_certified": 0, "contacts_expected": 0, "named_limit": "stubbed"})
    res = w.step(f"verify:{CLS}")
    assert "NOT persisted by the builder" in res.notes and "gate stays CLOSED" in res.notes
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'"
                          ).fetchone()[0] == 0                                  # the builder wrote nothing
    with pytest.raises(wg.CandidateGateRefused, match="window_verification_missing"):
        wg.require_candidate_gate(w.conn, CHART_ID, GEN, CLS)
    _windows(w, ("P3",))                                                         # the verification job's window half
    wg.require_candidate_gate(w.conn, CHART_ID, GEN, CLS)                        # now passes


def test_without_1240_the_writer_says_so_and_does_not_pretend_the_gate_passed(world):
    w = world
    _boot_p3(w)
    with w.conn.transaction():
        w.conn.execute("DROP TABLE public.ka_gochara_eval_window_verification CASCADE")
    res = w.step(f"window:{CLS}:P3")
    assert "NOT persisted by the builder" in res.notes             # the builder never persists, with or without 1240
    assert wg.verification_available(w.conn) is False


def test_a_not_admitted_record_forms_no_expected_window_in_either_derivation(world):
    """The expected set is derived from ADMITTED scored records only — in the verifier (Python) and in the database."""
    w = world
    _boot_p3(w)
    _windows(w, ("P3",))
    assert _violations(w) - {("P1", "window_verification_missing"), ("P2", "window_verification_missing"),
                             ("P4", "window_verification_missing")} == set()
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("UPDATE public.ka_gochara_record_prerequisite SET result = 'false'")
        w.conn.execute("UPDATE public.ka_gochara_relationship_record SET admission_state = 'not_admitted'")
    _windows(w, ("P3",))                                        # the record no longer admits: no window (then re-verified)
    grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
    assert wg.expected_windows(w.conn, **grain) == [] and wg.stored_windows(w.conn, **grain) == []
    assert not {v for p, v in _db_violations(w) if p == "P3"}
    assert not {v for p, v in _violations(w) if p == "P3"}
