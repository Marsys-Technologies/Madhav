"""TR-26 gates added by SR-TR26-PLAN (a) and SR-KGEW-QUAL-BOUND-AMEND-2 (a)(b)(c): G-7 verifier repeat, the certificate-size checks (G-1), the INCONCLUSIVE thresholds (G-4), the truncated-window re-solve
timing (G-5), the read-only certificate / truncation audit and the verdict recorder.  One oracle per distinct claim; the single planted reversion that fails it is named in its docstring.
Doctrine for the numbers: migration 1402 (400 cells, 262,144 bytes), the ruling texts above.  Counts and ids only — no chart value, no date."""
import copy
import json
import re
import uuid
from pathlib import Path

import pytest

import fixtures as fx
import gates
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS, REPORT

HARNESS = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[6]
PROFILE26 = json.loads((HARNESS / "gate_profile.tr26.json").read_text())


def wid(n):
    return str(uuid.UUID(int=n))


def repeat(verdicts, *, truncated=(), g6=(), inconclusive=(), classes=None, unmapped=0, timing=None):
    return {"schema": "ky.verifier_repeat/1", "classes_covered": sorted(classes if classes is not None else fx.CLASSES), "unmapped_verdicts": unmapped, "verdicts": dict(verdicts),
            "truncated_window_ids": list(truncated), "g6_sample_window_ids": list(g6), "inconclusive_windows": list(inconclusive),
            "truncated_resolve": timing or {"windows": len(truncated), "windows_timed": len(truncated), "seconds_total": 9.0, "seconds_max": 3.0, "by_class": {}, "by_path": {}}}


def pair(v1, v2, **kw):
    """Two reports (run 1, run 2) at the same head with equal row digests, each carrying its verifier_repeat."""
    a, b = fx.report(), fx.report()
    a["verifier_repeat"] = repeat(v1, **kw)
    b["verifier_repeat"] = repeat(v2, **{k: v for k, v in kw.items() if k != "g6"})
    for r in (a, b):
        r["verification"]["attestation_recount"]["attested"]["demoted_windows"] = []          # collect_attestation_recount always writes the list
    return a, b


def profile(**over):
    p = fx.profile()
    for k in ("determinism", "certificate_audit", "verification"):
        p[k] = copy.deepcopy(PROFILE26[k])
    p["determinism"] = {"verifier_repeat": p["determinism"]["verifier_repeat"]}          # the kill+resume checks have their own file (test_tr26_resume.py)
    p["runtime"] = {**p["runtime"], "truncated_resolve_report": True}
    p.update(over)
    return p


def g7(a, b, prof=None):
    return gates.g7_determinism(a, b, prof if prof is not None else profile())


def status_of(gate, claim_part):
    return next(c["status"] for c in gate["checks"] if claim_part in c["claim"])


T1, T2, S1 = wid(1), wid(2), wid(3)
BASE = {T1: "AGREED", T2: "INCONCLUSIVE:abc123abc123", S1: "AGREED", wid(4): "AGREED"}


# ── the profile itself ──────────────────────────────────────────────────────────────────────────────────────────

def test_the_tr26_profile_runs_the_26_classes_requires_the_new_detectors_and_pins_the_database_caps():
    """The TR-26 profile lists exactly the 26 classes, switches the four new detectors on, and its two caps are the numbers of migration 1402.  Reversion: any cap or class changed in the profile,
    or a detector switched off."""
    assert PROFILE26["trial_classes"] == list(gates.TRIAL_CLASSES_26)
    assert PROFILE26["determinism"]["verifier_repeat"]["required"] is True and PROFILE26["runtime"]["truncated_resolve_report"] is True
    assert PROFILE26["verification"]["inconclusive_thresholds"] == {"required": True, "per_class_accept": 2, "total_max": 12, "source": "SR-KGEW-QUAL-BOUND-AMEND-2 (b)"}
    sql = (REPO / "platform" / "migrations" / "1402_gochara_qualification_provenance_certificate.sql").read_text()
    assert f"jsonb_array_length(c -> 'cells') <= {PROFILE26['certificate_audit']['max_cells']}" in sql
    assert f"octet_length(c::text) <= {PROFILE26['certificate_audit']['max_bytes']}" in sql
    assert (ts.CERT_MAX_CELLS, ts.CERT_MAX_BYTES) == (PROFILE26["certificate_audit"]["max_cells"], PROFILE26["certificate_audit"]["max_bytes"])
    assert not (HARNESS / "gate_profile.tr14.json").exists()


