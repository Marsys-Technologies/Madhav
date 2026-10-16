"""K9-5: exercise the offline preparation/report boundary, never a database.

The breaks caught here are invented verdicts, dropped assets, stale detector
bindings, and a report that hides the engine's caps or certifier refusals.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import asset_census as ac

TOOL = Path(os.environ.get("K9_CENSUS_TOOL", HERE.parent / "kala_rehearsal_census.py"))


@pytest.fixture
def tool():
    assert TOOL.is_file(), "K9-5 offline census preparation tool is missing"
    spec = importlib.util.spec_from_file_location("k9_census_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def census(tmp_path, measurements=None, **updates):
    declarations = (ROOT / "platform/scripts/governance/asset_declarations.json").read_bytes()
    head = dict(layer="L3", generated="2026-10-16T01:00:00+00:00",
                chart_scope="482012f1-710e-4a25-994a-93821f5871aa",
                census_target={"declared": "disposable"}, registry_revision=ac.REGISTRY_REVISION,
                registry_fingerprint=ac.registry_fingerprint(),
                declarations_sha256=hashlib.sha256(declarations).hexdigest(),
                declarations_version=json.loads(declarations)["version"],
                assets=[dict(asset_id="ka_avadhi", layer="L3", asset_kind="data",
                             measurements=measurements or {"Idem.pattern": {"v": "FAIL", "measured": "no replacement"}})])
    head.update(updates)
    path = tmp_path / "census.json"
    path.write_text(json.dumps({"L3": head}))
    return path


def row(report, aid="ka_avadhi"):
    return next(a for a in report["assets"] if a["asset"] == aid)


def test_preparation_preserves_unknowns_and_complete_planned_population(tool):
    report = tool.build_report(ROOT)
    assert len(report["assets"]) == 25
    assert {"ka_gochara_v5", "ka_gochara_sweep", "ka_tulana"} <= {a["asset"] for a in report["assets"]}
    assert report["mode"] == "preparation" and report["production_certification"] is None
    assert report["summary"] == dict(planned_assets=25, observed_assets=0, missing_assets=25, observed_gates=0)
    assert all(g["observed"] is None and g["expected"] is None
               for a in report["assets"] for g in a["gates"].values())
    d2 = report["criteria"]["Carr.D2"]
    assert d2["detector"] == "NONE" and d2["recordable_verdict"] == "NO_DETECTOR"
    assert report["criteria"]["Idem.pattern"]["recordable_verdict"] is None


def test_file_evidence_is_hashed_and_partial_population_never_disappears(tool, tmp_path):
    path = census(tmp_path)
    report = tool.build_report(ROOT, path)
    assert report["source"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert report["source"]["generated"] == "2026-10-16T01:00:00+00:00"
    assert row(report)["measurements"]["Idem.pattern"]["v"] == "FAIL"
    assert row(report)["gates"]["Idem"]["observed"] == "FAIL"
    assert row(report, "ka_sangam")["gates"]["Idem"]["observed"] is None
    assert report["summary"] == dict(planned_assets=25, observed_assets=1, missing_assets=24, observed_gates=9)
    assert report["production_certification"] is None


def test_expected_gate_disagreement_is_visible_and_cli_nonzero(tool, tmp_path):
    path = census(tmp_path)
    expected = {"ka_avadhi": {"Idem": "PASS"}}
    report = tool.build_report(ROOT, path, expected)
    assert report["mismatches"] == [dict(asset="ka_avadhi", gate="Idem", expected="PASS", observed="FAIL", reason="census_mismatch")]
    ep = tmp_path / "expected.json"
    ep.write_text(json.dumps(expected))
    p = subprocess.run([sys.executable, str(TOOL), "--repo", str(ROOT), "--census", str(path),
                        "--expectations", str(ep)], capture_output=True, text=True)
    assert p.returncode == 2 and "census_mismatch" in p.stdout
    assert json.loads(p.stdout)["mismatches"] == report["mismatches"]


@pytest.mark.parametrize("verdict", ["PASS", "PARTIAL", "FAIL", "N/A", "ERRORED"])
def test_detector_none_never_becomes_a_recordable_claim(tool, tmp_path, verdict):
    report = tool.build_report(ROOT, census(tmp_path, {"Carr.D2": {"v": verdict}}))
    assert row(report)["measurements"]["Carr.D2"]["v"] == verdict  # raw is preserved, never rewritten
    assert report["certifier_refusals"] == [dict(asset="ka_avadhi", criterion="Carr.D2", verdict=verdict, reason="detector_none")]


def test_honest_no_detector_is_preserved_without_a_refusal(tool, tmp_path):
    report = tool.build_report(ROOT, census(tmp_path, {"Carr.D2": {"v": "NO_DETECTOR"}}))
    assert report["certifier_refusals"] == []
    assert row(report)["gates"]["Carr"]["observed"] == "NO_DETECTOR"


@pytest.mark.parametrize("criterion,gate", [("Null.schema_default", "Null"), ("Narr.fidelity_test", "Narr")])
def test_unearned_pass_keeps_raw_reading_but_engine_caps_the_gate(tool, tmp_path, criterion, gate):
    # Every sibling supplied so absence does not dominate the cap being tested.
    measurements = {c: {"v": "PASS"} for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == gate}
    report = tool.build_report(ROOT, census(tmp_path, measurements))
    assert row(report)["measurements"][criterion]["v"] == "PASS"
    assert row(report)["gates"][gate]["observed"] == "PARTIAL"


def test_unruled_na_and_absent_checks_are_not_released(tool, tmp_path):
    report = tool.build_report(ROOT, census(tmp_path, {"Idem.pattern": {"v": "N/A"}}))
    assert row(report)["gates"]["Idem"]["observed"] == "NO_DETECTOR"
    assert row(report)["gates"]["Ldgr"]["observed"] == "NO_DETECTOR"


@pytest.mark.parametrize("updates", [dict(registry_revision=-1), dict(registry_fingerprint="a" * 64),
                                    dict(layer="L2"), dict(census_target={"declared": "production"}), dict(generated=None)])
def test_unbound_or_production_census_is_refused(tool, tmp_path, updates):
    with pytest.raises(ValueError):
        tool.build_report(ROOT, census(tmp_path, **updates))


@pytest.mark.parametrize("updates", [dict(declarations_sha256="a" * 64), dict(declarations_version="obsolete"),
                                    dict(declarations_sha256=None)])
def test_changed_or_missing_declarations_binding_cannot_reinterpret_old_readings(tool, tmp_path, updates):
    with pytest.raises(ValueError, match="declarations binding mismatch"):
        tool.build_report(ROOT, census(tmp_path, **updates))


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "wrong_layer", "bad_verdict", "empty", "unknown_criterion"])
def test_malformed_population_and_measurements_fail_closed(tool, tmp_path, mutation):
    path = census(tmp_path)
    doc = json.loads(path.read_text())
    assets = doc["L3"]["assets"]
    if mutation == "duplicate":
        assets.append(copy.deepcopy(assets[0]))
    elif mutation == "unknown":
        assets[0]["asset_id"] = "ka_invented"
    elif mutation == "wrong_layer":
        assets[0]["layer"] = "L2"
    elif mutation == "bad_verdict":
        assets[0]["measurements"]["Idem.pattern"]["v"] = "GREEN"
    elif mutation == "empty":
        doc["L3"]["assets"] = []
    else:
        assets[0]["measurements"]["Invented.claim"] = {"v": "PASS"}
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        tool.build_report(ROOT, path)


@pytest.mark.parametrize("expected", [{"ka_invented": {"Build": "PASS"}}, {"ka_avadhi": {"Invented": "PASS"}},
                                      {"ka_avadhi": {"Build": "GREEN"}}])
def test_bad_expectations_are_refused_instead_of_dropped(tool, expected):
    with pytest.raises(ValueError):
        tool.build_report(ROOT, expectations=expected)


def test_unmeasured_expected_pass_is_a_mismatch(tool):
    report = tool.build_report(ROOT, expectations={"ka_avadhi": {"Build": "PASS"}})
    assert report["mismatches"] == [dict(asset="ka_avadhi", gate="Build", expected="PASS", observed=None, reason="unmeasured")]


def test_rehearsal_report_cli_exposes_detector_none_refusal(tool, tmp_path):
    path = census(tmp_path, {"Carr.D2": {"v": "PASS"}})
    p = subprocess.run([sys.executable, str(TOOL), "--repo", str(ROOT), "--census", str(path)],
                       capture_output=True, text=True)
    assert p.returncode == 2
    assert json.loads(p.stdout)["certifier_refusals"][0]["reason"] == "detector_none"


def test_duplicate_json_keys_cannot_replace_a_measured_failure(tool, tmp_path):
    path = census(tmp_path)
    path.write_text(path.read_text().replace('"v": "FAIL"', '"v": "FAIL", "v": "PASS"'))
    with pytest.raises(ValueError, match="duplicate JSON key"):
        tool.build_report(ROOT, path)


def test_mandatory_governance_ci_discovers_this_suite_exactly_once():
    import ci_shard
    suite = Path(__file__).resolve()
    shards = ci_shard.partition(ci_shard.test_files(), 5)
    assert sum(p == suite for shard in shards for p in shard) == 1
    assert ci_shard.verify(ci_shard.test_files(), shards) == []


def test_preparation_artifact_is_reproducible_and_stale_output_check_fails(tool, tmp_path):
    # A committed preparation report records the inputs at generation time.
    # Other queued PRs may legitimately change them; regenerate from this tree
    # instead of requiring that historical snapshot to match the current inputs.
    expected = tool.render_markdown(tool.build_report(ROOT))
    output = tmp_path / "report.md"
    argv = [sys.executable, str(TOOL), "--repo", str(ROOT), "--format", "markdown", "--out", str(output)]
    p = subprocess.run(argv, capture_output=True, text=True)
    assert p.returncode == 0 and output.read_text() == expected
    assert subprocess.run([*argv, "--check"], capture_output=True).returncode == 0
    assert subprocess.run(argv, capture_output=True).returncode == 0
    assert output.read_text() == expected

    # A legitimate input change must still invalidate an already generated
    # report. Work on copies so neither the plan nor other tests are mutated.
    repo = tmp_path / "repo"
    for relative in (tool.PLAN, tool.REGISTRY, tool.DECLARATIONS):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    plan = repo / tool.PLAN
    plan.write_text(plan.read_text() + "\n<!-- unrelated merge-queue plan edit -->\n")
    changed_argv = [sys.executable, str(TOOL), "--repo", str(repo),
                    "--format", "markdown", "--out", str(output)]
    stale = subprocess.run([*changed_argv, "--check"], capture_output=True, text=True)
    assert stale.returncode == 2 and "stale/missing output" in stale.stderr
    assert output.read_text() == expected  # --check never repairs stale output
    assert subprocess.run(changed_argv, capture_output=True).returncode == 0
    changed = output.read_text()
    assert changed != expected
    assert subprocess.run([*changed_argv, "--check"], capture_output=True).returncode == 0
    assert subprocess.run(changed_argv, capture_output=True).returncode == 0
    assert output.read_text() == changed

    output.write_text("stale report")
    assert subprocess.run([*changed_argv, "--check"], capture_output=True).returncode == 2
