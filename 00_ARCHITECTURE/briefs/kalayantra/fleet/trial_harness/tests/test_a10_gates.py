"""A10.1 evaluator (task T1B): the G-3 decision table, forbidden reasons and caps, noninterference, the digests record, the effective wall and G-0 TRIAL_READY/1.
One oracle per distinct claim, the source in each docstring (PLAN v2 §5, PLAN_A10_1 §2/§3, RECONCILIATION N3); every world is synthetic.  T14's detector — the
evaluator must read FALSE on a planted forbidden reason or a cap breach — is `test_t14_*`.  Each test breaks exactly ONE thing in a fully passing A10.1 world."""
import copy
import json

import pytest

import fixtures as fx
import gates
import trial_eval as te
from gates import FAIL, NOT_EVALUATED, PASS, REPORT

# ── the plan's own table, restated literally (PLAN v2 §5; carried by PLAN_A10_1 §9) — NOT read from the data file ──────────────────────────────────────
PLAN_FLOORS = {"P1": 0.90, "P2": 0.85, "P3": 0.92, "P4": 0.95, "P3+P4": 0.90, "ALL": 0.88}
PLAN_ALLOWED = {"state_boundaries_incomplete", "solver_budget_exhausted", "monotone_arc_not_established", "solver_certificate_incomplete", "obstructor_residence_unknown",
                "node_residence_unknown", "verifier_budget_exhausted", "tie_isolation_unresolved", "tie_ambiguous", "dasha_horizon_exhausted"}
PLAN_FORBIDDEN = ["applicability_undeclared", "value_mapping_undeclared", "vedha_overlay_not_bound", "orb_not_ratified", "dynamic_objective_solver_guarantee_not_available",
                  "agent_nature_node_undecided", "node_obstruction_undecided", "node_dignity_unclassified"]


def run10(rep=None, base=None, prof=None, table=None, **kw):
    r, b, p = fx.a10_good()
    kw.setdefault("second_report", fx.second())
    kw.setdefault("dispatch_modules", fx.dispatch_modules())
    kw.setdefault("dispatch_digests", fx.dispatch_digests())
    return gates.evaluate(rep if rep is not None else r, base if base is not None else b, prof if prof is not None else p,
                          decision_table=table if table is not None else fx.decision_table(), **kw)


def status(v, gid):
    return v["gates"][gid]["status"]


def row_check(v, prefix):
    hits = [c for c in v["gates"]["G-3"]["checks"] if c["claim"].startswith(prefix)]
    assert len(hits) == 1, (prefix, [c["claim"] for c in v["gates"]["G-3"]["checks"]])
    return hits[0]