# ── G-7: the verifier repeat (SR-TR26-PLAN (a)) ─────────────────────────────────────────────────────────────────

def test_g7_passes_when_every_audited_window_has_the_same_verdict_in_both_runs():
    a, b = pair(BASE, BASE, truncated=[T1, T2], g6=[S1])
    g = g7(a, b)
    assert g["status"] == PASS, g["checks"]


def test_g7_fails_when_the_verdict_on_one_truncated_window_differs_between_the_runs():
    """SR-TR26-PLAN (a): a differing verdict on ONE truncated window -> G-7 FAIL.  Reversion: drop the per-window comparison (g7_verifier_repeat_checks) -> this reads PASS."""
    v2 = {**BASE, T2: "AGREED"}                       # run 2 settled the window run 1 left INCONCLUSIVE
    a, b = pair(BASE, v2, truncated=[T1, T2], g6=[S1])
    g = g7(a, b)
    assert g["status"] == FAIL
    chk = next(c for c in g["checks"] if "identical in both runs" in c["claim"])
    assert chk["status"] == FAIL and chk["observed"]["differing"] == 1 and chk["observed"]["examples"][0]["window"] == T2[:8]


def test_g7_fails_when_a_g6_sample_window_differs_even_if_no_truncated_window_does():
    """The audit set is truncated ∪ the G-6 sample.  Reversion: audit only the truncated windows."""
    v2 = {**BASE, S1: "DISAGREEMENT:111111111111"}
    a, b = pair(BASE, v2, truncated=[T1], g6=[S1])
    assert g7(a, b)["status"] == FAIL


def test_g7_sample_comparison_is_not_evaluated_when_no_sample_window_has_a_verdict_in_both_runs_and_counts_those_that_do():
    """NB-2 (SR-TR26-HARNESS-NB; N.8): a G-6 sample made only of exact-re-derivation windows (no solver verdict) compared absent-in-both = vacuous equality, never a pass.  Cases: 0 verdicts -> NOT_EVALUATED;
    verdicts and one differing -> FAIL; verdicts and equal -> PASS, each with `g6_with_verdict` in observed.  Reversion: state = not differ (drop the g6_with_verdict term) -> the first case reads PASS."""
    chk = lambda g: next(c for c in g["checks"] if "identical in both runs" in c["claim"])
    S2 = wid(5)
    none = {k: x for k, x in BASE.items() if k != S1}
    a, b = pair(none, none, truncated=[T1], g6=[S1, S2])
    g = g7(a, b)
    assert chk(g)["status"] == NOT_EVALUATED and chk(g)["observed"]["g6_sample"] == 2 and chk(g)["observed"]["g6_with_verdict"] == 0 and g["status"] == NOT_EVALUATED
    a, b = pair(BASE, BASE, truncated=[T1], g6=[S1, S2])                      # S1 has a verdict in both runs, S2 none: counted once
    g = g7(a, b)
    assert chk(g)["status"] == PASS and chk(g)["observed"]["g6_with_verdict"] == 1 and g["status"] == PASS
    a, b = pair(BASE, {**BASE, S1: "DISAGREEMENT:111111111111"}, truncated=[T1], g6=[S1, S2])
    g = g7(a, b)
    assert chk(g)["status"] == FAIL and chk(g)["observed"]["differing"] == 1 and chk(g)["observed"]["g6_with_verdict"] == 1 and g["status"] == FAIL


def test_g7_ignores_a_difference_on_a_window_outside_the_audit_set():
    """Only the audited windows gate (the ruling's scope).  Reversion: compare every verdict -> FAIL here."""
    v2 = {**BASE, wid(4): "INCONCLUSIVE:ffffffffffff"}
    a, b = pair(BASE, v2, truncated=[T1], g6=[S1])
    assert g7(a, b)["status"] == PASS


