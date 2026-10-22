"""Gate evaluator G-1..G-8: one test per distinct claim of PLAN.md §4.3, each breaking exactly ONE thing in an otherwise fully-passing world.
Oracles are the plan's own criteria text (cited per test); nothing here is a captured output."""
import copy
import math

import pytest

import fixtures as fx
import gates
from gates import FAIL, NOT_EVALUATED, PASS


def run(rep=None, base=None, prof=None, **kw):
    r, b, p = fx.good()
    kw.setdefault("second_report", fx.second())
    kw.setdefault("dispatch_modules", fx.dispatch_modules())
    return gates.evaluate(rep if rep is not None else r, base if base is not None else b, prof if prof is not None else p, **kw)


def status(v, gid):
    return v["gates"][gid]["status"]


# ── the control: a fully passing world passes every gate, and only a FINAL profile makes it dispatchable ─────────

def test_control_all_gates_pass_but_placeholder_profile_is_never_dispatchable():
    v = run()
    assert [status(v, g) for g in gates.GATE_IDS] == [PASS] * 8, {g: x["checks"] for g, x in v["gates"].items() if x["status"] != PASS}
    assert v["overall"] == "ALL_GATES_PASS_PROFILE_NOT_FINAL" and v["dispatchable"] is False


def test_final_profile_with_all_gates_passing_is_dispatchable():
    v = run(prof=fx.profile(final=True))
    assert v["overall"] == "DISPATCH_GATE_MET" and v["dispatchable"] is True


# ── G-1 integrity ───────────────────────────────────────────────────────────────────────────────────────────────

def test_g1_class_set_must_be_the_12():
    r, b, p = fx.good()
    r["config"]["classes"] = r["config"]["classes"][:8]
    assert status(run(r), "G-1") == FAIL


def test_g1_windows_total_must_equal_baseline_per_class():
    r, b, p = fx.good()
    r["classes"]["major_loss"]["windows_total"] = 151                      # one extra window in one class
    v = run(r)
    assert status(v, "G-1") == FAIL
    assert "major_loss" in str(v["gates"]["G-1"]["checks"])


def test_g1_unmeasured_baseline_class_is_not_a_pass():
    r, b, p = fx.good()
    b["classes"]["spiritual_turn"]["windows_total"] = None
    assert status(run(r, b), "G-1") == NOT_EVALUATED


@pytest.mark.parametrize("field", gates.ANOMALY_FIELDS)
def test_g1_every_anomaly_must_be_zero(field):
    r, b, p = fx.good()
    r["anomalies"][field] = 1
    assert status(run(r), "G-1") == FAIL


def test_g1_missing_anomaly_detector_is_not_a_zero():
    r, b, p = fx.good()
    del r["anomalies"]["peak_without_score"]
    assert status(run(r), "G-1") == NOT_EVALUATED


# ── G-2 wiring complete ─────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("code", ["applicability_undeclared", "value_mapping_undeclared", "vedha_overlay_not_bound", "orb_not_ratified",
                                  "dynamic_objective_solver_guarantee_not_available"])
def test_g2_each_wiring_code_must_have_zero_blank_windows(code):
    r, b, p = fx.good()
    r["reason_windows_any"][code] = 1
    assert status(run(r), "G-2") == FAIL


def test_g2_a_wiring_code_hidden_as_a_secondary_reason_still_fails():
    # the stored `unqualified_reason` is only the FIRST sorted reason; the window also carries the other unresolved reasons
    r, b, p = fx.good()
    r["totals"]["unresolved_factors_in_blank_windows"]["vedha_overlay_not_bound"] = {"windows": 2, "members": 2}
    r["reason_windows_any"]["vedha_overlay_not_bound"] = 2
    assert status(run(r), "G-2") == FAIL


def test_g2_reason_outside_the_closed_set_fails():
    r, b, p = fx.good()
    r["totals"]["blank_reasons"]["objective_undeterminable"] = 1
    assert status(run(r), "G-2") == FAIL


def test_g2_secondary_reason_outside_the_closed_set_fails():
    r, b, p = fx.good()
    r["totals"]["unresolved_factors_in_blank_windows"]["geometry_operand_missing"] = {"windows": 1, "members": 1}
    assert status(run(r), "G-2") == FAIL


