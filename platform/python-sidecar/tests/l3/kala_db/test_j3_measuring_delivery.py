"""MB-7 consumer tests: numbers are recomputed, missing evidence stays missing."""
from __future__ import annotations

import json

import pytest

from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import measuring_delivery as md
from services.gochara_kernel import measuring_report as mr

from .test_j3_measuring_capture import bundle, record


def golden(tmp_path):
    b = bundle()
    rows = []
    for agent, lo, hi in [("jupiter", "2000-01-01", "2000-01-06"), ("saturn", "2000-01-04", "2000-01-09")]:
        row = record()
        row.update(agent=agent, path_id="P4", temporal_support_intervals=[[lo + "T00:00:00+00:00", hi + "T00:00:00+00:00"]])
        rows.append(row)
    # A stored admitted testimony does not contribute to any scored share.
    testimony = record()
    testimony.update(operator_role="testimony", temporal_support_intervals=[["1998-01-01T00:00:00+00:00", "2026-04-18T00:00:00+00:00"]])
    rows.append(testimony)
    b = mc.make_bundle(binding=b["digests.json"]["binding"], contacts=[], records=rows, windows=[],
                       horizon_basis={"schema": "horizon_basis/1", "basis": "ruled_horizon", "rule": "ruled_scope+birth_centenary", "horizon": ["1998-01-01", "2084-02-05"]},
                       stretch_sink=[], informational={"horizon": ["1998-01-01", "2084-02-05"]})
    path = tmp_path / "golden"
    receipt = mc.write_bundle(path, b)
    observations = {
        "binding": dict(b["digests.json"]["binding"]), "golden_manifest_sha256": receipt["manifest_sha256"],
        "timings": {"run_seconds": 10, "asset_seconds": 9, "by_phase": {"records": 5}, "by_class_substep": {"marriage:record": 5}},
        "runtime": {"run_state": "completed", "asset_state": "complete", "disposition": "build", "throughput_state": "lit",
                    "last_substep_index": 298, "planned_substeps": 298, "inventory_classes": 26, "completed_classes": 26},
        "row_counts": {"ka_gochara_contact": 0, "ka_gochara_relationship_record": 3, "ka_gochara_eval_window": 0},
        "sink_recount": {"group_I": {}, "group_R": {}, "sink_disagreement": [], "independent_review": None},
        "horizon_readback": {"lel_drift": [], "independent_review": None},
        "teardown": {"dry_run_counts": {}, "outcome": "NOT_EXECUTED", "end_state": None},
        "acceptance": {"accepted": None, "refusals": [], "independent_review": None},
        "golden_commit": None,
    }
    return path, observations


def test_report_recomputes_instant_p4_intersection_and_both_grids_excluding_testimony(tmp_path):
    path, observations = golden(tmp_path)
    report = md.build_report(path, observations)
    assert set(report["numbers"]) == {str(i) for i in range(1, 15)}
    build, scored = report["numbers"]["4"]["data"], report["numbers"]["5"]["data"]
    assert build["horizon_days"] == 31446
    assert scored["horizon_days"] == 10334
    assert build["classes"]["marriage"]["admitted_days"]["P4_with_dvi"] == 2
    assert scored["classes"]["marriage"]["admitted_days"]["P4_with_dvi"] == 3
    assert scored["classes"]["marriage"]["admitted_share"]["P3_union"] == 0
    assert build["classes"]["bereavement"]["admitted_days"]["class_union"] == 0
    assert report["numbers"]["14"]["data"]["budget_share"] == .0261
    assert report["numbers"]["14"]["data"]["label"] == "structural-saturation finding, not a decision"
    assert report["independent_acceptance"] is None
    assert report["status"] == "DRAFT_AWAITING_INDEPENDENT_ACCEPTANCE"
    assert "excursions shorter than 60 s are not excluded" in report["numbers"]["8"]["data"]["limit"]
    assert "common-mode" in report["numbers"]["8"]["data"]["limit"]
    assert report["numbers"]["8"]["data"]["independent_recount_performed_by_exporter"] is False
    assert report["numbers"]["13"]["data"]["cannot_establish"] == (
        "Nothing about the eight ND-H classes beyond P2; nothing about K-B, karakatva, natal-Sun target, DVI, "
        "the 40% guard's decision (final-rules candidate); no near-miss storage; no scoring, endpoints, "
        "retrodiction or 3.0 comparison; nothing about sealing, publication, serving, 1236, rollback, "
        "1984-1998; no final run length (lower bound); no verification rows; nothing about 1305-1308.")
    assert "golden_commit_not_recorded" in report["refusals"]
    assert "teardown_not_executed" in report["refusals"]
    assert "acceptance_not_independently_reviewed" in report["refusals"]


@pytest.mark.parametrize("section,number", [("timings", 1), ("runtime", 2), ("row_counts", 3),
                                           ("sink_recount", 8), ("horizon_readback", 10),
                                           ("teardown", 12), ("acceptance", 13)])
def test_report_names_each_missing_observation_instead_of_substituting_pass(tmp_path, section, number):
    path, observations = golden(tmp_path)
    del observations[section]
    got = md.build_report(path, observations)
    assert f"report_number_missing:{number}" in got["refusals"]


@pytest.mark.parametrize("edit", ["binding", "digest"])
def test_report_refuses_evidence_from_a_different_run_or_capture(tmp_path, edit):
    path, observations = golden(tmp_path)
    if edit == "binding":
        observations["binding"]["run_id"] = "a-different-run"
    else:
        observations["golden_manifest_sha256"] = "0" * 64
    with pytest.raises(md.DeliveryRefused, match="report_evidence_binding_mismatch"):
        md.build_report(path, observations)