def test_g7_is_not_evaluated_without_a_verifier_repeat_record_in_run_2():
    """A build-only second run carries no verdicts: that is no evidence, never a pass.  Reversion: treat the missing record as equal."""
    a, b = pair(BASE, BASE, truncated=[T1], g6=[S1])
    del b["verifier_repeat"]
    assert g7(a, b)["status"] == NOT_EVALUATED


def test_g7_is_not_evaluated_when_a_class_was_not_covered_or_a_verdict_could_not_be_mapped():
    a, b = pair(BASE, BASE, truncated=[T1], g6=[S1], classes=fx.CLASSES[:-1])
    assert g7(a, b)["status"] == NOT_EVALUATED
    a, b = pair(BASE, BASE, truncated=[T1], g6=[S1], unmapped=2)
    assert g7(a, b)["status"] == NOT_EVALUATED


def test_g7_is_not_evaluated_when_a_truncated_window_never_reached_the_solver_check():
    """A truncated window must have a verdict in both runs (its certificate is re-solved).  Reversion: skip the 'reached' check -> an absent==absent comparison would read equal."""
    v = {k: x for k, x in BASE.items() if k != T1}
    a, b = pair(v, v, truncated=[T1], g6=[S1])
    g = g7(a, b)
    assert status_of(g, "reached the verifier's solver check") == NOT_EVALUATED and g["status"] == NOT_EVALUATED


def test_g7_fails_when_the_truncated_sets_differ_and_when_the_demoted_windows_differ():
    a, b = pair(BASE, BASE, truncated=[T1], g6=[S1])
    b["verifier_repeat"]["truncated_window_ids"] = [T1, T2]
    assert status_of(g7(a, b), "truncated windows (solver_certificate.truncated") == FAIL
    a, b = pair(BASE, BASE, truncated=[T1], g6=[S1])
    a["verification"]["attestation_recount"]["attested"]["demoted_windows"] = [{"window_id": T2, "reason": "verifier_budget_exhausted"}]
    b["verification"]["attestation_recount"]["attested"]["demoted_windows"] = []
    assert status_of(g7(a, b), "demote") == FAIL


def test_g7_without_the_profile_switch_is_the_unchanged_row_digest_gate():
    """Backward compatibility: a profile that does not require the repeat (the 12-class profiles) is judged as before."""
    a, b = fx.report(), fx.report()
    assert gates.g7_determinism(a, b, fx.profile())["status"] == PASS
    assert gates.g7_determinism(a, b)["status"] == PASS


# ── G-1: certificate size (SR-KGEW-QUAL-BOUND-AMEND-2 (a)) ──────────────────────────────────────────────────────

def audit(max_cells=310, max_bytes=120000, truncated=0, classes=None):
    return {"classes": {c: {"max_cells": max_cells, "max_bytes": max_bytes, "truncated": truncated} for c in (classes or fx.CLASSES)}}


def cert_status(rep_audit, prof=None):
    r = fx.report()
    if rep_audit is not None:
        r["certificate_audit"] = rep_audit
    return gates.g1_certificate_checks(r, prof or profile())


def test_a_401_cell_certificate_fails_and_so_does_one_byte_over_the_cap():
    """401 cells / 262,145 bytes in any class -> FAIL.  Reversion: compare with >= 402 / drop the check."""
    assert cert_status(audit())[0]["status"] == PASS
    over = audit()
    over["classes"]["major_loss"]["max_cells"] = 401
    c = cert_status(over)[0]
    assert c["status"] == FAIL and c["observed"] == {"major_loss": {"max_cells": 401, "max_bytes": 120000}}
    over = audit()
    over["classes"]["business_launch"]["max_bytes"] = 262145
    assert cert_status(over)[0]["status"] == FAIL
    edge = audit(max_cells=400, max_bytes=262144)
    assert cert_status(edge)[0]["status"] == PASS