def test_g2_node_obstruction_undecided_is_legitimate_only_under_q9a():
    # PLAN §4.3 G-2: "node_obstruction_undecided only if Q9a"
    r, b, p = fx.good()
    assert status(run(r, b, p), "G-2") == PASS
    p9b = fx.profile(answers={"q4": "b", "q9": "b"})
    assert status(run(r, b, p9b), "G-2") == FAIL


def test_g2_node_nature_blank_is_legitimate_only_under_q4b():
    r, b, p = fx.good()
    p4a = fx.profile(answers={"q4": "a", "q9": "a"})
    assert status(run(r, b, p4a), "G-2") == FAIL


def test_g2_no_windows_is_not_evaluated():
    r, b, p = fx.good()
    r["totals"]["windows_total"] = 0
    assert status(run(r), "G-2") == NOT_EVALUATED


# ── G-3 share floors ────────────────────────────────────────────────────────────────────────────────────────────

def test_g3_p3_p4_pooled_floor_is_90_percent():
    r, b, p = fx.good()
    r["paths"]["P3"]["numbered"], r["paths"]["P4"]["numbered"] = 80, 400      # (80+400)/(100+400) = 96% -> still passes
    assert status(run(r), "G-3") == PASS
    r["paths"]["P4"]["numbered"] = 350                                        # (80+350)/500 = 86% -> fails
    assert status(run(r), "G-3") == FAIL


def test_g3_p2_floor_follows_the_q9_answer():
    r, b, p = fx.good()                                                       # P2 share .714
    assert status(run(r, b, fx.profile(answers={"q4": "b", "q9": "a"})), "G-3") == PASS          # floor .40
    assert status(run(r, b, fx.profile(answers={"q4": "b", "q9": "b"})), "G-3") == FAIL          # floor .90


def test_g3_p1_floor_follows_the_q4_answer():
    r, b, p = fx.good()                                                       # P1 share .50
    assert status(run(r, b, fx.profile(answers={"q4": "b", "q9": "a"})), "G-3") == PASS          # floor .20
    assert status(run(r, b, fx.profile(answers={"q4": "a", "q9": "a"})), "G-3") == FAIL          # floor .90


def test_g3_floor_without_an_answer_is_not_evaluated_not_defaulted():
    r, b, p = fx.good()
    assert status(run(r, b, fx.profile(answers={"q4": "b"})), "G-3") == NOT_EVALUATED


def test_g3_solver_budget_exhausted_capped_at_half_a_percent_of_all_windows():
    r, b, p = fx.good()
    r["reason_windows_any"]["solver_budget_exhausted"] = 9                    # 9/1800 = 0.5% -> at the cap passes
    assert status(run(r), "G-3") == PASS
    r["reason_windows_any"]["solver_budget_exhausted"] = 10                   # 0.556% -> fails
    assert status(run(r), "G-3") == FAIL


def test_g3_a_path_with_no_windows_is_not_evaluated():
    r, b, p = fx.good()
    r["paths"]["P2"] = {"windows": 0, "numbered": 0}
    assert status(run(r), "G-3") == NOT_EVALUATED


# ── G-4 independent verification ────────────────────────────────────────────────────────────────────────────────

def test_g4_not_run_is_not_evaluated():
    r, b, p = fx.good()
    r["verification"] = {"ran": False, "not_run_reason": "preconditions refused"}
    assert status(run(r), "G-4") == NOT_EVALUATED


def test_g4_verdict_must_be_passed():
    r, b, p = fx.good()
    r["verification"]["generation_verdict"]["status"] = "FAILED"
    r["verification"]["generation_verdict"]["problems"] = ["x: the persisted attestation differs"]
    assert status(run(r), "G-4") == FAIL


def test_g4_numbered_windows_must_be_positive():
    r, b, p = fx.good()
    r["verification"]["generation_verdict"]["numbered_windows"] = 0
    assert status(run(r), "G-4") == FAIL


def test_g4_blocking_judgment_flag_fails():
    r, b, p = fx.good()
    r["verification"]["generation_verdict"]["judgment_flags"] = ["no_window_numbered_under_numerical_policy"]
    assert status(run(r), "G-4") == FAIL