def with_numbered(**per_path):
    """The A10.1 world with some paths' numbered counts changed — every dependent total kept consistent so ONLY the shares move."""
    r = fx.a10_report()
    for p, n in per_path.items():
        r["paths"][p]["numbered"] = n
    peak = sum(v["numbered"] for v in r["paths"].values())
    r["totals"]["with_peak"], r["totals"]["blank"] = peak, 1800 - peak
    extra = r["totals"]["blank"] - sum(r["totals"]["blank_reasons"].values())        # the census must account for every blank window: the extra ones carry an ALLOWED reason
    for where in (r["totals"]["blank_reasons"], r["reason_windows_any"]):
        where["state_boundaries_incomplete"] += extra
    r["totals"]["unresolved_factors_in_blank_windows"]["state_boundaries_incomplete"]["windows"] += extra
    r["verification"]["generation_verdict"]["numbered_windows"] = peak
    r["verification"]["attestation_recount"] = {"attested": {"windows": 1800, "numbered": peak}, "live": {"windows": 1800, "numbered": peak}}
    r["crosscheck"].update({"numbered_windows": peak, "sampled": max(50, -(-3 * peak // 100))})
    return r


# ── the control ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_control_every_gate_g0_to_g8_passes_and_only_a_final_profile_dispatches():
    v = run10()
    assert [status(v, g) for g in ("G-0",) + gates.GATE_IDS] == [PASS] * 9, {g: x["checks"] for g, x in v["gates"].items() if x["status"] != PASS}
    assert v["overall"] == "ALL_GATES_PASS_PROFILE_NOT_FINAL" and not v["dispatchable"] and v["decision_table"]["sha256"] == fx.decision_table()["sha256"]
    assert run10(prof=fx.profile(final=True))["overall"] == "DISPATCH_GATE_MET"


# ── (1) the G-3 decision table, the forbidden list and the caps are DATA, and they are the plan's ─────────────────────────────────────────────────────

def test_the_shipped_table_is_the_plan_v2_section_5_table():
    """PLAN v2 §5, row by row: floors 90/85/92/95/90/88, shortfall REPORT, forbidden REFUSE, caps 0.5 %/0.5 %, the 10 allowed and 8 forbidden reasons."""
    t = fx.decision_table()
    assert {r["id"]: r["floor"] for r in t["rows"]} == PLAN_FLOORS
    assert {(r["shortfall"], r["forbidden"]) for r in t["rows"]} == {("REPORT", "REFUSE")}
    assert {c["id"]: (c["max_share"], c["above"]) for c in t["caps"]} == {"solver_budget_exhausted": (0.005, "REFUSE"), "inconclusive": (0.005, "REFUSE")}
    assert set(t["allowed_reasons"]) == PLAN_ALLOWED and sorted(t["forbidden_reasons"]) == sorted(PLAN_FORBIDDEN)
    assert {tuple(r["paths"]) for r in t["rows"]} == {("P1",), ("P2",), ("P3",), ("P4",), ("P3", "P4"), ("*",)}


@pytest.mark.parametrize("mutate,why", [
    (lambda t: t.__setitem__("forbidden_reasons", t["forbidden_reasons"] + [t["allowed_reasons"][0]]), "a reason both allowed and forbidden"),
    (lambda t: t.pop("caps"), "a missing section"),
    (lambda t: t["rows"][0].__setitem__("floor", 1.5), "a floor above 1"),
    (lambda t: t["rows"][0].__setitem__("shortfall", "IGNORE"), "a shortfall outcome that is not REPORT"),
    (lambda t: t["caps"][0].__setitem__("reasons", ["not_an_allowed_reason"]), "a cap on a reason the table does not allow"),
    (lambda t: t["noninterference"].__setitem__("kinds", ["windows"]), "noninterference kinds that are not the four"),
    (lambda t: t.__setitem__("surprise", 1), "an unknown key"),
])
def test_an_unusable_table_is_refused_not_defaulted(mutate, why):
    """A gate without its table would be a silent default: the loader refuses (the driver turns the refusal into exit 2 before any work)."""
    raw = json.loads(fx.TABLE_PATH.read_text())
    mutate(raw)
    with pytest.raises(gates.DecisionTableError):
        gates.load_decision_table(raw)


def test_the_table_digest_moves_with_any_value():
    raw = json.loads(fx.TABLE_PATH.read_text())
    a = gates.load_decision_table(raw)["sha256"]
    raw["rows"][0]["floor"] = 0.89
    assert gates.load_decision_table(raw)["sha256"] != a


def test_the_evaluator_without_a_table_is_the_pre_a10_one():
    r, b, p = fx.good()
    v = gates.evaluate(r, b, p, second_report=fx.second(), dispatch_modules=fx.dispatch_modules())
    assert "G-0" not in v["gates"] and "decision_table" not in v and status(v, "G-3") == PASS


# ── T14: the evaluator reads FALSE on a planted forbidden reason or a cap breach ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("reason", PLAN_FORBIDDEN)
@pytest.mark.parametrize("where", ["secondary", "primary"])
def test_t14_a_planted_forbidden_reason_refuses_g3(reason, where):
    """PLAN v2 §5 'Forbidden (zero required)': one window carrying any of the eight reasons — as its primary reason or only as a secondary one — is a REFUSAL."""
    r = fx.a10_report()
    if where == "primary":
        r["totals"]["blank_reasons"][reason] = 1
    r["reason_windows_any"][reason] = 1
    v = run10(r)
    assert status(v, "G-3") == FAIL and v["overall"] == "NO_DISPATCH"
    assert row_check(v, "no forbidden reason")["status"] == FAIL and reason in row_check(v, "no forbidden reason")["observed"]


def test_a_forbidden_reason_also_refuses_g2_by_the_same_list():
    """PLAN v2 §4.4 'G-2 (wiring complete, with the new forbidden list)': G-2 reads the table's list, including the three reasons the Q4/Q9 rulings removed."""
    r = fx.a10_report()
    r["reason_windows_any"]["node_obstruction_undecided"] = 2
    v = run10(r)
    zero = [c for c in v["gates"]["G-2"]["checks"] if "node_obstruction_undecided" in c["claim"]]
    assert status(v, "G-2") == FAIL and len(zero) == 1 and zero[0]["status"] == FAIL      # the zero-check of THAT reason, not only the closed-set check


def test_t14_a_reason_outside_the_closed_set_refuses_g3():
    """PLAN v2 §5 'Allowed blank reasons (closed set; a reason outside it fails)'.  `all_null_candidate_policy` is the stored reason of the wrong policy."""
    r = fx.a10_report()
    r["totals"]["blank_reasons"]["all_null_candidate_policy"] = 1
    r["reason_windows_any"]["all_null_candidate_policy"] = 1
    v = run10(r)
    assert status(v, "G-3") == FAIL and row_check(v, "no blank reason outside")["status"] == FAIL


@pytest.mark.parametrize("n,expect", [(9, PASS), (10, FAIL)])
def test_t14_a_solver_budget_exhausted_cap_breach_refuses(n, expect):
    """PLAN v2 §5: `solver_budget_exhausted` ≤ 0.5 % of windows, REFUSE above — 9 of 1,800 is the cap, 10 is a breach."""
    r = fx.a10_report()
    r["reason_windows_any"]["solver_budget_exhausted"] = n
    v = run10(r)
    assert row_check(v, "solver_budget_exhausted ≤")["status"] == expect and (status(v, "G-3") == FAIL) == (expect == FAIL)


@pytest.mark.parametrize("n,expect", [(9, PASS), (10, FAIL)])
def test_t14_an_inconclusive_cap_breach_refuses(n, expect):
    """PLAN v2 §5: INCONCLUSIVE (R-6) ≤ 0.5 % of windows, REFUSE above (a breach predicts a seal refusal after a ~4 h build).  The INCONCLUSIVE reasons are the
    three of PLAN_A10_1 T15 (tie_ambiguous, tie_isolation_unresolved, verifier_budget_exhausted), summed."""
    r = fx.a10_report()
    r["reason_windows_any"].update({"tie_ambiguous": n - 6, "tie_isolation_unresolved": 3, "verifier_budget_exhausted": 3})
    v = run10(r)
    assert row_check(v, "inconclusive ≤")["status"] == expect and (status(v, "G-3") == FAIL) == (expect == FAIL)


def test_the_cap_is_a_share_of_ALL_windows_and_an_empty_run_is_not_a_pass():
    r = fx.a10_report()
    r["totals"]["windows_total"] = 0
    v = run10(r)
    assert row_check(v, "solver_budget_exhausted ≤")["status"] == NOT_EVALUATED


# ── the floor rows: PASS at the floor, REPORT below it with allowed reasons, FAIL below it with an outside reason ────────────────────────────────

def test_every_floor_row_passes_exactly_at_its_floor():
    """PLAN v2 §5: P1 ≥ 90 %, P2 ≥ 85 %, P3 ≥ 92 %, P4 ≥ 95 %, P3∪P4 ≥ 90 %, All ≥ 88 % — a share equal to the floor is met."""
    v = run10(with_numbered(P1=540, P2=595, P3=92, P4=380))              # exactly .90 / .85 / .92 / .95 ; P3+P4 = 472/500 ; ALL = 1607/1800
    for prefix in ("P1 numbered", "P2 numbered", "P3 numbered", "P4 numbered", "P3+P4 numbered", "ALL numbered"):
        assert row_check(v, prefix)["status"] == PASS, row_check(v, prefix)


@pytest.mark.parametrize("row,numbers", [
    ("P1 numbered", {"P1": 539}),                                         # .8983 < .90
    ("P2 numbered", {"P2": 594}),                                         # .8486 < .85
    ("P3 numbered", {"P3": 91}),                                          # .91   < .92
    ("P4 numbered", {"P4": 379}),                                         # .9475 < .95
    ("P3+P4 numbered", {"P3": 90, "P4": 359}),                            # 449/500 = .898 < .90
    ("ALL numbered", {"P1": 440}),                                        # 1445/1800 = .803 < .88
])
def test_a_shortfall_with_every_blank_reason_allowed_is_reported_to_the_surrogate_not_refused(row, numbers):
    """PLAN v2 §5: 'a shortfall whose blank reasons are all allowed is REPORTED to the surrogate for a dispatch ruling, not an automatic refusal'."""
    v = run10(with_numbered(**numbers))
    assert row_check(v, row)["status"] == REPORT
    assert status(v, "G-3") == REPORT and v["reported"] == ["G-3"] and v["overall"] == "NO_DISPATCH_REPORT_TO_SURROGATE" and not v["dispatchable"]
    assert run10(with_numbered(**numbers), prof=fx.profile(final=True))["dispatchable"] is False


def test_a_shortfall_beside_a_reason_outside_the_allowed_set_is_a_refusal_not_a_report():
    """PLAN v2 §5: 'a defect (a reason outside the set) stays a refusal' — the row's OWN blank reasons decide."""
    r = with_numbered(P2=594)
    r["paths"]["P2"]["blank_by_reason"] = {"node_obstruction_undecided": 106}
    v = run10(r)
    assert row_check(v, "P2 numbered")["status"] == FAIL and status(v, "G-3") == FAIL


def test_a_rows_shortfall_is_judged_by_its_own_paths_reasons():
    """P1's shortfall is blank only for an allowed reason; the defect sits in P2's windows: P1 is still a REPORT (and the run is refused by the forbidden check)."""
    r = with_numbered(P1=539)
    r["paths"]["P1"]["blank_by_reason"] = {"state_boundaries_incomplete": 61}
    r["paths"]["P2"]["blank_by_reason"] = {"node_obstruction_undecided": 1}
    v = run10(r)
    assert row_check(v, "P1 numbered")["status"] == REPORT and status(v, "G-3") == FAIL


def test_a_path_with_no_windows_is_not_evaluated_never_vacuously_met():
    r = fx.a10_report()
    r["paths"]["P3"] = {"windows": 0, "numbered": 0}
    assert row_check(run10(r), "P3 numbered")["status"] == NOT_EVALUATED


def test_report_outranks_pass_and_is_outranked_by_unknown_and_refusal():
    c = lambda s: {"status": s}                                            # noqa: E731
    assert gates.roll_up([c(PASS), c(REPORT)]) == REPORT
    assert gates.roll_up([c(REPORT), c(NOT_EVALUATED)]) == NOT_EVALUATED
    assert gates.roll_up([c(REPORT), c(FAIL)]) == FAIL


# ── (2) noninterference: natural keys, not counts (RECONCILIATION N3; PLAN v2 §4.4 G-7) ─────────────────────────────────────────────────────────────

def _with_trial_snapshot(tweak=None, versions=None, geometry="g" * 64):
    r = fx.a10_report()
    r["noninterference"] = fx.snapshot(geometry=geometry, versions=versions, tweak=tweak)
    return r


def _ni(v, kind):
    return [c for c in v["gates"]["G-7"]["checks"] if c["claim"].startswith(f"{kind}: natural keys")][0]


def test_noninterference_equal_snapshots_pass():
    v = run10()
    assert status(v, "G-7") == PASS and all(_ni(v, k)["status"] == PASS for k in gates.NONINTERFERENCE_KINDS)


def test_a_moved_window_boundary_that_keeps_every_count_is_caught():
    """GPT N3: 'A moved boundary ... can preserve every count.'  Same number of windows, one end moved a day."""
    def move(k):
        g, rv, key = k["windows"][0]
        k["windows"][0] = (g, rv, key.replace("1998-02-01", "1998-02-02"))
    v = run10(_with_trial_snapshot(move))
    assert _ni(v, "windows")["status"] == FAIL and _ni(v, "windows")["observed"]["count"] == [2, 2] and status(v, "G-7") == FAIL
    assert _ni(v, "windows")["observed"]["differing_groups"] == ["bereavement|P1"]


def test_a_substituted_contact_that_keeps_the_count_is_caught():
    """GPT N3: 'a substituted contact'.  MB-3.2 contact key: contact_id + t_in, t_out, t_exact, delta_lambda."""
    v = run10(_with_trial_snapshot(lambda k: k["contacts"].__setitem__(0, ("contacts|-", "-", '["c2","1998-01-01T00:00:00.000000",null,null,"0.5"]'))))
    assert _ni(v, "contacts")["status"] == FAIL and _ni(v, "contacts")["observed"]["count"] == [1, 1]


def test_a_changed_membership_pair_that_keeps_the_count_is_caught():
    """GPT N3: 'changed membership'."""
    v = run10(_with_trial_snapshot(lambda k: k["membership"].__setitem__(0, ("bereavement|P1", "1.2.0", '[["w"],["r2"]]'))))
    assert _ni(v, "membership")["status"] == FAIL


def test_a_moved_support_interval_is_caught():
    """MEASURING_BUILD_CONTRACT T3.2: one support interval moved changes the (class, path) digest; supports carry admission_state/operator_role too."""
    v = run10(_with_trial_snapshot(lambda k: k["supports"].__setitem__(0, ("bereavement|P1", "1.2.0", k["supports"][0][2].replace('"admitted"', '"refused"')))))
    assert _ni(v, "supports")["status"] == FAIL and status(v, "G-7") == FAIL


def test_the_snapshot_is_order_independent_and_key_sensitive():
    two = [("bereavement|P1", "1.2.0", '["x"]'), ("bereavement|P1", "1.2.0", '["y"]')]          # two keys in ONE group, in either order
    a = fx.snapshot(tweak=lambda k: k["windows"].extend(two))
    assert a == fx.snapshot(tweak=lambda k: k["windows"].extend(reversed(two))) and a["kinds"]["windows"]["groups"]["bereavement|P1"]["count"] == 3
    a = fx.snapshot()
    changed = fx.snapshot(tweak=lambda k: k["windows"].append(("bereavement|P1", "1.2.0", '["x"]')))
    assert changed["kinds"]["windows"]["sha256"] != a["kinds"]["windows"]["sha256"] and changed["kinds"]["windows"]["count"] == 3


def test_the_rule_version_is_not_part_of_a_window_key():
    """GPT N3 'allowing only explicitly changed rule-version identities': the same windows under 1.3.0 have the same key digest; the version is reported per path."""
    a = fx.snapshot()
    b = fx.snapshot(tweak=lambda k: k.__setitem__("windows", [(g, "1.3.0", key) for g, _, key in k["windows"]]))
    assert a["kinds"]["windows"] == b["kinds"]["windows"] and a["rule_versions"] != b["rule_versions"]


def test_an_undeclared_rule_version_change_is_a_failure_and_a_declared_one_is_allowed():
    """The rule-version identity may change only when the table DECLARES it ({path, from, to})."""
    base = fx.a10_baseline()
    base["noninterference"]["rule_versions"] = {"P1": ["1.2.0"], "P2": ["1.2.0"]}
    r = _with_trial_snapshot(versions={"P1": ["1.2.0"], "P2": ["1.3.0"]})
    v = run10(r, base)
    rv = [c for c in v["gates"]["G-7"]["checks"] if c["claim"].startswith("rule-version identities")][0]
    assert rv["status"] == FAIL and "P2" in rv["observed"]
    raw = json.loads(fx.TABLE_PATH.read_text())
    raw["noninterference"]["declared_rule_version_changes"] = [{"path": "P2", "from": "1.2.0", "to": "1.3.0"}]
    ok = run10(r, base, table=gates.load_decision_table(raw))
    assert [c for c in ok["gates"]["G-7"]["checks"] if c["claim"].startswith("rule-version identities")][0]["status"] == PASS


def test_a_declared_change_does_not_excuse_another_path():
    base = fx.a10_baseline()
    base["noninterference"]["rule_versions"] = {"P1": ["1.2.0"], "P2": ["1.2.0"]}
    raw = json.loads(fx.TABLE_PATH.read_text())
    raw["noninterference"]["declared_rule_version_changes"] = [{"path": "P2", "from": "1.2.0", "to": "1.3.0"}]
    r = _with_trial_snapshot(versions={"P1": ["1.3.0"], "P2": ["1.3.0"]})
    v = run10(r, base, table=gates.load_decision_table(raw))
    assert [c for c in v["gates"]["G-7"]["checks"] if c["claim"].startswith("rule-version identities")][0]["status"] == FAIL


@pytest.mark.parametrize("trial_geo,base_geo", [("h" * 64, "g" * 64), (None, None)])
def test_a_different_or_unknown_geometry_configuration_is_not_evaluated_never_equal(trial_geo, base_geo):
    """PLAN v2 G-7: 'at the same geometry configuration'.  Two unknowns are not equal."""
    base = fx.a10_baseline()
    base["noninterference"] = fx.snapshot(geometry=base_geo)
    v = run10(_with_trial_snapshot(geometry=trial_geo), base)
    assert status(v, "G-7") == NOT_EVALUATED


def test_a_baseline_made_before_a10_has_no_snapshot_and_reads_not_evaluated():
    base = fx.a10_baseline()
    del base["noninterference"]
    assert status(run10(base=base), "G-7") == NOT_EVALUATED
    r = fx.a10_report()
    r["noninterference"] = None
    assert status(run10(r), "G-7") == NOT_EVALUATED


# ── the digests record (PLAN v2 G-8: a later L0 or config change invalidates the trial) ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("component,over", [
    ("registry", {"registry": "R" * 64}),
    ("l0", {"l0": {"bg_transit_rules": "L" * 64}}),
    ("ephemeris", {"ephemeris": {"backend": "swiss", "swe_version": "2.10", "library_sha256": "s" * 64, "platform": "linux/amd64", "files": {"sepl_18.se1": "X" * 64}, "probe_digest": "p" * 64}}),
    ("convention", {"node": {"model": "true"}}),
    ("orb_policy", {"orb_policy": {"admission_digest": "O" * 64, "activity": {"1.3.0": "1.0"}}}),
    ("rulings", {"rulings_digest": "U" * 64}),
    ("config", {"result_policy": "all_null_candidate/1"}),
])
def test_each_digest_component_moves_with_its_own_source_and_g8_refuses_the_dispatch_that_differs(component, over):
    base = fx.digests()
    changed = fx.digests(**over)
    moved = [c for c in gates.DIGEST_COMPONENTS if base["components"][c] != changed["components"][c]]
    assert moved == [component]
    v = run10(dispatch_digests=changed)
    c = [x for x in v["gates"]["G-8"]["checks"] if x["claim"].startswith("registry, L0")][0]
    assert c["status"] == FAIL and c["observed"] == [component] and status(v, "G-8") == FAIL


def test_trial_scope_keys_are_not_config():
    """EQUIVALENCE_RECORD §3.3 P1: the trial's own scope (test_slice, scored_classes, horizon_basis, stored_scope) is excluded from the comparison by name."""
    a = fx.digests()
    b = fx.digests(scored_classes=["bereavement"], test_slice={"classes": 1}, horizon_basis={"kind": "x"}, stored_scope="trial_slice")
    assert a["components"] == b["components"]


def test_missing_digests_are_not_evaluated_never_equal():
    r = fx.a10_report()
    r["digests_record"] = None
    assert status(run10(r), "G-8") == NOT_EVALUATED
    assert status(run10(dispatch_digests=None), "G-8") == NOT_EVALUATED
    r2 = fx.a10_report()
    del r2["digests_record"]["components"]["l0"]
    assert status(run10(r2), "G-8") == NOT_EVALUATED


def test_an_unreadable_manifest_vector_gives_no_record_rather_than_an_empty_one():
    assert te.digests_record(None) is None and te.digests_record({"registry": "x"}) is None


# ── (5) G-5 effective wall, T17: compute and lock wait SEPARATELY ──────────────────────────────────────────────────────────────────────────────────

def test_the_clock_splits_wall_into_compute_and_lock_wait():
    """T17: wall 10 s with 20 sampled waits at 0.25 s → 5 s of lock wait, 5 s of compute, reported as separate numbers that sum to the wall."""
    c = te.StageClock(lambda: False, interval_s=0.25)
    c.add("build:record", 10.0, 20, 40)
    s = c.record()["stages"]["build:record"]
    assert (s["wall_s"], s["lock_wait_s"], s["compute_s"]) == (10.0, 5.0, 5.0)


def _sample_until(n, **kw):
    """Run a block on a clock whose probe answers `kw['answer']` until the probe has been asked `n` times (no timing assumption)."""
    import time
    calls = {"n": 0}

    def probe():
        calls["n"] += 1
        return kw["answer"]
    c = te.StageClock(probe, interval_s=0.01)
    with c.measure("build:x"):
        t0 = time.time()
        while calls["n"] < n and time.time() - t0 < 20:
            time.sleep(0.005)
    return c.record()["stages"]["build:x"]


def test_the_clock_measures_a_real_block_with_a_probe_that_always_waits():
    s = _sample_until(5, answer=True)
    assert s["waiting_samples"] >= 5 and s["lock_wait_s"] > 0 and abs(s["compute_s"] + s["lock_wait_s"] - s["wall_s"]) < 0.01


def test_a_probe_that_never_answers_gives_unknown_lock_wait_not_zero():
    s = _sample_until(5, answer=None)
    assert s["lock_wait_s"] is None and s["compute_s"] is None
    c2 = te.StageClock(lambda: None, interval_s=0.02)
    c2.load({"stages": {"build:x": s}})                         # unknown survives a resume
    assert c2.record()["stages"]["build:x"]["lock_wait_s"] is None


def test_a_probe_that_says_no_one_waits_gives_zero_lock_wait():
    s = _sample_until(5, answer=False)
    assert s["lock_wait_s"] == 0 and s["compute_s"] == s["wall_s"]


def test_the_stage_name_may_be_resolved_after_the_block():
    c = te.StageClock(lambda: False, interval_s=0.5)
    box = {}
    with c.measure(lambda: "build:" + box.get("kind", "empty")):
        box["kind"] = "record"
    assert list(c.record()["stages"]) == ["build:record"]


def test_g5_without_a_measured_lock_wait_is_not_evaluated():
    """T17 detector: 'harness cannot report lock wait separately from compute' reads false."""
    r = fx.a10_report()
    for st in r["effective_wall"]["stages"].values():
        st["lock_wait_s"] = st["compute_s"] = None
    assert status(run10(r), "G-5") == NOT_EVALUATED
    r2 = fx.a10_report()
    del r2["effective_wall"]
    assert status(run10(r2), "G-5") == NOT_EVALUATED


def test_g5_compute_that_does_not_add_up_to_the_wall_fails():
    """A lock wait reported as part of compute (or dropped) breaks wall = compute + lock wait."""
    r = fx.a10_report()
    st = r["effective_wall"]["stages"]["build:record"]
    st["compute_s"] = st["wall_s"]                                # lock wait counted as compute as well
    v = run10(r)
    assert status(v, "G-5") == FAIL


def test_g5_the_cap_is_on_the_effective_wall_not_on_compute_alone():
    """PLAN v2 §4.4 G-5: builder (base_s + solver_s)·r ≤ 43,200 s measured wall.  Compute alone projects under the limit; the lock wait takes it over → FAIL."""
    r = fx.a10_report()
    for name, st in r["effective_wall"]["stages"].items():
        st["wall_s"], st["compute_s"], st["lock_wait_s"] = 40.0, 10.0, 30.0           # 8 build stages → compute 80 s, lock wait 240 s, then × 26/12
    r["effective_wall"]["stages"]["build:record"].update({"wall_s": 20000.0, "compute_s": 6000.0, "lock_wait_s": 14000.0})
    v = run10(r, prof=fx.profile(final=True))
    ew = [c for c in v["gates"]["G-5"]["checks"] if c["claim"].startswith("projected effective wall")][0]
    assert ew["observed"]["projected_compute_s"] < 43200 < ew["observed"]["effective_s"] and ew["status"] == FAIL


# ── G-0 TRIAL_READY/1 ──────────────────────────────────────────────────────────────────────────────────────────

def _g0(tr):
    r = fx.a10_report()
    r["trial_ready"] = tr
    return run10(r)


def test_g0_passes_only_on_a_ready_evaluation_at_this_trials_head():
    assert status(_g0(fx.trial_ready()), "G-0") == PASS


def test_g0_a_false_check_fails_even_when_the_ready_flag_says_true():
    """§N.8: G-0 recomputes readiness from the embedded checks, never off the evaluator's own flag alone."""
    tr = fx.trial_ready()
    tr["checks"][13]["value"] = False                           # T14
    v = _g0(tr)
    assert status(v, "G-0") == FAIL and v["overall"] == "NO_DISPATCH"


def test_g0_a_null_or_missing_check_is_not_ready_and_not_a_pass():
    """TRIAL_READY/1: 'a check whose evidence cannot be read is null and counts as not ready'."""
    tr = fx.trial_ready()
    tr["checks"][4]["value"] = None
    assert status(_g0(tr), "G-0") == NOT_EVALUATED
    tr2 = fx.trial_ready()
    del tr2["checks"][-1]
    assert status(_g0(tr2), "G-0") == NOT_EVALUATED


def test_g0_an_evaluation_at_another_head_is_a_failure():
    assert status(_g0(fx.trial_ready(head="b" * 40)), "G-0") == FAIL


def test_g0_a_ready_false_document_fails_even_with_all_checks_true():
    assert status(_g0(fx.trial_ready(ready=False)), "G-0") == FAIL


def test_g0_an_evaluation_that_did_not_run_is_not_evaluated():
    assert status(_g0({"predicate": "TRIAL_READY/1", "head_sha": "a" * 40, "checks": [], "ready": False, "not_run_reason": "no repo"}), "G-0") == NOT_EVALUATED
    assert status(_g0(None), "G-0") == NOT_EVALUATED


def test_a_trial_without_trial_ready_is_a_diagnostic_and_never_dispatchable():
    """PLAN_A10_1 §2.1: every rolling run before `ready: true` writes {qualifying: false, label: DIAGNOSTIC, head, image, scope, status}."""
    r = fx.a10_report()
    r["trial_ready"] = None
    q = te.qualification_block(r)
    assert q["qualifying"] is False and q["label"] == "DIAGNOSTIC" and q["head"] == "a" * 40 and set(q) >= {"qualifying", "label", "head", "image", "scope", "status"}
    assert not run10(r, prof=fx.profile(final=True))["dispatchable"]
    ok = te.qualification_block(fx.a10_report())
    assert ok["qualifying"] is True and ok["label"] != "DIAGNOSTIC"


def test_the_required_ids_are_the_25_of_the_merged_evaluator():
    import importlib.util
    from pathlib import Path
    tool = Path(fx.HARNESS / "tests" / "vendor" / "trial_ready.py")
    spec = importlib.util.spec_from_file_location("vendored_trial_ready", tool)
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, str(tool.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(tool.parent))
    assert tuple(mod.REQUIRED_IDS) == gates.TRIAL_READY_IDS and mod.PREDICATE == gates.TRIAL_READY_PREDICATE