def test_the_certificate_check_reports_headroom_per_class_and_is_not_evaluated_without_the_audit():
    c = cert_status(audit(max_cells=310, max_bytes=100000, truncated=2))[0]
    assert c["observed"]["headroom_per_class"]["bereavement"] == {"cells": 90, "bytes": 162144, "truncated_windows": 2}
    assert cert_status(None)[0]["status"] == NOT_EVALUATED
    partial = audit(classes=fx.CLASSES[:-1])
    assert cert_status(partial)[0]["status"] == NOT_EVALUATED


# ── G-4: the INCONCLUSIVE thresholds (SR-KGEW-QUAL-BOUND-AMEND-2 (b)) ───────────────────────────────────────────

def inconclusive(per_class):
    out = []
    for c, n in per_class.items():
        out += [{"event_class": c, "path_id": "P3", "window_id": wid(1000 + len(out)), "reason": "verifier_budget_exhausted"} for _ in range(n)]
    return out


def inc_check(per_class):
    r = fx.report()
    r["verifier_repeat"] = repeat({}, inconclusive=inconclusive(per_class))
    return gates.g4_inconclusive_checks(r, profile())[0]


def test_two_inconclusive_windows_in_a_class_are_accepted_and_disclosed_but_a_third_is_referred():
    """Ruling (b): <=2 in a class accepted + disclosed per window; a 3rd in any class -> REFER-TO-SURROGATE (REPORT), never PASS.  Reversion: per-class limit 3 (or no limit)."""
    ok = inc_check({"major_gain": 2, "relocation": 1})
    assert ok["status"] == PASS and len(ok["observed"]["disclosed"]) == 3
    assert {"event_class", "path_id", "window_id", "reason"} == set(ok["observed"]["disclosed"][0])
    bad = inc_check({"major_gain": 3})
    assert bad["status"] == REPORT and bad["observed"]["classes_over"] == {"major_gain": 3}


def test_twelve_inconclusive_windows_in_total_are_accepted_and_a_thirteenth_is_referred():
    """Ruling (b): more than 12 in total -> REFER, with no class above 2.  Reversion: total limit 13 (or no total limit)."""
    classes = fx.CLASSES
    twelve = {c: 2 for c in classes[:6]}
    assert inc_check(twelve)["status"] == PASS
    thirteen = {**twelve, classes[6]: 1}
    c = inc_check(thirteen)
    assert c["status"] == REPORT and c["observed"]["total_over"] is True and c["observed"]["classes_over"] == {}


def test_the_inconclusive_check_is_not_evaluated_without_the_record_and_is_in_g4_through_evaluate():
    r = fx.report()
    assert gates.g4_inconclusive_checks(r, profile())[0]["status"] == NOT_EVALUATED
    r["verifier_repeat"] = repeat({}, inconclusive=inconclusive({"major_gain": 3}))
    v = gates.evaluate(r, fx.baseline(), profile())
    g4 = v["gates"]["G-4"]
    assert any("INCONCLUSIVE windows are within" in c["claim"] and c["status"] == REPORT for c in g4["checks"]) and g4["status"] == REPORT


# ── G-5: the truncated windows' re-solve time, reported separately (AMEND-2 (c)) ────────────────────────────────

def test_the_truncated_window_resolve_time_is_reported_and_missing_timing_is_not_evaluated():
    """A measurement, not a cap: PASS when every truncated window was timed (zero windows is a measurement of zero), NOT_EVALUATED when one was not.  Reversion: drop the windows==timed check."""
    r = fx.report()
    r["verifier_repeat"] = repeat({}, truncated=[T1, T2], timing={"windows": 2, "windows_timed": 2, "seconds_total": 40.0, "seconds_max": 30.0, "by_class": {"major_gain": {"windows": 2, "seconds": 40.0}}, "by_path": {"P3": {"windows": 2, "seconds": 40.0}}})
    c = gates.g5_truncated_resolve_checks(r, profile())[0]
    assert c["status"] == PASS and c["observed"]["by_path"] == {"P3": {"windows": 2, "seconds": 40.0}}
    r["verifier_repeat"]["truncated_resolve"]["windows_timed"] = 1
    assert gates.g5_truncated_resolve_checks(r, profile())[0]["status"] == NOT_EVALUATED
    assert gates.g5_truncated_resolve_checks(fx.report(), profile())[0]["status"] == NOT_EVALUATED
    assert gates.g5_truncated_resolve_checks(fx.report(), fx.profile()) == []
    v = gates.evaluate(fx.report(), fx.baseline(), profile())
    assert any("re-solve wall time" in c["claim"] for c in v["gates"]["G-5"]["checks"])