def test_g4_attested_counts_must_equal_the_live_recount():
    r, b, p = fx.good()
    r["verification"]["attestation_recount"]["attested"]["numbered"] = 1293
    assert status(run(r), "G-4") == FAIL


def test_g4_recount_must_be_of_this_trials_windows():
    r, b, p = fx.good()
    r["verification"]["attestation_recount"]["live"] = {"windows": 1700, "numbered": 1294}
    r["verification"]["attestation_recount"]["attested"] = {"windows": 1700, "numbered": 1294}
    assert status(run(r), "G-4") == FAIL


def test_g4_unverified_windows_must_be_zero():
    r, b, p = fx.good()
    r["verification"]["unverified_windows"] = 1
    assert status(run(r), "G-4") == FAIL


def test_g4_every_class_must_be_verified():
    r, b, p = fx.good()
    r["verification"]["classes"]["parental_event"]["status"] = "UNVERIFIED"
    assert status(run(r), "G-4") == FAIL


# ── G-5 runtime ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_g5_projection_formula_is_the_plans():
    # PLAN §4.3 G-5 / §2.5: (base_s + solver_s) · r, base_s extrapolated 26/12; base = every kind but `window`, solver = the window kind
    r, b, p = fx.good()                                                       # base 1150, solver 50, r = 1
    proj = gates.runtime_projection(r, p)
    assert proj["base_s"] == 1150.0 and proj["solver_s"] == 50.0 and proj["r"] == 1.0
    assert proj["projected_writer_s"] == pytest.approx((1150 + 50) * 26 / 12, abs=0.1)
    assert proj["limit_s"] == pytest.approx(0.75 * 0.8 * 72000)               # 43,200 s


def test_g5_r_is_century_horizon_over_trial_horizon():
    r, b, p = fx.good()
    p["runtime"]["century_horizon"] = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]       # == trial horizon -> r = 1
    assert gates.runtime_projection(r, p)["r"] == pytest.approx(1.0)
    p["runtime"]["century_horizon"] = ["1998-01-01T00:00:00+00:00", "2170-03-12T00:00:00+00:00"]       # twice the span
    assert gates.runtime_projection(r, p)["r"] == pytest.approx(2.0, rel=1e-3)


def test_g5_writer_projection_above_the_limit_fails():
    r, b, p = fx.good()
    r["runtime_s"]["by_step_kind"]["window"] = 40000.0                       # (1150 + 40000) · 26/12 ≈ 89,000 s
    assert status(run(r), "G-5") == FAIL


def test_g5_a_longer_century_horizon_raises_the_projection_over_the_limit():
    r, b, p = fx.good()
    r["runtime_s"]["by_step_kind"]["window"] = 5000.0                        # (1150+5000)·26/12 = 13,325 s: passes at r = 1
    assert status(run(r), "G-5") == PASS
    p["runtime"]["century_horizon"] = ["1998-01-01T00:00:00+00:00", "2400-01-01T00:00:00+00:00"]      # r ≈ 4.7 -> 62,000 s
    assert status(run(r, b, p), "G-5") == FAIL


def test_g5_verifier_solver_check_over_600_s_per_class_fails():
    r, b, p = fx.good()
    r["verification"]["classes"]["bereavement"]["window_check_s"] = 601.0
    assert status(run(r), "G-5") == FAIL


def test_g5_no_step_timings_is_not_evaluated():
    r, b, p = fx.good()
    r["runtime_s"]["by_step_kind"] = {}
    assert status(run(r), "G-5") == NOT_EVALUATED


def test_g5_a_final_profile_must_state_the_century_horizon():
    r, b, p = fx.good()
    final = fx.profile(final=True)
    assert status(run(r, b, final), "G-5") == PASS
    final["runtime"]["century_horizon"] = None
    assert status(run(r, b, final), "G-5") == FAIL


# ── G-6 cross-check ─────────────────────────────────────────────────────────────────────────────────────────────

def test_g6_sample_must_be_at_least_3_percent_of_numbered_windows():
    r, b, p = fx.good()                                                       # 1294 numbered -> ceil(38.82) = 39
    r["crosscheck"]["sampled"] = 38
    assert status(run(r), "G-6") == FAIL