@pytest.mark.parametrize("mutation,refusal", [
    ("missing", "report_number_missing:7"),
    ("convention", "report_convention_mixed"),
    ("ratio", "report_ratio_mismatch"),
    ("scope", "report_scope_statement_missing"),
])
def test_report_validator_detects_missing_numbers_mixed_conventions_wrong_ratios_and_lost_limits(tmp_path, mutation, refusal):
    path, observations = golden(tmp_path)
    report = md.build_report(path, observations)
    if mutation == "missing":
        del report["numbers"]["7"]
    elif mutation == "convention":
        report["numbers"]["4"]["data"]["horizon_days"] = 10334
    elif mutation == "ratio":
        report["numbers"]["5"]["data"]["classes"]["marriage"]["admitted_share"]["P4_with_dvi"] = .40
    else:
        report["numbers"]["13"]["data"]["cannot_establish"] = "Everything passed"
    assert refusal in md.report_refusals(report)


def test_offline_cli_verifies_before_writing_report_and_fails_on_tamper(tmp_path, capsys):
    path, observations = golden(tmp_path)
    evidence = tmp_path / "observations.json"
    evidence.write_text(json.dumps(observations))
    out = tmp_path / "report.json"
    assert md.main(["report", "--golden", str(path), "--observations", str(evidence), "--output", str(out)]) == 0
    assert json.loads(out.read_text())["independent_acceptance"] is None
    (path / "records.jsonl").write_text("[]\n")
    out.unlink()
    assert md.main(["report", "--golden", str(path), "--observations", str(evidence), "--output", str(out)]) == 2
    assert not out.exists()
    assert "golden_digest_mismatch" in capsys.readouterr().err


def test_report_does_not_treat_external_acceptance_as_its_own_or_hide_failed_runtime(tmp_path):
    path, observations = golden(tmp_path)
    observations["acceptance"].update(accepted=True, refusals=["certifier_omissions_present:3"])
    observations["runtime"].update(run_state="failed", last_substep_index=297)
    report = md.build_report(path, observations)
    assert report["independent_acceptance"] is None
    assert "asset_lit_under_failed_run" in report["refusals"]
    assert "substep_plan_incomplete" in report["refusals"]
    assert "certifier_omissions_present:3" in report["numbers"]["13"]["data"]["observed"]["refusals"]


def test_one_completed_substep_does_not_substitute_for_the_full_298_step_plan(tmp_path):
    path, observations = golden(tmp_path)
    observations["runtime"].update(last_substep_index=1, planned_substeps=1)
    report = md.build_report(path, observations)
    assert "substep_plan_incomplete" in report["refusals"]


def test_report_refuses_admitted_rows_from_a_rule_version_not_bound_by_the_protocol(tmp_path):
    _, observations = golden(tmp_path)
    row = record()
    row["rule_version"] = "2.0.0"
    data = mc.make_bundle(binding=observations["binding"], contacts=[], records=[row], windows=[],
                          horizon_basis={}, stretch_sink=[], informational={"horizon": ["1998-01-01", "2084-02-05"]})
    bad = tmp_path / "unbound-version"
    observations["golden_manifest_sha256"] = mc.write_bundle(bad, data)["manifest_sha256"]
    with pytest.raises(mr.MeasuringReportError, match="^rule_version_not_in_scope$"):
        md.build_report(bad, observations)


def test_malformed_runtime_is_named_as_non_success_instead_of_crashing(tmp_path):
    path, observations = golden(tmp_path)
    observations["runtime"] = "completed"
    error = None
    try:
        report = md.build_report(path, observations)
    except AttributeError as exc:
        error = str(exc)
    assert error is None, f"malformed runtime must produce named refusals: {error}"
    assert "verdict_not_success" in report["refusals"]
    assert "substep_plan_incomplete" in report["refusals"]


@pytest.mark.parametrize("mutation,refusal", [
    ("empty_timing", "report_number_missing:1"),
    ("missing_phase", "report_number_missing:1"),
    ("negative_timing", "report_timing_invalid"),
    ("missing_class", "report_number_missing:4"),
    ("grid_label", "report_convention_mixed"),
    ("grid_horizon", "report_convention_mixed"),
    ("boolean_count", "report_row_counts_mismatch"),
])
def test_report_completeness_requires_values_and_pins_the_calendar_inputs(tmp_path, mutation, refusal):
    path, obs = golden(tmp_path)
    report = md.build_report(path, obs)
    if mutation == "empty_timing":
        report["numbers"]["1"]["data"] = {}
    elif mutation == "missing_phase":
        del report["numbers"]["1"]["data"]["by_phase"]
    elif mutation == "negative_timing":
        report["numbers"]["1"]["data"]["asset_seconds"] = -1
    elif mutation == "missing_class":
        del report["numbers"]["4"]["data"]["classes"]["bereavement"]
    elif mutation == "grid_label":
        report["numbers"]["4"]["data"]["convention"] = "ist_inclusive"
    elif mutation == "grid_horizon":
        report["numbers"]["5"]["data"]["horizon"] = ["1998-01-01", "2026-04-18"]
    else:
        report["numbers"]["3"]["data"]["observed"]["ka_gochara_eval_window"] = False
    assert refusal in md.report_refusals(report)