# ── the verdict recorder ────────────────────────────────────────────────────────────────────────────────────────

class Verdict:
    def __init__(self, classification, findings=(), inconclusive=()):
        self.classification, self.findings, self.inconclusive = classification, list(findings), list(inconclusive)


def test_the_verdict_fingerprint_is_the_class_and_the_codes_never_the_free_text():
    assert ts.verdict_fingerprint(Verdict("AGREED")) == "AGREED"
    a = ts.verdict_fingerprint(Verdict("INCONCLUSIVE", inconclusive=[("verifier_budget_exhausted", "t=1998-01-01 value 0.5")]))
    b = ts.verdict_fingerprint(Verdict("INCONCLUSIVE", inconclusive=[("verifier_budget_exhausted", "another detail")]))
    c = ts.verdict_fingerprint(Verdict("INCONCLUSIVE", inconclusive=[("tie_ambiguous", "x")]))
    assert a == b and a != c and a.startswith("INCONCLUSIVE:") and "1998" not in a


def test_the_recorder_returns_the_real_verdict_untouched_and_records_id_verdict_inconclusive_and_truncated_timing():
    """The wrapper watches `_certificate_verdict`: identity of the returned object, the verdict by window id, the INCONCLUSIVE window by path/reason, the truncated window's seconds, unmapped counted.
    Reversion: return a copy / record by the wrong key -> the id lookup fails."""
    import datetime as dt
    lo1, lo2, lo3 = (dt.datetime(2000, 1, d, tzinfo=dt.timezone.utc) for d in (1, 2, 3))
    rec = ts.VerdictRecorder("major_gain", {("P3", "1.2.0", lo1): T1, ("P3", "1.2.0", lo2): T2})
    verdicts = {lo1: Verdict("AGREED"), lo2: Verdict("INCONCLUSIVE", inconclusive=[("verifier_budget_exhausted", "d")]), lo3: Verdict("AGREED")}

    def real(window, **kw):
        return verdicts[window["lo"]]
    f = rec.wrap(real)

    def win(lo, trunc):
        return {"path_id": "P3", "rule_version": "1.2.0", "lo": lo, "qualification": {"solver_certificate": {"truncated": trunc}}}
    assert f(win(lo1, False)) is verdicts[lo1] and f(win(lo2, True)) is verdicts[lo2] and f(win(lo3, False)) is verdicts[lo3]
    r = rec.record()
    assert r["verdicts"] == {T1: "AGREED", T2: ts.verdict_fingerprint(verdicts[lo2])} and r["unmapped"] == 1
    assert r["inconclusive"] == [{"event_class": "major_gain", "path_id": "P3", "window_id": T2, "reason": "verifier_budget_exhausted"}]
    assert list(r["truncated_s"]) == [T2] and r["truncated_s"][T2]["path_id"] == "P3"


def test_the_section_merges_classes_takes_run1s_g6_sample_and_sums_the_truncated_timing_by_class_and_path():
    state = {"verifier_verdicts": {"a": {"verdicts": {T1: "AGREED"}, "inconclusive": [], "truncated_s": {T1: {"path_id": "P3", "seconds": 4.0}}, "unmapped": 0},
                                   "b": {"verdicts": {T2: "AGREED"}, "inconclusive": [{"event_class": "b", "path_id": "P3", "window_id": T2, "reason": "r"}], "truncated_s": {}, "unmapped": 0}},
             "crosscheck": {"selection": {"random": [S1], "top_mixed": [T1]}}}
    s = ts.verifier_repeat_section(state, [T1])
    assert s["classes_covered"] == ["a", "b"] and s["verdicts"] == {T1: "AGREED", T2: "AGREED"} and s["g6_sample_window_ids"] == sorted([S1, T1])
    assert s["truncated_resolve"] == {"windows": 1, "windows_timed": 1, "seconds_total": 4.0, "seconds_max": 4.0, "by_class": {"a": {"windows": 1, "seconds": 4.0}}, "by_path": {"P3": {"windows": 1, "seconds": 4.0}}}
    assert ts.verifier_repeat_section({}, None) is None