def test_g6_sample_must_come_from_this_trials_numbered_windows():
    r, b, p = fx.good()
    r["crosscheck"]["numbered_windows"] = 1200
    assert status(run(r), "G-6") == FAIL


def test_g6_every_top_mixed_piece_window_must_be_checked():
    r, b, p = fx.good()
    r["crosscheck"]["top_mixed_checked"] = 3
    assert status(run(r), "G-6") == FAIL


def test_g6_solver_below_the_legacy_sampler_fails():
    r, b, p = fx.good()
    r["crosscheck"]["sampler_violations"] = [{"window": "w1", "stored": 0.5, "sampler": 0.6}]
    assert status(run(r), "G-6") == FAIL


def test_g6_dense_brute_force_disagreement_fails():
    r, b, p = fx.good()
    r["crosscheck"]["dense_violations"] = [{"window": "w2", "stored": 0.5, "dense": 0.7}]
    assert status(run(r), "G-6") == FAIL


def test_g6_inconsistent_value_at_stored_peak_fails():
    r, b, p = fx.good()
    r["crosscheck"]["recompute_inconsistent"] = [{"window": "w3"}]
    assert status(run(r), "G-6") == FAIL


def test_g6_incomplete_cross_check_is_not_a_pass():
    r, b, p = fx.good()
    r["crosscheck"]["status"] = "BUDGET_EXHAUSTED"
    assert status(run(r), "G-6") == FAIL


def test_g6_no_cross_check_record_is_not_evaluated():
    r, b, p = fx.good()
    del r["crosscheck"]
    assert status(run(r), "G-6") == NOT_EVALUATED


def test_g6_zero_numbered_windows_is_not_evaluated_never_vacuously_green():
    r, b, p = fx.good()
    r["totals"]["with_peak"] = 0
    assert status(run(r), "G-6") == NOT_EVALUATED


# ── G-7 determinism ─────────────────────────────────────────────────────────────────────────────────────────────

def test_g7_no_second_run_is_not_evaluated():
    assert status(run(second_report=None), "G-7") == NOT_EVALUATED


def test_g7_window_rows_must_be_byte_identical():
    s = fx.second()
    s["window_rows_digest"]["sha256"] = "e" * 64
    assert status(run(second_report=s), "G-7") == FAIL


def test_g7_both_runs_must_be_at_the_same_head():
    s = fx.second()
    s["code"]["head"] = "b" * 40
    assert status(run(second_report=s), "G-7") == FAIL


# ── G-8 head identity ───────────────────────────────────────────────────────────────────────────────────────────

def test_g8_a_changed_module_digest_fails():
    d = fx.dispatch_modules()
    d["services.gochara_kernel.window_sweep"] = "9" * 64
    assert status(run(dispatch_modules=d), "G-8") == FAIL


def test_g8_a_module_present_on_one_side_only_fails():
    d = fx.dispatch_modules()
    d["services.gochara_kernel.window_solver"] = "3" * 64
    assert status(run(dispatch_modules=d), "G-8") == FAIL


def test_g8_missing_dispatch_digests_is_not_evaluated():
    assert status(run(dispatch_modules=None), "G-8") == NOT_EVALUATED


# ── verdict logic ───────────────────────────────────────────────────────────────────────────────────────────────

def test_one_failed_gate_means_no_dispatch_even_with_a_final_profile():
    r, b, p = fx.good()
    r["anomalies"]["number_without_score"] = 3
    v = run(r, b, fx.profile(final=True))
    assert v["overall"] == "NO_DISPATCH" and v["failed"] == ["G-1"]


def test_an_unevaluated_gate_is_never_a_pass_overall():
    v = run(second_report=None)
    assert v["overall"] == "NO_DISPATCH_NOT_EVALUATED" and v["not_evaluated"] == ["G-7"] and not v["dispatchable"]


def test_a_trial_that_did_not_run_as_designed_is_invalid_not_judged():
    r, b, p = fx.good()
    r["policy_effect"]["took_effect"] = False
    assert run(r)["overall"] == "INVALID_TRIAL"
    r, b, p = fx.good()
    r["build"]["defects"] = [{"step": "window:x:P1"}]
    assert run(r)["overall"] == "INVALID_TRIAL"