# ── the read-only audit SQL on a disposable database of the local lane cluster ───────────────────────────────────

ADMIN = "postgresql://postgres@127.0.0.1:55433/postgres"
DDL = "CREATE TABLE public.ka_gochara_eval_window (window_id uuid PRIMARY KEY, chart_id uuid, generation text, event_class text, path_id text, rule_version text, qualification jsonb);"


@pytest.fixture(scope="module")
def audit_db():
    psycopg = pytest.importorskip("psycopg")
    try:
        admin = psycopg.connect(ADMIN, autocommit=True, connect_timeout=3)
    except Exception:                                                                    # noqa: BLE001
        pytest.skip("the local lane cluster 127.0.0.1:55433 is not reachable")
    name = "ky_t26a_" + uuid.uuid4().hex[:8]
    admin.execute(f'CREATE DATABASE "{name}"')
    admin.execute(f"COMMENT ON DATABASE \"{name}\" IS 'ky.job=tr26-audit-tests'")
    try:
        with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{name}", autocommit=True) as c:
            c.execute(DDL)
        yield name
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')                  # only the database this fixture created
        admin.close()


def cert(cells=10, truncated=False, omitted=None, pad=0):
    geometry = {"cuts": [], "pieces": []}
    if omitted is not None:
        geometry["omitted"] = omitted
    return {"schema": "window_solver_certificate/1", "cells": [["piece", 0, 1, 1]] * cells, "geometry": geometry, "truncated": truncated, "pad": "x" * pad}


def put(conn, event_class, qualification):
    conn.execute("INSERT INTO ka_gochara_eval_window VALUES (%s,%s,%s,%s,'P3','1.2.0',%s::jsonb)",
                 (wid(uuid.uuid4().int % 10**9), ts.CHART, ts.GENERATION, event_class, None if qualification is None else json.dumps(qualification)))


def test_the_audit_counts_truncation_by_cause_only_where_a_stored_field_distinguishes_it_and_labels_the_rest_an_upper_bound(audit_db):
    """SR-TR2-TRUNC-AUDIT: cells dropped / geometry bounded are split by `geometry.omitted`; a truncated window without it is cause_unattributed and moves the figure to an UPPER BOUND.
    Also: the TR #2 figure is restricted to the 12 TR #2 classes (`relocation` is a new class); over-cap counts and headroom.  Reversion: count unattributed windows as a cause -> the label stays 'exact'."""
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{audit_db}", autocommit=True) as c:
        c.execute("TRUNCATE ka_gochara_eval_window")
        put(c, "major_loss", {"solver_certificate": cert()})                                                       # a plain window
        put(c, "major_loss", {"solver_certificate": cert(truncated=True, omitted={"cells": 7, "cuts": 0, "pieces": 0})})   # cells dropped
        put(c, "major_loss", {"solver_certificate": cert(truncated=True, omitted={"cells": 0, "cuts": 5, "pieces": 3})})   # byte bound
        put(c, "major_loss", {"unqualified_reason": "x"})                                                            # no certificate
        put(c, "relocation", {"solver_certificate": cert(cells=401, truncated=True)})                                # new class, over the cell cap, no omitted member
        put(c, "relocation", {"solver_certificate": cert(pad=262200)})                                               # over the byte cap
        a = ts.cert_audit(c, ["major_loss", "relocation"])
    ml, rl = a["classes"]["major_loss"], a["classes"]["relocation"]
    assert (ml["windows_total"], ml["with_certificate"], ml["truncated"], ml["cause_cells_only"], ml["cause_geometry_bounded"], ml["cause_unattributed"]) == (4, 3, 2, 1, 1, 0)
    assert (rl["truncated"], rl["cause_unattributed"], rl["over_cells"], rl["over_bytes"], rl["max_cells"]) == (1, 1, 1, 1, 401)
    assert rl["cells_headroom"] == -1 and ml["bytes_headroom"] == 262144 - ml["max_bytes"]
    assert a["tr2_classes"]["classes"] == ["major_loss"] and a["tr2_classes"]["truncated"] == 2
    assert (a["tr2_classes"]["pre_fix_cause_windows"], a["tr2_classes"]["pre_fix_cause_lower_bound"], a["tr2_classes"]["pre_fix_cause_label"]) == (1, 1, "exact")
    assert a["all_classes"]["pre_fix_cause_label"] == "upper_bound" and a["all_classes"]["pre_fix_cause_windows"] == 2 and a["cause_split_complete"] is False
    assert not re.search(r"\d{4}-\d\d-\d\d", json.dumps(a))                                                       # counts only


def test_the_truncated_id_select_returns_exactly_the_truncated_windows(audit_db):
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{audit_db}", autocommit=True) as c:
        c.execute("TRUNCATE ka_gochara_eval_window")
        c.execute("INSERT INTO ka_gochara_eval_window VALUES (%s,%s,%s,'major_loss','P3','1.2.0',%s::jsonb)", (T1, ts.CHART, ts.GENERATION, json.dumps({"solver_certificate": cert(truncated=True)})))
        c.execute("INSERT INTO ka_gochara_eval_window VALUES (%s,%s,%s,'major_loss','P3','1.2.0',%s::jsonb)", (T2, ts.CHART, ts.GENERATION, json.dumps({"solver_certificate": cert()})))
        assert ts.truncated_window_ids(c, ["major_loss"]) == [T1]


# ── G-1: the baseline is the trial's own (SR-TR26-PLAN (b)) ─────────────────────────────────────────────────────

def test_the_baseline_must_have_been_built_at_the_trials_head_by_a_passing_oracle():
    """SR-TR26-PLAN (b): a VM-made baseline vouches only for the head it was built at.  Reversion: drop the head comparison (g1_baseline_provenance_checks) -> a baseline of another head reads PASS."""
    r = fx.report()
    base = {**fx.baseline(), "code": {"head": r["code"]["head"]}, "oracle": {"passed": True}}
    prof = profile(baseline_provenance=PROFILE26["baseline_provenance"])
    ok = gates.g1_baseline_provenance_checks(r, base, prof)
    assert [c["status"] for c in ok] == [PASS, PASS]
    other = {**base, "code": {"head": "b" * 40}}
    assert gates.g1_baseline_provenance_checks(r, other, prof)[0]["status"] == FAIL
    assert gates.g1_baseline_provenance_checks(r, {**base, "oracle": {"passed": False}}, prof)[1]["status"] == FAIL
    assert gates.g1_baseline_provenance_checks(r, fx.baseline(), prof)[0]["status"] == NOT_EVALUATED          # no code.head in a baseline: unknown, not equal
    assert gates.g1_baseline_provenance_checks(r, base, fx.profile()) == [] and PROFILE26["baseline_provenance"]["required"] is True


def test_the_recorder_wraps_a_function_the_verifier_really_has_with_the_signature_the_wrapper_forwards():
    """Drift guard: the verdict recorder replaces `window_verifier._certificate_verdict`; if the verifier renames it or changes its call shape the recorder would record nothing (G-7 NOT_EVALUATED),
    so the shape is pinned here against the real module.  Reversion: rename the wrapped attribute in trial_slice.verify_stage."""
    wv = pytest.importorskip("services.gochara_kernel.window_verifier")
    import inspect
    params = inspect.signature(wv._certificate_verdict).parameters
    assert list(params)[0] == "window" and {"records", "objective", "position_at", "against_evaluated", "ov"} <= set(params)
    assert "_certificate_verdict" in (HARNESS / "trial_slice.py").read_text()
    assert {"classification", "findings", "inconclusive"} <= set(wv._cc.CertReport.__dataclass_fields__)
